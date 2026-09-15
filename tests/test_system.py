import pytest

from infraaudit.system import (
    SYSTEM_INFO_COMMAND,
    InvalidSystemInfoError,
    collect_system_info,
)


def test_collect_system_info_invokes_runner_once():
    calls = []
    response = "host\0Debian 13\0kernel\0x86_64\0"

    def run_command(command):
        calls.append(command)
        return response

    assert collect_system_info(run_command).hostname == "host"
    assert calls == [SYSTEM_INFO_COMMAND]


@pytest.mark.parametrize("response", ["", "host\0Debian\0kernel", "host\0\0kernel\0x86_64\0"])
def test_empty_or_malformed_system_response_is_rejected(response):
    with pytest.raises(InvalidSystemInfoError, match="malformed system information response"):
        collect_system_info(lambda command: response)
