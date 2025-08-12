# 한국어 PDF 오탈자 자동 검수 시스템

대용량 PDF에서 한국어 오탈자, 맞춤법, 띄어쓰기 오류를 자동으로 검출하는 시스템입니다.

## 주요 기능

- **다중 검사기 OR 로직**: Hanspell, PyKoSpacing, 규칙 기반 검사
- **스마트 텍스트 추출**: PyMuPDF + Tesseract OCR 자동 전환
- **한국어 최적화**: kss 문장 분리, 한글 비중 필터링
- **사람 검수 친화적**: Excel/CSV 출력, diff 표시, 화이트리스트 관리

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

```bash
python run.py
```

## 출력 파일

- `out/review.xlsx`: 검수 결과 (Excel)
- `out/review.csv`: 검수 결과 (CSV)
- `out/false_positive.csv`: 오탐 제거용 화이트리스트

## 프로젝트 구조

```
project/
├── run.py                 # 메인 실행 파일
├── checkers/             # 검사기 모듈
│   ├── base.py
│   ├── hanspell_checker.py
│   ├── spacing_checker.py
│   └── rule_checker.py
├── utils/                # 유틸리티 모듈
│   ├── pdf.py
│   ├── text.py
│   └── diff.py
├── data/                 # 설정 파일
│   ├── whitelist.txt
│   └── rules.yaml
└── out/                  # 출력 디렉토리
```
