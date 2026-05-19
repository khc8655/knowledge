"""Allow running as `python -m kb_cli`."""
import sys
from kb_cli.main import main

sys.exit(main())
