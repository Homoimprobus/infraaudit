"""Remote Linux system information collection and parsing."""

from dataclasses import dataclass
from collections.abc import Callable
import math


SYSTEM_INFO_COMMAND = (
    "set -eu; "
    "hostname_value=$(hostname); "
    "pretty_name=$(sed -n 's/^PRETTY_NAME=//p' /etc/os-release | head -n 1); "
    "kernel_value=$(uname -r); "
    "architecture_value=$(uname -m); "
    "uptime_value=$(awk '{print $1}' /proc/uptime); "
    "read -r load_1 load_5 load_15 _ < /proc/loadavg; "
    "cpu_count=$(awk '/^processor[[:space:]]*:/ {count++} END {print count}' /proc/cpuinfo); "
    "memory_values=$(awk '/^MemTotal:[[:space:]]+/ {total=$2 * 1024} "
    "/^MemAvailable:[[:space:]]+/ {available=$2 * 1024} "
    "END {if (total == \"\" || available == \"\") exit 1; "
    "printf \"%.0f %.0f\\n\", total, total - available}' /proc/meminfo); "
    "memory_total=${memory_values%% *}; "
    "memory_used=${memory_values#* }; "
    "root_values=$(df -P -B1 / | awk 'NR == 2 {print $2, $3}'); "
    "root_total=${root_values%% *}; "
    "root_used=${root_values#* }; "
    "test -n \"$pretty_name\"; "
    "test -n \"$uptime_value\" -a -n \"$load_1\" -a -n \"$load_5\" -a -n \"$load_15\"; "
    "test -n \"$cpu_count\" -a -n \"$memory_values\" -a -n \"$root_values\"; "
    "printf '%s\\0%s\\0%s\\0%s\\0%s\\0%s\\0%s\\0%s\\0%s\\0%s\\0%s\\0%s\\0%s\\0' "
    "\"$hostname_value\" \"$pretty_name\" \"$kernel_value\" \"$architecture_value\" "
    "\"$uptime_value\" \"$load_1\" \"$load_5\" \"$load_15\" \"$cpu_count\" "
    "\"$memory_total\" \"$memory_used\" \"$root_total\" \"$root_used\""
)


@dataclass(frozen=True)
class SystemInfo:
    """Selected system information from a remote Linux host."""

    hostname: str
    os_name: str
    kernel: str
    architecture: str
    uptime_seconds: float
    load_average_1: float
    load_average_5: float
    load_average_15: float
    logical_cpus: int
    memory_total_bytes: int
    memory_used_bytes: int
    root_total_bytes: int
    root_used_bytes: int


class InvalidSystemInfoError(ValueError):
    """The remote system information response is invalid."""


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_system_info(response: str) -> SystemInfo:
    """Parse one NUL-framed system information response."""
    fields = response.split("\0")
    if fields[-1:] != [""] or any(not field for field in fields[:-1]):
        raise InvalidSystemInfoError("malformed system information response")
    if len(fields) != 14:
        raise InvalidSystemInfoError("malformed system information response")

    try:
        uptime_seconds = float(fields[4])
        loads = tuple(float(value) for value in fields[5:8])
        integer_values = tuple(int(value) for value in fields[8:13])
    except ValueError as error:
        raise InvalidSystemInfoError("malformed system information response") from error
    if (
        not math.isfinite(uptime_seconds)
        or not all(math.isfinite(value) for value in loads)
        or uptime_seconds < 0
        or any(value < 0 for value in loads)
        or integer_values[0] <= 0
        or any(value < 0 for value in integer_values[1:])
        or integer_values[2] > integer_values[1]
        or integer_values[4] > integer_values[3]
    ):
        raise InvalidSystemInfoError("malformed system information response")

    return SystemInfo(
        hostname=fields[0],
        os_name=_unquote(fields[1]),
        kernel=fields[2],
        architecture=fields[3],
        uptime_seconds=uptime_seconds,
        load_average_1=loads[0],
        load_average_5=loads[1],
        load_average_15=loads[2],
        logical_cpus=integer_values[0],
        memory_total_bytes=integer_values[1],
        memory_used_bytes=integer_values[2],
        root_total_bytes=integer_values[3],
        root_used_bytes=integer_values[4],
    )


def collect_system_info(run_command: Callable[[str], str]) -> SystemInfo:
    """Collect and parse system information with one remote command."""
    return parse_system_info(run_command(SYSTEM_INFO_COMMAND))
