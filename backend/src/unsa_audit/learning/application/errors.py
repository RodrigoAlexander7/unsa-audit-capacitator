class LearningError(Exception):
    """Error base del modulo learning."""


class RouteNotFound(LearningError):
    pass


class ModuleNotFound(LearningError):
    pass


class NotEnrolled(LearningError):
    """El usuario no esta matriculado en la ruta del modulo."""


class PrerequisiteNotMet(LearningError):
    def __init__(self, prerequisite_code: str) -> None:
        super().__init__(prerequisite_code)
        self.prerequisite_code = prerequisite_code


class ModuleLocked(LearningError):
    """El modulo aun no esta disponible (p. ej. evaluacion final)."""


class NoExercise(LearningError):
    """El modulo no tiene ejercicio (solo lectura)."""


class HasExercise(LearningError):
    """El modulo tiene ejercicio: no se completa solo con leerlo."""
