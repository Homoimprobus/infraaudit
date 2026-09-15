"""Remote Linux system information collection and parsing."""

from dataclasses import dataclass
from collections.abc import Callable


SYSTEM_INFO_COMMAND = (
    "set -eu; "
    "hostname_value=$(hostname); "
    "pretty_name=$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | head -n 1); "
    "kernel_value=$(uname -r); "
    "architecture_value=$(uname -m); "
    "test -n \"$pretty_name\"; "
    "printf '%s\\0%s\\0%s\\0%s\\0' "
    "\"$hostname_value\" \"$pretty_name\" \"$kernel_value\" \"$architecture_value\""
)


@dataclass(frozen=True)
class SystemInfo:
    """Selected system information from a remote Linux host."""

    hostname: str
    os_name: str
    kernel: str
    architecture: str


class InvalidSystemInfoError(ValueError):
    """The remote system information response is invalid."""


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_system_info(response: str) -> SystemInfo:
    """Parse one NUL-framed system information response."""
    fields = response.split("\0")
    if len(fields) != 5 or fields[-1] != "" or any(not field for field in fields[:-1]):
        raise InvalidSystemInfoError("malformed system information response")
    return SystemInfo(
        hostname=fields[0],
        os_name=_unquote(fields[1]),
        kernel=fields[2],
        architecture=fields[3],
    )


def collect_system_info(run_command: Callable[[str], str]) -> SystemInfo:
    """Collect and parse system information with one remote command."""
    return parse_system_info(run_command(SYSTEM_INFO_COMMAND))
