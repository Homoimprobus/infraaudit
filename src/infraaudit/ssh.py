"""OpenSSH command execution for remote InfraAudit scans."""

from dataclasses import dataclass
from pathlib import Path
import subprocess


class SSHError(RuntimeError):
    """Base class for SSH failures."""


class SSHExecutableNotFoundError(SSHError):
    """The system OpenSSH executable is not installed."""


class SSHConnectionError(SSHError):
    """The SSH connection could not be established."""


class SSHAuthenticationError(SSHError):
    """SSH authentication failed."""


class RemoteCommandError(SSHError):
    """A command failed after SSH connected."""


@dataclass(frozen=True)
class SSHClient:
    """Run fixed commands through the system OpenSSH client."""

    host: str
    user: str
    identity: str

    def __post_init__(self) -> None:
        identity_path = Path(self.identity).expanduser()
        if not identity_path.is_file():
            raise FileNotFoundError(f"identity file not found: {identity_path}")
        object.__setattr__(self, "identity", str(identity_path))

    def run(self, command: str) -> str:
        """Run one remote command and return its standard output."""
        arguments = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "ConnectTimeout=5",
            "-i",
            self.identity,
            f"{self.user}@{self.host}",
            command,
        ]
        try:
            result = subprocess.run(
                arguments,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as error:
            raise SSHExecutableNotFoundError(
                "OpenSSH executable 'ssh' was not found"
            ) from error

        if result.returncode == 0:
            return result.stdout

        error_output = result.stderr.strip()
        lower_error = error_output.lower()
        if any(
            phrase in lower_error
            for phrase in (
                "permission denied",
                "authentication failed",
                "no supported authentication methods",
            )
        ):
            raise SSHAuthenticationError(
                f"SSH authentication failed: {error_output or 'unknown error'}"
            )
        if result.returncode == 255:
            raise SSHConnectionError(
                f"SSH connection failed: {error_output or 'unknown error'}"
            )
        raise RemoteCommandError(
            f"remote command failed: {error_output or 'unknown error'}"
        )
