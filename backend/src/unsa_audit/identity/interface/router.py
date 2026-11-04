from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from unsa_audit.identity.domain.errors import (
    EmailNotAvailable,
    InvalidCredentials,
    InvalidRegistration,
)
from unsa_audit.identity.domain.user import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    User,
)
from unsa_audit.identity.interface.dependencies import CurrentUser, SuperAdmin

router = APIRouter(tags=["identity"])


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    full_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(
            id=str(user.id), email=user.email, full_name=user.full_name, role=user.role.value
        )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/auth/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(body: RegisterRequest, request: Request) -> UserResponse:
    try:
        user = await request.app.state.register_user.execute(
            body.email, body.password, body.full_name
        )
    except InvalidRegistration as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Datos de registro inválidos"
        ) from exc
    except EmailNotAvailable as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email no disponible") from exc
    return UserResponse.from_domain(user)


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request) -> LoginResponse:
    try:
        result = await request.app.state.login.execute(body.email, body.password)
    except InvalidCredentials as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return LoginResponse(
        access_token=result.access_token, user=UserResponse.from_domain(result.user)
    )


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse.from_domain(user)


@router.get("/admin/ping")
async def admin_ping(_: SuperAdmin) -> dict[str, str]:
    return {"status": "ok"}
