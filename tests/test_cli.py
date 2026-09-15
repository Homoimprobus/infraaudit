from pathlib import Path

import pytest

from infraaudit.cli import main
from infraaudit.ssh import SSHAuthenticationError, SSHConnectionError, RemoteCommandError


def test_version_is_unchanged(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--version"])
    assert error.value.code == 0
    assert capsys.readouterr().out == "InfraAudit 0.1.0\n"


def test_scan_prints_system_information(monkeypatch, capsys, tmp_path: Path):
    identity = tmp_path / "id_ed25519"
    identity.touch()
    response = (
        "infraaudit-debian13\x00"
        '"Debian GNU/Linux 13 (trixie)"\x00'
        "6.12.107+deb13-amd64\x00"
        "x86_64\x00"
        "123.5\x000.5\x000.25\x000.1\x004\x0016000\x001000\x0020000\x005000\x00"
    )

    monkeypatch.setattr(
        "infraaudit.ssh.SSHClient.run",
        lambda self, command: response,
    )

    assert (
        main(
            [
                "scan",
                "192.168.122.141",
                "--user",
                "improbus",
                "--identity",
                str(identity),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "Target: 192.168.122.141" in output
    assert "Hostname: infraaudit-debian13" in output
    assert "OS:       Debian GNU/Linux 13 (trixie)" in output
    assert "Uptime:   123.50 seconds" in output
    assert "Load:     0.50, 0.25, 0.10" in output
    assert "CPUs:     4" in output
    assert "Memory:   1000 / 16000 bytes" in output
    assert "Root FS:  5000 / 20000 bytes" in output


def test_scan_reports_missing_identity(capsys, tmp_path: Path):
    result = main(
        [
            "scan",
            "host",
            "--user",
            "user",
            "--identity",
            str(tmp_path / "missing"),
        ]
    )
    assert result != 0
    assert "identity file not found" in capsys.readouterr().err


def test_scan_reports_malformed_system_information(monkeypatch, capsys, tmp_path: Path):
    identity = tmp_path / "id_ed25519"
    identity.touch()
    monkeypatch.setattr(
        "infraaudit.ssh.SSHClient.run",
        lambda self, command: "malformed response",
    )

    result = main(
        [
            "scan",
            "host",
            "--user",
            "user",
            "--identity",
            str(identity),
        ]
    )

    captured = capsys.readouterr()
    assert result != 0
    assert captured.out == ""
    assert "Error: invalid system information:" in captured.err


def test_scan_reports_remote_failures(monkeypatch, capsys, tmp_path: Path):
    identity = tmp_path / "id_ed25519"
    identity.touch()
    for error, message in (
        (SSHAuthenticationError("SSH authentication failed"), "authentication failed"),
        (SSHConnectionError("SSH connection failed"), "connection failed"),
        (RemoteCommandError("remote command failed"), "remote command failed"),
    ):
        monkeypatch.setattr(
            "infraaudit.ssh.SSHClient.run",
            lambda self, command, error=error: (_ for _ in ()).throw(error),
        )
        assert (
            main(
                [
                    "scan",
                    "host",
                    "--user",
                    "user",
                    "--identity",
                    str(identity),
                ]
            )
            != 0
        )
        assert message in capsys.readouterr().err
