"""Command-line entry point for InfraAudit."""

import argparse
import sys
from collections.abc import Sequence


VERSION = "0.1.0"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the InfraAudit command-line interface."""
    parser = argparse.ArgumentParser(
        prog="infraaudit",
        description="Infrastructure auditing CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"InfraAudit {VERSION}",
        help="show the application version and exit",
    )

    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        parser.print_help()
        return 0

    parser.parse_args(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())