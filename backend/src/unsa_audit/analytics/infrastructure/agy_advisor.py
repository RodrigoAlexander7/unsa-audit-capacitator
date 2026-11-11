"""Asesor IA via `agy` (Antigravity CLI) en modo no interactivo.

Contrato verificado (spike): `agy --print <prompt> --output-format json ...` imprime un JSON con
`status` ("SUCCESS"), `response` (texto) y `duration_seconds`.
"""

import asyncio
import json
import os
import shlex
import tempfile
import time
from asyncio.subprocess import DEVNULL, PIPE, Process

from unsa_audit.analytics.application.errors import AdvisorTimeout, AdvisorUnavailable
from unsa_audit.analytics.application.ports import AdvisorAnswer

_MAX_STDOUT_BYTES = 256 * 1024
_ENV_WHITELIST = (
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "TERM",
    "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR",
)  # fmt: skip


def minimal_env() -> dict[str, str]:
    """Entorno por lista blanca: la IA no hereda secretos del backend."""
    return {k: os.environ[k] for k in _ENV_WHITELIST if k in os.environ}


class AgyCliAdvisor:
    def __init__(
        self,
        command: str = "agy",
        args: str = "--output-format json --mode plan --sandbox --effort low",
        timeout_seconds: int = 120,
        max_chars: int = 8000,
        grace_seconds: int = 5,
    ) -> None:
        self._command = command
        self._args = args
        self._timeout = timeout_seconds
        self._max_chars = max_chars
        self._grace = grace_seconds  # margen sobre el timeout propio de agy

    def _argv(self, prompt: str) -> list[str]:
        # El prompt es UN solo argumento: nunca pasa por un shell.
        return [
            *shlex.split(self._command),
            "--print",
            prompt,
            *shlex.split(self._args),
            "--print-timeout",
            f"{self._timeout}s",
        ]

    async def _read_stdout(self, process: Process) -> bytes:
        assert process.stdout is not None
        data = bytearray()
        while chunk := await process.stdout.read(65536):
            data += chunk
            if len(data) > _MAX_STDOUT_BYTES:
                break
        return bytes(data)

    async def ask(self, prompt: str) -> AdvisorAnswer:
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="agy-") as workdir:  # directorio de trabajo vacio
            try:
                process = await asyncio.create_subprocess_exec(
                    *self._argv(prompt),
                    cwd=workdir,
                    env=minimal_env(),
                    stdin=DEVNULL,
                    stdout=PIPE,
                    stderr=DEVNULL,
                )
            except (FileNotFoundError, PermissionError) as exc:
                raise AdvisorUnavailable("No se encontró el comando de la IA (agy).") from exc

            try:
                stdout = await asyncio.wait_for(
                    self._read_stdout(process), self._timeout + self._grace
                )
                await asyncio.wait_for(process.wait(), 5)
            except TimeoutError as exc:
                process.kill()
                await process.wait()
                raise AdvisorTimeout("La IA tardó demasiado en responder.") from exc
            finally:
                if process.returncode is None:
                    process.kill()
                    await process.wait()

        if process.returncode != 0:
            raise AdvisorUnavailable(f"La IA terminó con error (código {process.returncode}).")
        return AdvisorAnswer(self._parse(stdout), int((time.monotonic() - started) * 1000))

    def _parse(self, stdout: bytes) -> str:
        text = stdout.decode("utf-8", errors="replace").strip()
        payload = None
        for candidate in (text, *reversed(text.splitlines())):
            try:
                payload = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if not isinstance(payload, dict) or payload.get("status") != "SUCCESS":
            raise AdvisorUnavailable("La IA no devolvió una respuesta válida.")
        response = payload.get("response")
        if not isinstance(response, str) or not response.strip():
            raise AdvisorUnavailable("La IA devolvió una respuesta vacía.")
        response = response.strip()
        if len(response) > self._max_chars:
            response = response[: self._max_chars].rstrip() + "\n\n*(respuesta truncada)*"
        return response
