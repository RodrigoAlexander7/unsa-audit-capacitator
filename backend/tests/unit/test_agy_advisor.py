"""AC-007-5: el adaptador de `agy` contra un script falso que imita su contrato."""

import json
import os
import stat
import sys
import time
from pathlib import Path

import pytest

from unsa_audit.analytics.application.errors import AdvisorTimeout, AdvisorUnavailable
from unsa_audit.analytics.infrastructure.agy_advisor import AgyCliAdvisor, minimal_env

FAKE = """
import json, os, sys, time
from pathlib import Path

prompt = sys.argv[2]
Path(__file__).with_name("record.json").write_text(json.dumps({
    "argv": sys.argv[1:],
    "cwd": os.getcwd(),
    "cwd_entries": os.listdir(os.getcwd()),
    "env_keys": sorted(os.environ),
    "has_secret": "JWT_SECRET" in os.environ,
}))
if "TIMEOUT" in prompt:
    time.sleep(30)
if "EXIT3" in prompt:
    sys.exit(3)
if "BADJSON" in prompt:
    print("esto no es json")
    sys.exit(0)
if "NOSUCCESS" in prompt:
    print(json.dumps({"status": "ERROR", "response": "x"}))
    sys.exit(0)
if "EMPTY" in prompt:
    print(json.dumps({"status": "SUCCESS", "response": "   "}))
    sys.exit(0)
if "BIG" in prompt:
    print(json.dumps({"status": "SUCCESS", "response": "x" * 20000}))
    sys.exit(0)
print("linea de ruido previa")
print(json.dumps({"status": "SUCCESS", "response": "Respuesta de prueba", "duration_seconds": 0.1}))
"""


@pytest.fixture
def fake(tmp_path: Path) -> tuple[str, Path]:
    script = tmp_path / "fake_agy.py"
    script.write_text(FAKE, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return f"{sys.executable} {script}", tmp_path / "record.json"


def _advisor(command: str, **kwargs) -> AgyCliAdvisor:
    return AgyCliAdvisor(command, "--output-format json --mode plan --sandbox", **kwargs)


@pytest.mark.ac("AC-007-5")
async def test_exito_invoca_con_argumentos_sin_shell_y_en_un_directorio_vacio(fake, monkeypatch):
    command, record = fake
    monkeypatch.setenv("JWT_SECRET", "no-debe-llegar-a-la-ia")
    answer = await _advisor(command, timeout_seconds=20).ask("Pregunta normal")
    assert answer.text == "Respuesta de prueba" and answer.duration_ms >= 0

    seen = json.loads(record.read_text())
    assert seen["argv"] == [
        "--print", "Pregunta normal", "--output-format", "json", "--mode", "plan", "--sandbox",
        "--print-timeout", "20s",
    ]  # fmt: skip
    assert seen["cwd_entries"] == [], "directorio de trabajo vacio"
    assert not seen["cwd"].startswith(str(Path.cwd())) or seen["cwd"] != str(Path.cwd())
    assert seen["has_secret"] is False, "el entorno no hereda secretos"
    assert set(seen["env_keys"]) <= set(minimal_env()) | {"LC_CTYPE", "PWD", "SHLVL", "_"}


@pytest.mark.ac("AC-007-5")
async def test_el_prompt_llega_como_un_unico_argumento_aunque_tenga_metacaracteres(fake) -> None:
    command, record = fake
    nasty = "$(touch /tmp/pwned) `id` ; rm -rf / && echo \"hola\" 'x' \n--flag-falso\n| cat"
    await _advisor(command).ask(nasty)
    assert json.loads(record.read_text())["argv"][1] == nasty
    assert not os.path.exists("/tmp/pwned"), "la inyeccion no se ejecuto"  # noqa: ASYNC240


@pytest.mark.ac("AC-007-5")
async def test_timeout_mata_el_proceso_y_lanza_advisor_timeout(fake) -> None:
    command, _ = fake
    started = time.monotonic()
    with pytest.raises(AdvisorTimeout):
        await _advisor(command, timeout_seconds=1, grace_seconds=0).ask("TIMEOUT")
    assert time.monotonic() - started < 10, "no espera los 30 s del script"


@pytest.mark.ac("AC-007-5")
@pytest.mark.parametrize("trigger", ["EXIT3", "BADJSON", "NOSUCCESS", "EMPTY"])
async def test_errores_se_traducen_a_advisor_unavailable(fake, trigger) -> None:
    command, _ = fake
    with pytest.raises(AdvisorUnavailable):
        await _advisor(command).ask(trigger)


@pytest.mark.ac("AC-007-5")
async def test_comando_inexistente(tmp_path: Path) -> None:
    with pytest.raises(AdvisorUnavailable, match="No se encontró"):
        await _advisor("agy-que-no-existe-xyz").ask("hola")
    not_executable = tmp_path / "x"
    not_executable.write_text("#!/bin/sh\n")
    with pytest.raises(AdvisorUnavailable):
        await _advisor(str(not_executable)).ask("hola")


@pytest.mark.ac("AC-007-5")
async def test_respuesta_muy_larga_se_trunca(fake) -> None:
    command, _ = fake
    answer = await _advisor(command, max_chars=100).ask("BIG")
    assert answer.text.startswith("x" * 100) and answer.text.endswith("*(respuesta truncada)*")
    assert len(answer.text) < 200


def test_el_entorno_minimo_solo_tiene_variables_de_la_lista_blanca(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "x")
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    env = minimal_env()
    assert "JWT_SECRET" not in env and "DATABASE_URL" not in env
    assert env.get("PATH") == os.environ.get("PATH")
