import pytest

from infraaudit.system import (
    SYSTEM_INFO_COMMAND,
    InvalidSystemInfoError,
    collect_system_info,
)


def test_collect_system_info_invokes_runner_once():
    assert SYSTEM_INFO_COMMAND.count("%s") == 13
    calls = []
    response = (
        "host\x00Debian 13\x00kernel\x00x86_64\x00"
        "123.5\x000.5\x000.25\x000.1\x004\x0016000\x001000\x0020000\x005000\x00"
    )

    def run_command(command):
        calls.append(command)
        return response

    assert collect_system_info(run_command).hostname == "host"
    assert calls == [SYSTEM_INFO_COMMAND]


def test_parse_system_info_reads_resource_information():
    response = (
        "host\x00Debian\x00kernel\x00x86_64\x00"
        "123.5\x000.5\x000.25\x000.1\x004\x0016000\x001000\x0020000\x005000\x00"
    )

    info = collect_system_info(lambda command: response)

    assert info.uptime_seconds == 123.5
    assert (info.load_average_1, info.load_average_5, info.load_average_15) == (
        0.5,
        0.25,
        0.1,
    )
    assert info.logical_cpus == 4
    assert (info.memory_total_bytes, info.memory_used_bytes) == (16000, 1000)
    assert (info.root_total_bytes, info.root_used_bytes) == (20000, 5000)


@pytest.mark.parametrize(
    "response",
    [
        "",
        "host\0Debian\0kernel",
        "host\0\0kernel\0x86_64\0",
        "host\0Debian\0kernel\0x86_64\0",
    ],
)
def test_empty_or_malformed_system_response_is_rejected(response):
    with pytest.raises(InvalidSystemInfoError, match="malformed system information response"):
        collect_system_info(lambda command: response)


@pytest.mark.parametrize(
    "response",
    [
        "host\x00Debian\x00kernel\x00x86_64\x00not-a-number\x000.5\x000.25\x000.1\x004\x0016000\x001000\x0020000\x005000\x00",
        "host\x00Debian\x00kernel\x00x86_64\x001\x000.5\x000.25\x000.1\x004\x0016000\x0017000\x0020000\x005000\x00",
        "host\x00Debian\x00kernel\x00x86_64\x001\x000.5\x000.25\x000.1\x004\x0016000\x001000\x002000\x005000\x00",
    ],
)
def test_invalid_resource_information_is_rejected(response):
    with pytest.raises(InvalidSystemInfoError, match="malformed system information response"):
        collect_system_info(lambda command: response)


def test_parse_system_info_accepts_large_memory_values():
    response = (
        "host\x00Debian\x00kernel\x00x86_64\x00"
        "86400\x000.1\x000.2\x000.3\x008\x00343597383680\x00171798691840\x00"
        "549755813888\x00274877906944\x00"
    )

    info = collect_system_info(lambda command: response)

    assert info.memory_total_bytes == 343597383680
    assert info.memory_used_bytes == 171798691840
