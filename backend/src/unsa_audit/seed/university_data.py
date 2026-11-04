"""Dataset ficticio de la UNSA (POC). Nombres, cargos y datos son inventados.

Los ids son deterministas (uuid5 sobre un slug) para que el seed sea idempotente y
las referencias entre entidades no dependan del orden de insercion.
"""

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, UUID, uuid5

from unsa_audit.university.domain.entities import (
    DataOwner,
    DataOwnerRole,
    OrgUnit,
    OrgUnitKind,
    Person,
    PersonKind,
    Position,
    ProcessingActivity,
    System,
)

_NS = uuid5(NAMESPACE_URL, "https://unsa-audit-poc.example/seed")


def uid(slug: str) -> UUID:
    return uuid5(_NS, slug)


@dataclass
class UniversityDataset:
    org_units: list[OrgUnit] = field(default_factory=list)  # padres antes que hijos
    positions: list[Position] = field(default_factory=list)  # jefes antes que subordinados
    people: list[Person] = field(default_factory=list)
    systems: list[System] = field(default_factory=list)
    data_owners: list[DataOwner] = field(default_factory=list)
    processing_activities: list[ProcessingActivity] = field(default_factory=list)


_FIRST_NAMES = [
    "Ana", "Luis", "María", "Carlos", "Rosa", "Jorge", "Lucía", "Miguel", "Elena", "Pedro",
    "Carmen", "Raúl", "Silvia", "Andrés", "Patricia", "Héctor", "Valeria", "Diego", "Sofía", "Iván",
]  # fmt: skip
_SURNAMES = [
    "Quispe", "Mamani", "Huamán", "Condori", "Flores", "Ccori", "Salas", "Paredes",
    "Cáceres", "Valdivia", "Zúñiga", "Ramos", "Cuadros", "Medina", "Arce", "Bellido",
    "Choque", "Delgado", "Escobedo", "Fuentes", "Gamarra", "Herrera", "Lazo", "Núñez",
]  # fmt: skip


def _name(index: int) -> str:
    """Nombre ficticio unico y determinista para cada indice < 120."""
    first = _FIRST_NAMES[index % len(_FIRST_NAMES)]
    s1 = _SURNAMES[index % len(_SURNAMES)]
    s2 = _SURNAMES[(index * 5 + 3) % len(_SURNAMES)]
    if s1 == s2:
        s2 = _SURNAMES[(index * 5 + 4) % len(_SURNAMES)]
    return f"{first} {s1} {s2}"


_FACULTIES: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "FIPS",
        "Facultad de Ingeniería de Producción y Servicios",
        [("EISI", "Ingeniería de Sistemas"), ("EIIN", "Ingeniería Industrial"),
         ("EIEL", "Ingeniería Electrónica")],
    ),
    (
        "FCNF",
        "Facultad de Ciencias Naturales y Formales",
        [("EBIO", "Biología"), ("EFIS", "Física"), ("EMAT", "Matemática")],
    ),
    (
        "FCHS",
        "Facultad de Ciencias Histórico Sociales",
        [("EHIS", "Historia"), ("ESOC", "Sociología"), ("EPSI", "Psicología")],
    ),
    (
        "FCSA",
        "Facultad de Ciencias de la Salud",
        [("EENF", "Enfermería"), ("ENUT", "Nutrición"), ("EOBS", "Obstetricia")],
    ),
]  # fmt: skip


class _Builder:
    def __init__(self) -> None:
        self.ds = UniversityDataset()
        self._person_index = 0

    def unit(self, code: str, kind: OrgUnitKind, name: str, parent: str | None) -> None:
        self.ds.org_units.append(
            OrgUnit(
                id=uid(f"unit:{code}"),
                parent_id=uid(f"unit:{parent}") if parent else None,
                kind=kind,
                name=name,
                code=code,
            )
        )

    def position(
        self, slug: str, unit: str, title: str, reports_to: str | None, kind: PersonKind
    ) -> None:
        """Crea el cargo y su titular (una persona ficticia)."""
        self.ds.positions.append(
            Position(
                id=uid(f"pos:{slug}"),
                org_unit_id=uid(f"unit:{unit}"),
                title=title,
                reports_to_position_id=uid(f"pos:{reports_to}") if reports_to else None,
            )
        )
        self.person(f"holder:{slug}", kind, position=slug)

    def person(self, slug: str, kind: PersonKind, position: str | None = None) -> None:
        self.ds.people.append(
            Person(
                id=uid(f"person:{slug}"),
                full_name=_name(self._person_index),
                kind=kind,
                position_id=uid(f"pos:{position}") if position else None,
            )
        )
        self._person_index += 1

    def system(
        self,
        slug: str,
        name: str,
        description: str,
        unit: str,
        categories: tuple[str, ...],
        owners: list[tuple[str, DataOwnerRole]],
    ) -> None:
        self.ds.systems.append(
            System(
                id=uid(f"system:{slug}"),
                name=name,
                description=description,
                owner_org_unit_id=uid(f"unit:{unit}"),
                data_categories=categories,
            )
        )
        for position_slug, role in owners:
            self.ds.data_owners.append(
                DataOwner(
                    system_id=uid(f"system:{slug}"),
                    person_id=uid(f"person:holder:{position_slug}"),
                    role=role,
                )
            )

    def activity(
        self,
        slug: str,
        unit: str,
        name: str,
        purpose: str,
        legal_basis: str,
        categories: tuple[str, ...],
        retention: str,
    ) -> None:
        self.ds.processing_activities.append(
            ProcessingActivity(
                id=uid(f"activity:{slug}"),
                org_unit_id=uid(f"unit:{unit}"),
                name=name,
                purpose=purpose,
                legal_basis=legal_basis,
                data_categories=categories,
                retention=retention,
            )
        )


def build_university_dataset() -> UniversityDataset:
    b = _Builder()
    adm, doc, est = PersonKind.ADMINISTRATIVO, PersonKind.DOCENTE, PersonKind.ESTUDIANTE
    ctrl, proc, stew = DataOwnerRole.CONTROLLER, DataOwnerRole.PROCESSOR, DataOwnerRole.STEWARD

    # --- Unidades organicas (padres primero) ---
    b.unit("UNSA", OrgUnitKind.RECTORADO, "Rectorado", None)
    b.unit("VRAC", OrgUnitKind.VICERRECTORADO, "Vicerrectorado Académico", "UNSA")
    b.unit("VRIN", OrgUnitKind.VICERRECTORADO, "Vicerrectorado de Investigación", "UNSA")
    for code, name, parent in [
        ("OTI", "Oficina de Tecnologías de la Información", "UNSA"),
        ("SGEN", "Secretaría General", "UNSA"),
        ("OCI", "Órgano de Control Institucional", "UNSA"),
        ("ORH", "Oficina de Recursos Humanos", "UNSA"),
        ("ORA", "Oficina de Registros Académicos", "VRAC"),
        ("BIBL", "Biblioteca Central", "VRAC"),
        ("OBU", "Oficina de Bienestar Universitario", "VRAC"),
    ]:
        b.unit(code, OrgUnitKind.OFICINA, name, parent)
    for fac_code, fac_name, schools in _FACULTIES:
        b.unit(fac_code, OrgUnitKind.FACULTAD, fac_name, "VRAC")
        for school_code, school_name in schools:
            b.unit(
                school_code, OrgUnitKind.ESCUELA, f"Escuela Profesional de {school_name}", fac_code
            )

    # --- Cargos y titulares (jefes antes que subordinados) ---
    b.position("rector", "UNSA", "Rector", None, adm)
    b.position("vr-academico", "VRAC", "Vicerrector Académico", "rector", adm)
    b.position("vr-investigacion", "VRIN", "Vicerrector de Investigación", "rector", adm)
    b.position(
        "jefe-oti", "OTI", "Jefe de la Oficina de Tecnologías de la Información", "rector", adm
    )
    b.position("sec-general", "SGEN", "Secretario General", "rector", adm)
    b.position("jefe-oci", "OCI", "Jefe del Órgano de Control Institucional", None, adm)
    b.position("jefe-orh", "ORH", "Jefe de la Oficina de Recursos Humanos", "rector", adm)
    b.position("jefe-ora", "ORA", "Jefe de Registros Académicos", "vr-academico", adm)
    b.position("dir-biblioteca", "BIBL", "Director de la Biblioteca Central", "vr-academico", adm)
    b.position("jefe-obu", "OBU", "Jefe de Bienestar Universitario", "vr-academico", adm)
    b.position("dpo", "OTI", "Oficial de Protección de Datos Personales", "jefe-oti", adm)
    b.position("ciso", "OTI", "Responsable de Seguridad de la Información", "jefe-oti", adm)
    for fac_code, fac_name, schools in _FACULTIES:
        b.position(f"decano-{fac_code}", fac_code, f"Decano de {fac_name}", "vr-academico", doc)
        for school_code, school_name in schools:
            b.position(
                f"dir-{school_code}",
                school_code,
                f"Director de la Escuela de {school_name}",
                f"decano-{fac_code}",
                doc,
            )

    # --- Personas sin cargo directivo ---
    for i in range(20):
        b.person(f"docente-{i}", doc)
    for i in range(14):
        b.person(f"estudiante-{i}", est)
    for i in range(6):
        b.person(f"admin-{i}", adm)

    # --- Sistemas y dueños de datos ---
    b.system(
        "matricula", "Sistema de Matrícula", "Inscripción de estudiantes en cursos por semestre.",
        "ORA", ("identificación", "datos académicos"),
        [("jefe-ora", ctrl), ("jefe-oti", proc), ("dpo", stew)],
    )  # fmt: skip
    b.system(
        "notas", "Sistema de Notas y Actas", "Registro de calificaciones y emisión de actas.",
        "ORA", ("identificación", "calificaciones"),
        [("jefe-ora", ctrl), ("jefe-oti", proc)],
    )  # fmt: skip
    b.system(
        "biblioteca", "Biblioteca Digital", "Catálogo y préstamo de material bibliográfico.",
        "BIBL", ("identificación", "historial de préstamos"),
        [("dir-biblioteca", ctrl), ("jefe-oti", proc)],
    )  # fmt: skip
    b.system(
        "aula-virtual", "Aula Virtual", "Plataforma de cursos en línea.",
        "OTI", ("identificación", "actividad de aprendizaje", "calificaciones"),
        [("jefe-oti", ctrl), ("ciso", stew)],
    )  # fmt: skip
    b.system(
        "planillas", "Sistema de Planillas y RR. HH.", "Gestión de personal y remuneraciones.",
        "ORH", ("identificación", "datos laborales", "datos bancarios", "datos de salud"),
        [("jefe-orh", ctrl), ("jefe-oti", proc), ("dpo", stew)],
    )  # fmt: skip
    b.system(
        "tramite", "Trámite Documentario", "Mesa de partes y seguimiento de expedientes.",
        "SGEN", ("identificación", "contenido de expedientes"),
        [("sec-general", ctrl), ("jefe-oti", proc)],
    )  # fmt: skip
    b.system(
        "correo", "Correo Institucional", "Cuentas de correo para estudiantes, docentes y personal.",
        "OTI", ("identificación", "comunicaciones"),
        [("jefe-oti", ctrl), ("ciso", stew)],
    )  # fmt: skip
    b.system(
        "bienestar", "Sistema de Bienestar y Salud", "Atención de salud y becas estudiantiles.",
        "OBU", ("identificación", "datos de salud", "datos socioeconómicos"),
        [("jefe-obu", ctrl), ("jefe-oti", proc), ("dpo", stew)],
    )  # fmt: skip

    # --- Actividades de tratamiento ---
    b.activity(
        "matricula", "ORA", "Matrícula de estudiantes",
        "Inscribir estudiantes en las asignaturas de cada semestre.",
        "Ejecución de la relación académica", ("identificación", "datos académicos"),
        "Mientras dure la condición de estudiante y 10 años después",
    )  # fmt: skip
    b.activity(
        "actas", "ORA", "Emisión de actas y certificados",
        "Registrar calificaciones y emitir constancias oficiales.",
        "Obligación legal", ("identificación", "calificaciones"), "Permanente (archivo académico)",
    )  # fmt: skip
    b.activity(
        "prestamos", "BIBL", "Préstamo bibliográfico",
        "Controlar préstamos y devoluciones de material.",
        "Interés legítimo", ("identificación", "historial de préstamos"), "2 años",
    )  # fmt: skip
    b.activity(
        "planillas", "ORH", "Gestión de planillas",
        "Calcular y pagar remuneraciones al personal.",
        "Obligación legal", ("identificación", "datos laborales", "datos bancarios"), "10 años",
    )  # fmt: skip
    b.activity(
        "seleccion", "ORH", "Selección de personal docente",
        "Evaluar postulantes a plazas docentes.",
        "Consentimiento", ("identificación", "currículum", "antecedentes"), "1 año tras el concurso",
    )  # fmt: skip
    b.activity(
        "salud", "OBU", "Atención de salud estudiantil",
        "Brindar atención básica y derivaciones médicas.",
        "Consentimiento explícito", ("identificación", "datos de salud"), "5 años",
    )  # fmt: skip
    b.activity(
        "becas", "OBU", "Becas y ayudas socioeconómicas",
        "Evaluar y otorgar beneficios a estudiantes.",
        "Ejecución de la relación académica", ("identificación", "datos socioeconómicos"), "5 años",
    )  # fmt: skip
    b.activity(
        "tramite", "SGEN", "Trámite documentario",
        "Registrar y dar seguimiento a expedientes administrativos.",
        "Obligación legal", ("identificación", "contenido de expedientes"), "Según tabla de retención",
    )  # fmt: skip
    b.activity(
        "cuentas", "OTI", "Administración de cuentas institucionales",
        "Crear y dar de baja cuentas de acceso y correo.",
        "Ejecución de la relación académica o laboral", ("identificación", "credenciales"),
        "Mientras dure el vínculo y 6 meses después",
    )  # fmt: skip
    b.activity(
        "videovigilancia", "OTI", "Videovigilancia del campus",
        "Resguardar la seguridad de personas e instalaciones.",
        "Interés legítimo", ("imagen",), "30 días",
    )  # fmt: skip
    return b.ds
