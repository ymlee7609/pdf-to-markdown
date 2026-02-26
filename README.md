# pdf-to-markdown

PDF를 마크다운으로 변환하는 고성능 CLI 도구입니다. PyMuPDF4LLM(기본)과 Marker(고품질 옵션) 백엔드를 지원합니다.

## 주요 기능

- **빠른 변환**: PyMuPDF4LLM 백엔드를 사용한 기본 고속 변환
- **고품질 변환**: Marker 백엔드로 표와 그림을 더욱 정확하게 처리
- **일괄 처리**: 디렉토리 내 여러 PDF 파일을 한 번에 변환
- **페이지 선택**: 특정 페이지만 선택적으로 변환
- **이미지 제어**: 이미지 추출 옵션 및 포맷 설정
- **간편한 설치**: uv 패키지 매니저로 빠른 환경 구성

## 설치

### 기본 설치 (PyMuPDF4LLM 백엔드)

```bash
uv venv && uv pip install -e ".[dev]"
```

### Marker 백엔드 포함 설치 (고품질 변환)

```bash
uv pip install -e ".[marker]"
```

**참고**: Marker 백엔드는 최적의 성능을 위해 GPU를 권장합니다.

## 사용법

### 기본 사용

단일 PDF 파일 변환:

```bash
python -m pdf_to_markdown input.pdf -o output.md
```

또는 설치된 CLI 명령 사용:

```bash
pdf2md input.pdf -o output.md
```

### 백엔드 선택

PyMuPDF 백엔드 사용 (기본값):

```bash
python -m pdf_to_markdown input.pdf --engine pymupdf
```

Marker 백엔드 사용 (고품질):

```bash
python -m pdf_to_markdown input.pdf --engine marker
```

### 페이지 범위 지정

특정 페이지만 변환:

```bash
python -m pdf_to_markdown input.pdf --pages 0,5-7,10
```

### 이미지 처리 옵션

이미지 없이 변환:

```bash
python -m pdf_to_markdown input.pdf --no-images
```

이미지 포맷 및 DPI 설정:

```bash
python -m pdf_to_markdown input.pdf --image-format png --dpi 150
```

### 디렉토리 일괄 변환

디렉토리 내 모든 PDF 파일을 변환:

```bash
python -m pdf_to_markdown sample/ -o output/
```

### 상세 출력

변환 과정을 자세히 확인:

```bash
python -m pdf_to_markdown input.pdf -v
```

## 프로젝트 구조

```
pdf_to_markdown/
├── pyproject.toml              # 프로젝트 설정 및 의존성
├── src/pdf_to_markdown/
│   ├── __init__.py
│   ├── __main__.py            # 메인 진입점
│   ├── cli.py                 # CLI 인터페이스
│   ├── converter.py           # 변환 프로토콜 및 데이터 클래스
│   ├── backends/
│   │   ├── __init__.py        # 백엔드 팩토리
│   │   ├── pymupdf.py         # PyMuPDF4LLM 백엔드
│   │   └── marker.py          # Marker 백엔드 (선택적)
│   ├── batch.py               # 일괄 변환 처리
│   └── output.py              # 마크다운 및 이미지 출력
└── tests/
    ├── conftest.py
    ├── test_converter.py
    ├── test_pymupdf_backend.py
    ├── test_marker_backend.py
    ├── test_cli.py
    ├── test_batch.py
    └── test_output.py
```

## 의존성

| 패키지 | 용도 | 필수 여부 |
|--------|------|-----------|
| pymupdf4llm | 기본 변환 백엔드 | 필수 |
| pymupdf | PDF 페이지 수 확인 및 이미지 추출 | 필수 |
| marker-pdf | 고품질 변환 백엔드 | 선택 (pip install .[marker]) |
| pytest, pytest-cov | 테스트 프레임워크 | 개발 |
| ruff | 코드 린팅 | 개발 |

## 백엔드 비교

### PyMuPDF4LLM (pymupdf)
- **장점**: 빠른 속도, 가벼운 메모리 사용
- **용도**: 대부분의 PDF 문서에 적합
- **설치**: 기본 포함
- **특징**: 기본 백엔드로 빠른 변환 제공

### Marker (marker-pdf)
- **장점**: 높은 품질, 표와 그림 처리 우수
- **용도**: 복잡한 레이아웃의 문서
- **설치**: 선택적 (`pip install .[marker]`)
- **특징**: GPU 사용 시 최적 성능

## 개발

### 테스트 실행

전체 테스트 및 커버리지 확인:

```bash
pytest tests/ -v --cov=pdf_to_markdown --cov-report=term-missing
```

빠른 테스트만 실행 (느린 테스트 제외):

```bash
pytest tests/ -m "not slow"
```

### 코드 린팅

```bash
ruff check src/ tests/
```

### 테스트 커버리지

현재 테스트 커버리지: **100%** (59개 테스트 통과)

## 요구사항

- Python >= 3.10
- uv 패키지 매니저

## 라이선스

라이선스 정보는 추후 업데이트 예정입니다.

## 기여

기여 가이드라인은 추후 업데이트 예정입니다.

## 문의

프로젝트 관련 문의사항이나 버그 리포트는 이슈 트래커를 통해 제출해 주세요.
