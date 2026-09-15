from pathlib import Path
import subprocess

import pytest

from infraaudit.ssh import (
    SSHAuthenticationError,
    SSHClient,
    SSHConnectionError,
    SSHExecutableNotFoundError,
    RemoteCommandError,
)


def test_ssh_command_uses_required_options(monkeypatch, tmp_path: Path):
    identity = tmp_path / "key"
    identity.touch()
    completed = subprocess.CompletedProcess([], 0, stdout="ok\n", stderr="")
    calls = []

    def fake_run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return completed

    monkeypatch.setattr("infraaudit.ssh.subprocess.run", fake_run)
    assert SSHClient("host", "user", str(identity)).run("hostname") == "ok\n"
    arguments, kwargs = calls[0]
    assert arguments == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "ConnectTimeout=5",
        "-i",
        str(identity),
        "user@host",
        "hostname",
    ]
    assert kwargs.get("shell", False) is False


@pytest.mark.parametrize(
    ("returncode", "stderr", "error_type"),
    [
        (255, "Connection timed out", SSHConnectionError),
        (255, "Permission denied (publickey)", SSHAuthenticationError),
        (1, "command failed", RemoteCommandError),
    ],
)
def test_ssh_failures_are_explicit(
    monkeypatch, tmp_path: Path, returncode, stderr, error_type
):
    identity = tmp_path / "key"
    identity.touch()
    monkeypatch.setattr(
        "infraaudit.ssh.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            [], returncode, stdout="", stderr=stderr
        ),
    )
    with pytest.raises(error_type):
        SSHClient("host", "user", str(identity)).run("hostname")


def test_missing_ssh_executable(monkeypatch, tmp_path: Path):
    identity = tmp_path / "key"
    identity.touch()
    monkeypatch.setattr(
        "infraaudit.ssh.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError),
    )
    with pytest.raises(SSHExecutableNotFoundError):
        SSHClient("host", "user", str(identity)).run("hostname")
