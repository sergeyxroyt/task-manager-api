#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        message = (
            "Couldn't import Django. Is it installed and available on your "
            "PYTHONPATH environment variable? "
            "Did you forget to activate a virtual "
            "environment?"
        )
        raise ImportError(message) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
