"""Command-line entry point for InfraAudit."""

import argparse
import sys
from collections.abc import Sequence

from infraaudit.ssh import SSHAuthenticationError, SSHClient, SSHConnectionError
from infraaudit.ssh import SSHExecutableNotFoundError, RemoteCommandError
from infraaudit.system import InvalidSystemInfoError, collect_system_info


VERSION = "0.1.0"


def _build_parser() -> argparse.ArgumentParser:
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
    subparsers = parser.add_subparsers(dest="command")
    scan_parser = subparsers.add_parser("scan", help="scan a remote Linux host")
    scan_parser.add_argument("host", help="remote host to scan")
    scan_parser.add_argument("--user", required=True, help="SSH username")
    scan_parser.add_argument(
        "--identity",
        required=True,
        help="path to the SSH private key",
    )
    return parser


def _run_scan(args: argparse.Namespace) -> int:
    try:
        client = SSHClient(host=args.host, user=args.user, identity=args.identity)
        system_info = collect_system_info(client.run)
    except FileNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except SSHExecutableNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except SSHAuthenticationError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except SSHConnectionError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except RemoteCommandError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except InvalidSystemInfoError as error:
        print(f"Error: invalid system information: {error}", file=sys.stderr)
        return 1

    print(f"InfraAudit {VERSION}")
    print()
    print(f"Target: {args.host}")
    print()
    print("[OK] SSH connection established")
    print()
    print("System")
    print(f"  Hostname: {system_info.hostname}")
    print(f"  OS:       {system_info.os_name}")
    print(f"  Kernel:   {system_info.kernel}")
    print(f"  Arch:     {system_info.architecture}")
    print(f"  Uptime:   {system_info.uptime_seconds:.2f} seconds")
    print(
        "  Load:     "
        f"{system_info.load_average_1:.2f}, "
        f"{system_info.load_average_5:.2f}, "
        f"{system_info.load_average_15:.2f}"
    )
    print(f"  CPUs:     {system_info.logical_cpus}")
    print(
        "  Memory:   "
        f"{system_info.memory_used_bytes} / {system_info.memory_total_bytes} bytes"
    )
    print(
        "  Root FS:  "
        f"{system_info.root_used_bytes} / {system_info.root_total_bytes} bytes"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the InfraAudit command-line interface."""
    parser = _build_parser()
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        parser.print_help()
        return 0

    parsed_args = parser.parse_args(args)
    if parsed_args.command == "scan":
        return _run_scan(parsed_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())