from uuid import uuid4

import pytest

from tests.unit.fakes import FakeHasher, InMemoryUserRepository
from unsa_audit.identity.application.use_cases import (
    EnsureSuperadmin,
    GetCurrentUser,
    Login,
    RegisterUser,
)
from unsa_audit.identity.domain.errors import (
    EmailNotAvailable,
    InvalidCredentials,
    InvalidRegistration,
    InvalidToken,
)
from unsa_audit.identity.domain.user import Role
from unsa_audit.identity.infrastructure.security import Argon2PasswordHasher, JwtTokenService

SUPERADMIN = "Superadmin@Test.example"
SECRET = "s" * 32


@pytest.fixture
def repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def register(repo: InMemoryUserRepository) -> RegisterUser:
    return RegisterUser(repo, FakeHasher(), SUPERADMIN)


@pytest.mark.ac("AC-002-1")
async def test_registro_crea_learner_con_password_hasheado(
    register: RegisterUser, repo: InMemoryUserRepository
) -> None:
    user = await register.execute("  Ana@Example.com ", "password123", " Ana Quispe ")
    assert user.role is Role.LEARNER
    assert user.email == "ana@example.com"
    assert user.full_name == "Ana Quispe"
    assert user.password_hash != "password123"
    assert repo.users[user.id] == user


@pytest.mark.ac("AC-002-2")
async def test_email_duplicado_sin_distinguir_mayusculas(register: RegisterUser) -> None:
    await register.execute("ana@example.com", "password123", "Ana")
    with pytest.raises(EmailNotAvailable):
        await register.execute("ANA@example.com", "otrapassword", "Otra Ana")


@pytest.mark.ac("AC-002-3")
async def test_email_superadmin_esta_reservado(register: RegisterUser) -> None:
    with pytest.raises(EmailNotAvailable):
        await register.execute("superadmin@test.example", "password123", "Intruso")


@pytest.mark.ac("AC-002-4")
@pytest.mark.parametrize(
    ("email", "password", "name"),
    [
        ("ana@example.com", "corta", "Ana"),
        ("sin-arroba", "password123", "Ana"),
        ("ana@example.com", "password123", "   "),
    ],
)
async def test_registro_invalido(register: RegisterUser, email: str, password: str, name: str):
    with pytest.raises(InvalidRegistration):
        await register.execute(email, password, name)


@pytest.mark.ac("AC-002-5")
async def test_login_exitoso_y_fallos_con_mismo_error(
    register: RegisterUser, repo: InMemoryUserRepository
) -> None:
    tokens = JwtTokenService(SECRET, 30)
    login = Login(repo, FakeHasher(), tokens)
    user = await register.execute("ana@example.com", "password123", "Ana")

    result = await login.execute("ANA@example.com", "password123")
    assert result.user.id == user.id
    assert tokens.decode(result.access_token).user_id == user.id

    with pytest.raises(InvalidCredentials):
        await login.execute("ana@example.com", "mala-password")
    with pytest.raises(InvalidCredentials):
        await login.execute("nadie@example.com", "password123")


@pytest.mark.ac("AC-002-6")
async def test_get_current_user_con_token_valido(
    register: RegisterUser, repo: InMemoryUserRepository
) -> None:
    tokens = JwtTokenService(SECRET, 30)
    user = await register.execute("ana@example.com", "password123", "Ana")
    token = tokens.issue(user.id, user.role)
    assert await GetCurrentUser(repo, tokens).execute(token) == user


@pytest.mark.ac("AC-002-6")
async def test_get_current_user_rechaza_tokens_invalidos(
    repo: InMemoryUserRepository, register: RegisterUser
) -> None:
    tokens = JwtTokenService(SECRET, 30)
    use_case = GetCurrentUser(repo, tokens)
    user = await register.execute("ana@example.com", "password123", "Ana")

    with pytest.raises(InvalidToken):
        await use_case.execute("no-es-un-jwt")
    with pytest.raises(InvalidToken):
        await use_case.execute(
            JwtTokenService("otra-clave-" + "x" * 21, 30).issue(user.id, user.role)
        )
    with pytest.raises(InvalidToken):
        await use_case.execute(JwtTokenService(SECRET, -1).issue(user.id, user.role))  # expirado
    with pytest.raises(InvalidToken):
        await use_case.execute(tokens.issue(uuid4(), Role.LEARNER))  # usuario inexistente


@pytest.mark.ac("AC-002-7")
async def test_ensure_superadmin_es_idempotente(repo: InMemoryUserRepository) -> None:
    use_case = EnsureSuperadmin(repo, FakeHasher(), SUPERADMIN, "clave-superadmin")
    first = await use_case.execute()
    second = await use_case.execute()
    assert first.id == second.id
    assert len(repo.users) == 1
    assert second.role is Role.SUPERADMIN
    assert second.email == "superadmin@test.example"


@pytest.mark.ac("AC-002-7")
async def test_ensure_superadmin_repara_rol_de_cuenta_existente(
    repo: InMemoryUserRepository,
) -> None:
    pre = RegisterUser(repo, FakeHasher(), "otro@test.example")
    existing = await pre.execute("superadmin@test.example", "password123", "Preexistente")
    user = await EnsureSuperadmin(repo, FakeHasher(), SUPERADMIN, "clave-superadmin").execute()
    assert user.id == existing.id
    assert user.role is Role.SUPERADMIN


@pytest.mark.ac("AC-002-9")
def test_argon2_hashea_y_verifica() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("password123")
    assert hashed.startswith("$argon2")
    assert "password123" not in hashed
    assert hasher.verify("password123", hashed)
    assert not hasher.verify("otra", hashed)
    assert not hasher.verify("password123", "basura-no-hash")
