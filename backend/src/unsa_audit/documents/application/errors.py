class DocumentsError(Exception):
    """Error base del modulo documents."""


class DocumentNotFound(DocumentsError):
    pass


class VersionNotFound(DocumentsError):
    pass


class ChangeRequestNotFound(DocumentsError):
    pass


class InvalidChangeRequest(DocumentsError):
    """Datos de la solicitud invalidos (campos vacios o demasiado largos)."""


class NoChanges(DocumentsError):
    """El contenido propuesto es igual al vigente (tras normalizar)."""


class AlreadyResolved(DocumentsError):
    pass


class StaleBase(DocumentsError):
    """El documento avanzo desde la version sobre la que se propuso el cambio."""
