#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국어 PDF 오탈자 자동 검수 시스템
대용량 PDF에서 한국어 오탈자, 맞춤법, 띄어쓰기 오류를 자동으로 검출합니다.
"""

import os
import time
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from utils.pdf import extract_pages
from utils.text import normalize_text, split_sentences, visible_korean_ratio
from utils.diff import simple_diff
from checkers.base import BaseChecker
from checkers.hanspell_checker import HanspellChecker
from checkers.spacing_checker import SpacingChecker
from checkers.rule_checker import RuleChecker

def build_checkers(args):
    """인자에 따라 검사기들을 동적으로 빌드."""
    checkers = []
    
    if args.hanspell:
        try:
            checkers.append(HanspellChecker(rate_limit_per_sec=args.hanspell_rate))
            print(f"✓ Hanspell 검사기 활성화 (rate: {args.hanspell_rate}/sec)")
        except Exception as e:
            print(f"✗ Hanspell 검사기 비활성화: {e}")
    
    if args.spacing:
        try:
            checkers.append(SpacingChecker())
            print(f"✓ PyKoSpacing 검사기 활성화")
        except Exception as e:
            print(f"✗ PyKoSpacing 검사기 비활성화: {e}")
    
    if args.rule:
        try:
            checkers.append(RuleChecker(args.rules_path, args.whitelist_path))
            print(f"✓ Rule 검사기 활성화")
        except Exception as e:
            print(f"✗ Rule 검사기 비활성화: {e}")
    
    if not checkers:
        print("경고: 활성화된 검사기가 없습니다!")
        return []
    
    return checkers

def check_sentence(sentence, checkers):
    """문장을 모든 검사기로 검사."""
    flags = []
    suggestions = {}
    metas = {}
    
    for checker in checkers:
        try:
            result = checker.check(sentence)
            if result["flag"]:
                flags.append(checker.name)
                if "suggestion" in result:
                    suggestions[checker.name] = result["suggestion"]
                elif "suggestions" in result:
                    suggestions[checker.name] = result["suggestions"]
                if "meta" in result:
                    metas[checker.name] = result["meta"]
        except Exception as e:
            print(f"검사기 {checker.name} 오류: {e}")
    
    return flags, suggestions, metas

def representative_suggestion(suggestions):
    """대표 교정안 선택 (우선순위: hanspell > spacing > rule)."""
    if "hanspell" in suggestions:
        return suggestions["hanspell"]
    elif "spacing" in suggestions:
        return suggestions["spacing"]
    return None

def main():
    parser = argparse.ArgumentParser(description="PDF 한국어 오탈자 검사기")
    parser.add_argument("pdf_path", help="검사할 PDF 파일 경로")
    parser.add_argument("--out-dir", default="out", help="출력 디렉토리")
    parser.add_argument("--korean-ratio", type=float, default=0.3, help="한글 비율 최소값")
    parser.add_argument("--min-length", type=int, default=10, help="최소 문장 길이")
    parser.add_argument("--snippet-length", type=int, default=60, help="스니펫 길이")
    parser.add_argument("--workers", type=int, default=4, help="동시 작업자 수")
    parser.add_argument("--ocr", action="store_true", help="OCR 사용")
    parser.add_argument("--ocr-threshold", type=int, default=50, help="OCR 트리거 문자 수")
    parser.add_argument("--hanspell", action="store_true", help="Hanspell 검사기 사용")
    parser.add_argument("--hanspell-rate", type=int, default=5, help="Hanspell 초당 요청 수")
    parser.add_argument("--spacing", action="store_true", help="PyKoSpacing 검사기 사용")
    parser.add_argument("--rule", action="store_true", help="Rule 검사기 사용")
    parser.add_argument("--rules-path", default="data/rules.yaml", help="규칙 파일 경로")
    parser.add_argument("--whitelist-path", default="data/whitelist.txt", help="화이트리스트 파일 경로")
    parser.add_argument("--format", choices=["csv", "xlsx", "both"], default="both", help="출력 형식")
    
    args = parser.parse_args()
    
    # 기본 검사기 활성화 (인자가 없으면)
    if not any([args.hanspell, args.spacing, args.rule]):
        args.hanspell = True
        args.spacing = True
        args.rule = True
    
    # 출력 디렉토리 생성
    os.makedirs(args.out_dir, exist_ok=True)
    
    # 검사기 빌드
    checkers = build_checkers(args)
    if not checkers:
        return
    
    print(f"PDF 처리 시작: {args.pdf_path}")
    print(f"활성 검사기: {[c.name for c in checkers]}")
    
    # PDF에서 페이지별 텍스트 추출
    pages = list(extract_pages(args.pdf_path, use_ocr=args.ocr, ocr_threshold=args.ocr_threshold))
    print(f"총 {len(pages)} 페이지 처리")
    
    rows = []
    total_sentences = 0
    flagged_sentences = 0
    
    # 페이지별 처리
    for page_no, text, is_ocr in pages:
        if not text.strip():
            continue
            
        # 텍스트 정규화
        normalized = normalize_text(text)
        
        # 한글 비율 체크
        if visible_korean_ratio(normalized) < args.korean_ratio:
            continue
        
        # 문장 분리
        sentences = split_sentences(normalized)
        sentences = [s for s in sentences if len(s.strip()) >= args.min_length]
        total_sentences += len(sentences)
        
        if not sentences:
            continue
        
        print(f"페이지 {page_no} 처리 중... ({len(sentences)} 문장, OCR: {is_ocr})")
        
        # 문장별 검사 (병렬 처리)
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(check_sentence, s, checkers): s for s in sentences}
            
            for future in as_completed(futures):
                sentence = futures[future]
                try:
                    flags, suggestions, metas = future.result()
                    
                    if flags:  # OR 로직: 하나라도 플래그가 있으면
                        flagged_sentences += 1
                        
                        # 대표 교정안
                        rep_suggestion = representative_suggestion(suggestions)
                        
                        # 스니펫 생성
                        snippet = sentence[:args.snippet_length]
                        if len(sentence) > args.snippet_length:
                            snippet += "…"
                        
                        # 오류 타입 추출 (rule 기반)
                        error_types = []
                        if "rule" in metas and metas["rule"]:
                            for hit in metas["rule"]:
                                if isinstance(hit, dict) and "rule" in hit:
                                    error_types.append(hit["rule"])
                        
                        # diff 생성
                        diff = ""
                        if rep_suggestion:
                            diff = simple_diff(sentence, rep_suggestion)
                        
                        rows.append({
                            "page": page_no,
                            "sentence": sentence,
                            "snippet": snippet,
                            "sources": ",".join(flags),
                            "error_types": ",".join(error_types) if error_types else "",
                            "suggestion_by_source": json.dumps(suggestions, ensure_ascii=False),
                            "representative_suggestion": rep_suggestion or "",
                            "diff": diff,
                            "is_ocr": is_ocr
                        })
                        
                except Exception as e:
                    print(f"문장 처리 오류: {e}")
    
    # 결과 정렬 (우선순위: rule > 다중 검사기 > 단일 검사기)
    def sort_key(row):
        sources = row["sources"].split(",")
        priority = 0
        if "rule" in sources:
            priority += 100
        if len(sources) > 1:
            priority += 10
        return (-priority, row["page"], row["sources"])
    
    rows.sort(key=sort_key)
    
    # 결과 저장
    df = pd.DataFrame(rows)
    
    if args.format in ["csv", "both"]:
        csv_path = os.path.join(args.out_dir, "review.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"CSV 저장: {csv_path}")
    
    if args.format in ["xlsx", "both"]:
        xlsx_path = os.path.join(args.out_dir, "review.xlsx")
        df.to_excel(xlsx_path, index=False)
        print(f"XLSX 저장: {xlsx_path}")
    
    # 통계 출력
    print(f"\n=== 처리 완료 ===")
    print(f"총 페이지: {len(pages)}")
    print(f"총 문장: {total_sentences}")
    print(f"플래그된 문장: {flagged_sentences}")
    print(f"검출률: {flagged_sentences/total_sentences*100:.1f}%" if total_sentences > 0 else "검출률: 0%")
    
    # 검사기별 통계
    if rows:
        source_counts = {}
        for row in rows:
            for source in row["sources"].split(","):
                source_counts[source] = source_counts.get(source, 0) + 1
        
        print(f"\n=== 검사기별 통계 ===")
        for source, count in sorted(source_counts.items()):
            print(f"{source}: {count}건")
    
    # 검사기 정리
    for checker in checkers:
        try:
            checker.shutdown()
        except:
            pass

if __name__ == "__main__":
    main()
