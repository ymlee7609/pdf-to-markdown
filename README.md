# pdf-to-markdown

High-performance CLI tool to convert PDF documents to Markdown format. Supports PyMuPDF4LLM (default) and Marker (high-quality option) backends.

[한국어](README.ko.md) | **English**

## Key Features

- **Fast conversion**: PyMuPDF4LLM backend for rapid PDF processing
- **High-quality conversion**: Marker backend for superior table and image handling
- **Batch processing**: Convert multiple PDFs in a directory at once
- **Page selection**: Convert specific pages using flexible page syntax
- **Image control**: Extract images with customizable format and DPI options
- **Chapter splitting**: Auto-split output into per-chapter files when markdown exceeds 500KB for RAG pipeline optimization
- **Easy installation**: Quick setup with uv package manager

## Installation

### Basic Installation (PyMuPDF4LLM Backend)

```bash
uv venv && uv pip install -e ".[dev]"
```

### With Marker Backend (High-Quality Conversion)

```bash
uv pip install -e ".[marker]"
```

**Note**: Marker backend is recommended to run with GPU for optimal performance.

## Usage

### Basic Usage

Convert a single PDF file:

```bash
pdf2md input.pdf -o output.md
```

Or using the module directly:

```bash
python -m pdf_to_markdown input.pdf -o output.md
```

### Backend Selection

Use PyMuPDF backend (default):

```bash
pdf2md input.pdf --engine pymupdf
```

Use Marker backend (high-quality):

```bash
pdf2md input.pdf --engine marker
```

### Page Range Selection

Convert specific pages only:

```bash
pdf2md input.pdf --pages 0,5-7,10
```

### Image Processing Options

Convert without images:

```bash
pdf2md input.pdf --no-images
```

Set image format and DPI:

```bash
pdf2md input.pdf --image-format png --dpi 150
```

### Batch Processing

Convert all PDFs in a directory:

```bash
pdf2md sample/ -o output/
```

### Chapter Splitting

The tool automatically splits large markdown files (>500KB) into per-chapter files for RAG pipeline optimization:

**Auto-split** (splits when markdown exceeds 500KB):
```bash
pdf2md large_document.pdf -o output/
```

**Force split** (always split by chapters):
```bash
pdf2md input.pdf --split
```

**Disable split** (keep single markdown file):
```bash
pdf2md input.pdf --no-split
```

#### Chapter Split Output Structure

When chapter splitting is active, output is organized as follows:

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

**Split Behavior**:
- Splits by `#` (h1) headings; falls back to `##` (h2) if no h1 found
- Code blocks are excluded from heading detection
- Content before the first heading is saved as `00_front-matter.md`
- Files are numbered and named as `NN_slugified-title.md`
- Images are stored in shared `_images/` subdirectory for easy reference
- Threshold: 500KB (UTF-8 bytes) per file

### Verbose Output

View detailed conversion progress:

```bash
pdf2md input.pdf -v
```

## Project Structure

```
pdf_to_markdown/
├── pyproject.toml
├── src/pdf_to_markdown/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                 # CLI interface
│   ├── converter.py           # Conversion protocol & data classes
│   ├── splitter.py            # Chapter splitting logic
│   ├── backends/
│   │   ├── __init__.py        # Backend factory
│   │   ├── pymupdf.py         # PyMuPDF4LLM backend
│   │   └── marker.py          # Marker backend (optional)
│   ├── batch.py               # Batch processing
│   └── output.py              # Markdown & image output
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

## Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| pymupdf4llm >=1.27.2 | Default conversion backend | Yes |
| pymupdf >=1.27.2 | PDF page counting & image extraction | Yes |
| marker-pdf >=1.10.0 | High-quality conversion backend | Optional |
| pytest, pytest-cov | Testing framework | Dev |
| ruff | Code linting | Dev |

## Backend Comparison

| | PyMuPDF4LLM | Marker |
|---|---|---|
| Speed | Fast (seconds) | Slow (minutes) |
| Memory | Low | High |
| Table handling | Basic | Excellent |
| Image handling | Basic | Excellent |
| Installation | Required | Optional |
| GPU | Not needed | Recommended |

## Development

### Run Tests

Run all tests with coverage report:

```bash
pytest tests/ -v --cov=pdf_to_markdown --cov-report=term-missing
```

Run tests excluding slow tests:

```bash
pytest tests/ -m "not slow"
```

### Code Linting

```bash
ruff check src/ tests/
```

### Test Coverage

Current test coverage: **106 tests passing**, targeting **85%+** coverage.

## Requirements

- Python >= 3.10
- uv package manager (recommended)

## License

License information to be updated.

## Contributing

Contributing guidelines to be updated.

## Support

Please submit issues and bug reports through the issue tracker.
