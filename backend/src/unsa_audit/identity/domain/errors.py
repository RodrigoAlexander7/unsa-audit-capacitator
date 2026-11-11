class IdentityError(Exception):
    """Error base del modulo identity."""


class InvalidRegistration(IdentityError):
    """Email o password no cumplen las reglas."""


class EmailNotAvailable(IdentityError):
    """El email ya existe o esta reservado (no se distingue a proposito)."""


class InvalidCredentials(IdentityError):
    """Email o password incorrectos (mensaje generico)."""


class InvalidToken(IdentityError):
    """Token ausente, malformado, firmado mal o expirado."""
