# pdf-to-markdown

PDF 문서를 마크다운으로 변환하는 고성능 CLI 도구입니다. PyMuPDF4LLM(기본) 및 Marker(고품질 옵션) 백엔드를 지원합니다.

**한국어** | [English](README.md)

## 주요 기능

- **빠른 변환**: PyMuPDF4LLM 백엔드를 사용한 고속 변환
- **고품질 변환**: Marker 백엔드로 표와 이미지를 더욱 정확하게 처리
- **일괄 처리**: 디렉토리 내 여러 PDF 파일을 한 번에 변환
- **페이지 선택**: 유연한 페이지 선택 문법으로 특정 페이지만 변환
- **이미지 제어**: 이미지 추출 옵션 및 포맷, DPI 설정
- **챕터 분할**: 마크다운이 500KB를 초과할 때 자동으로 챕터 단위로 분할하여 RAG 파이프라인 최적화
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

**참고**: Marker 백엔드는 최적의 성능을 위해 GPU 사용을 권장합니다.

## 사용법

### 기본 사용

단일 PDF 파일 변환:

```bash
pdf2md input.pdf -o output.md
```

또는 모듈 직접 사용:

```bash
python -m pdf_to_markdown input.pdf -o output.md
```

### 백엔드 선택

PyMuPDF 백엔드 사용 (기본값):

```bash
pdf2md input.pdf --engine pymupdf
```

Marker 백엔드 사용 (고품질):

```bash
pdf2md input.pdf --engine marker
```

### 페이지 범위 지정

특정 페이지만 변환:

```bash
pdf2md input.pdf --pages 0,5-7,10
```

### 이미지 처리 옵션

이미지 없이 변환:

```bash
pdf2md input.pdf --no-images
```

이미지 포맷 및 DPI 설정:

```bash
pdf2md input.pdf --image-format png --dpi 150
```

### 디렉토리 일괄 변환

디렉토리 내 모든 PDF 파일을 변환:

```bash
pdf2md sample/ -o output/
```

### 챕터 분할

도구는 큰 마크다운 파일(>500KB)을 자동으로 챕터 단위로 분할하여 RAG 파이프라인을 최적화합니다:

**자동 분할** (마크다운이 500KB를 초과할 때 분할):
```bash
pdf2md large_document.pdf -o output/
```

**강제 분할** (항상 챕터 단위로 분할):
```bash
pdf2md input.pdf --split
```

**분할 비활성화** (단일 마크다운 파일 유지):
```bash
pdf2md input.pdf --no-split
```

#### 챕터 분할 출력 구조

챕터 분할이 활성화되면 다음과 같이 구성됩니다:

```
document/
├── 00_front-matter.md
├── 01_introduction.md
├── 02_system-architecture.md
├── 03_implementation-guide.md
└── _images/
    ├── page0_image1.png
    ├── page5_image2.png
    └── page10_image3.png
```

**분할 동작**:
- `#` (h1) 제목으로 분할; h1이 없으면 `##` (h2)로 폴백
- 코드 블록은 제목 감지에서 제외
- 첫 번째 제목 이전의 내용은 `00_front-matter.md`로 저장
- 파일은 `NN_slugified-title.md` 형식으로 번호 지정 및 이름 지정
- 이미지는 공유 `_images/` 하위 디렉토리에 저장되어 쉬운 참조 가능
- 임계값: 파일당 500KB (UTF-8 바이트)

### 상세 출력

변환 과정을 자세히 확인:

```bash
pdf2md input.pdf -v
```

## 프로젝트 구조

```
pdf_to_markdown/
├── pyproject.toml
├── src/pdf_to_markdown/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                 # CLI 인터페이스
│   ├── converter.py           # 변환 프로토콜 및 데이터 클래스
│   ├── splitter.py            # 챕터 분할 로직
│   ├── backends/
│   │   ├── __init__.py        # 백엔드 팩토리
│   │   ├── pymupdf.py         # PyMuPDF4LLM 백엔드
│   │   └── marker.py          # Marker 백엔드 (선택적)
│   ├── batch.py               # 일괄 처리
│   └── output.py              # 마크다운 및 이미지 출력
└── tests/
    ├── conftest.py
    ├── test_converter.py
    ├── test_pymupdf_backend.py
    ├── test_marker_backend.py
    ├── test_cli.py
    ├── test_batch.py
    ├── test_output.py
    └── test_splitter.py
```

## 의존성

| 패키지 | 용도 | 필수 여부 |
|--------|------|-----------|
| pymupdf4llm >=1.27.2 | 기본 변환 백엔드 | 필수 |
| pymupdf >=1.27.2 | PDF 페이지 수 확인 및 이미지 추출 | 필수 |
| marker-pdf >=1.10.0 | 고품질 변환 백엔드 | 선택 (pip install .[marker]) |
| pytest, pytest-cov | 테스트 프레임워크 | 개발 |
| ruff | 코드 린팅 | 개발 |

## 백엔드 비교

| | PyMuPDF4LLM | Marker |
|---|---|---|
| 속도 | 빠름 (초 단위) | 느림 (분 단위) |
| 메모리 | 낮음 | 높음 |
| 표 처리 | 기본 | 우수 |
| 이미지 처리 | 기본 | 우수 |
| 설치 | 필수 | 선택 |
| GPU | 불필요 | 권장 |

## 개발

### 테스트 실행

전체 테스트 및 커버리지 확인:

```bash
pytest tests/ -v --cov=pdf_to_markdown --cov-report=term-missing
```

느린 테스트를 제외한 테스트만 실행:

```bash
pytest tests/ -m "not slow"
```

### 코드 린팅

```bash
ruff check src/ tests/
```

### 테스트 커버리지

현재 테스트 상태: **106개 테스트 통과**, **85%+** 커버리지 목표.

## 요구사항

- Python >= 3.10
- uv 패키지 매니저 (권장)

## 라이선스

라이선스 정보는 추후 업데이트 예정입니다.

## 기여

기여 가이드라인은 추후 업데이트 예정입니다.

## 지원

이슈 및 버그 리포트는 이슈 트래커를 통해 제출해 주세요.
