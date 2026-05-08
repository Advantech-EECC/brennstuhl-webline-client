"""Allow running `python -m brennstuhl_webline_client` as the psu CLI."""

import sys

from .cli import main

sys.exit(main())
