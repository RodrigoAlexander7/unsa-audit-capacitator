from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from unsa_audit.identity.application.use_cases import GetCurrentUser
from unsa_audit.identity.domain.errors import InvalidToken
from unsa_audit.identity.domain.user import User

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise _unauthorized()
    use_case: GetCurrentUser = request.app.state.get_current_user
    try:
        return await use_case.execute(credentials.credentials)
    except InvalidToken as exc:
        raise _unauthorized() from exc


async def require_superadmin(user: Annotated[User, Depends(current_user)]) -> User:
    if not user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso insuficiente")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
SuperAdmin = Annotated[User, Depends(require_superadmin)]
