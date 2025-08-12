#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국어 PDF 오탈자 검수 시스템 사용 예제
"""

import os
from run import TypoDetector

def example_usage():
    """기본 사용 예제"""
    
    # 설정 구성
    config = {
        "pdf_path": "sample.pdf",  # 검수할 PDF 파일 경로
        "out_dir": "out",          # 출력 디렉토리
        "max_workers_io": 2,       # 외부요청 동시성 (Hanspell 등)
        "max_workers_cpu": 4,      # CPU 작업 동시성 (PyKoSpacing, 규칙 등)
        "korean_ratio_min": 0.3,   # 최소 한글 비중
        "snippet_length": 60,      # 스니펫 길이
        "ocr_threshold": 20,       # OCR 사용 임계값
        "rate_limit_hanspell": 3,  # Hanspell 초당 요청 제한 (보수적)
        "enable_cache": True,      # 캐시 사용
        "save_detailed": True      # 상세 통계 저장
    }
    
    print("한국어 PDF 오탈자 검수 시스템 예제")
    print("=" * 50)
    
    # PDF 파일 존재 확인
    if not os.path.exists(config["pdf_path"]):
        print(f"PDF 파일을 찾을 수 없습니다: {config['pdf_path']}")
        print("사용법:")
        print("1. PDF 파일을 프로젝트 루트에 배치")
        print("2. 파일명을 'sample.pdf'로 변경하거나 config의 pdf_path 수정")
        print("3. python example.py 실행")
        return
    
    try:
        # 검수 시스템 초기화
        print("검수 시스템 초기화 중...")
        detector = TypoDetector(config)
        
        # PDF 처리 및 오탈자 검출
        print(f"\nPDF 처리 시작: {config['pdf_path']}")
        results = detector.process_pdf(config["pdf_path"])
        
        # 결과 저장
        print("\n결과 저장 중...")
        detector.save_results(results, "example_review")
        
        # 요약 출력
        detector.print_summary()
        
        print(f"\n예제 실행 완료!")
        print(f"결과 파일은 '{config['out_dir']}' 디렉토리에 저장되었습니다.")
        print(f"웹 뷰어로 확인하려면 'viewer.html' 파일을 브라우저에서 열어주세요.")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        print("\n문제 해결 방법:")
        print("1. requirements.txt의 패키지들이 모두 설치되었는지 확인")
        print("2. PDF 파일이 올바른 경로에 있는지 확인")
        print("3. 인터넷 연결 상태 확인 (Hanspell API 사용 시)")

def example_with_custom_rules():
    """사용자 정의 규칙을 사용하는 예제"""
    
    print("\n사용자 정의 규칙 예제")
    print("=" * 30)
    
    # 사용자 정의 규칙 추가
    from checkers.rule_checker import RuleChecker
    
    custom_rules = [
        {
            "name": "사용자 정의 규칙",
            "pattern": r"테스트",
            "hint": "테스트라는 단어가 포함된 문장",
            "examples": ["테스트 문장입니다"]
        }
    ]
    
    # 규칙 검사기 생성
    rules_checker = RuleChecker()
    rules_checker.rules.extend(custom_rules)
    
    # 테스트 문장 검사
    test_sentences = [
        "이것은 테스트 문장입니다.",
        "정상적인 문장입니다.",
        "또 다른 테스트 문장입니다."
    ]
    
    print("사용자 정의 규칙 테스트:")
    for sentence in test_sentences:
        result = rules_checker.check(sentence)
        status = "오류 발견" if result["flag"] else "정상"
        print(f"  '{sentence}' → {status}")
        if result["flag"]:
            print(f"    제안: {result['suggestions']}")

def example_whitelist_management():
    """화이트리스트 관리 예제"""
    
    print("\n화이트리스트 관리 예제")
    print("=" * 30)
    
    from checkers.rule_checker import RuleChecker
    
    # 화이트리스트가 있는 규칙 검사기 생성
    rules_checker = RuleChecker(whitelist_path="data/whitelist.txt")
    
    # 현재 화이트리스트 확인
    current_whitelist = rules_checker.get_whitelist()
    print(f"현재 화이트리스트 ({len(current_whitelist)}개):")
    for word in sorted(list(current_whitelist))[:10]:  # 처음 10개만 표시
        print(f"  - {word}")
    
    # 새로운 용어 추가
    new_term = "새로운용어"
    rules_checker.add_whitelist_word(new_term)
    print(f"\n새로운 용어 추가: {new_term}")
    
    # 화이트리스트 파일에 저장
    rules_checker.save_whitelist("data/updated_whitelist.txt")
    print("업데이트된 화이트리스트를 'data/updated_whitelist.txt'에 저장했습니다.")

if __name__ == "__main__":
    print("한국어 PDF 오탈자 검수 시스템 - 사용 예제")
    print("=" * 60)
    
    # 기본 사용 예제
    example_usage()
    
    # 추가 예제들
    example_with_custom_rules()
    example_whitelist_management()
    
    print("\n" + "=" * 60)
    print("모든 예제 실행 완료!")
    print("\n시스템 사용법:")
    print("1. python run.py <PDF파일경로> - 기본 실행")
    print("2. python example.py - 예제 실행")
    print("3. viewer.html - 웹 뷰어로 결과 확인")
