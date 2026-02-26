"""Allow running as `python -m pdf_to_markdown`."""

import sys

from pdf_to_markdown.cli import main

if __name__ == "__main__":
    sys.exit(main())
