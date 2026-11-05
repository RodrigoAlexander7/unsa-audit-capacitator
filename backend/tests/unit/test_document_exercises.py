"""Tests unitarios de dominio para los 6 nuevos tipos de ejercicio documental (Spec 009)."""

import re
from pathlib import Path
from typing import Any

import pytest

from tests.solutions import solve, wrong
from unsa_audit.learning.domain.exercises import (
    InvalidAnswer,
    InvalidExerciseSpec,
    grade,
    to_public,
    validate_spec,
)
from unsa_audit.learning.domain.route import ExerciseKind

ROOT = Path(__file__).resolve().parents[3]

# ----------------------------------------------------------------------------- specs canonicas

DOCUMENT_FORM_ALCANCE: dict[str, Any] = {
    "prompt": "Completa la ficha del Documento de alcance del PIMS para la ampliación OBU + FCSA.",
    "scenario": (
        "La UNSA amplía el Alcance del PIMS (etapa 2) para incorporar la Oficina de Bienestar "
        "Universitario (OBU) y las prácticas clínicas de la Facultad de Ciencias de la Salud "
        "(FCSA), que utilizan el Sistema de Bienestar y Salud y remiten análisis clínicos a un "
        "laboratorio médico externo contratado. Las facultades FIPS, FCNF y FCHS siguen fuera "
        "y el Sistema de Planillas y RR. HH. pertenece a ORH."
    ),
    "document_title": "Documento de alcance del PIMS — Ampliación OBU y FCSA",
    "sections": [
        {
            "id": "control",
            "title": "1. Control documental",
            "fields": [
                {
                    "id": "doc_code",
                    "label": "Código del documento",
                    "type": "text",
                    "required": True,
                    "validation": {
                        "pattern": r"^PIMS-ALC-\d{3}$",
                        "sample_solution": "PIMS-ALC-002",
                        "feedback_error": "Usa el formato institucional PIMS-ALC-NNN.",
                    },
                },
                {
                    "id": "owner_position",
                    "label": "Responsable del documento",
                    "type": "position",
                    "required": True,
                    "options": [
                        {"id": "dpo", "label": "Oficial de Protección de Datos Personales"},
                        {"id": "jefe-oti", "label": "Jefe de la OTI"},
                        {"id": "jefe-ora", "label": "Jefe de Registros Académicos"},
                        {"id": "rector", "label": "Rector"},
                    ],
                    "validation": {
                        "accepted": ["dpo", "jefe-oti"],
                        "feedback_error": "El dueño del alcance debe ser DPO o Jefe de OTI.",
                    },
                },
                {
                    "id": "approved_by",
                    "label": "Aprobado por",
                    "type": "position",
                    "required": True,
                    "options": [
                        {"id": "rector", "label": "Rector"},
                        {"id": "dpo", "label": "Oficial de Protección de Datos Personales"},
                        {"id": "jefe-oti", "label": "Jefe de la OTI"},
                    ],
                    "validation": {
                        "exact": "rector",
                        "feedback_error": "El alcance institucional requiere aprobación rectoral.",
                    },
                },
                {
                    "id": "approval_date",
                    "label": "Fecha de aprobación",
                    "type": "date",
                    "required": True,
                    "validation": {
                        "min_date": "2026-01-01",
                        "max_date": "2026-12-31",
                        "sample_solution": "2026-06-01",
                    },
                },
                {
                    "id": "review_date",
                    "label": "Próxima fecha de revisión",
                    "type": "date",
                    "required": True,
                    "validation": {
                        "min_date": "2026-01-02",
                        "max_date": "2027-12-31",
                        "sample_solution": "2027-05-15",
                    },
                },
            ],
        },
        {
            "id": "limites",
            "title": "2. Unidades, sistemas y roles",
            "fields": [
                {
                    "id": "included_units",
                    "label": "Unidades incluidas",
                    "type": "multiselect",
                    "required": True,
                    "options": [
                        {"id": "OBU", "label": "Oficina de Bienestar Universitario"},
                        {"id": "FCSA", "label": "Facultad de Ciencias de la Salud"},
                        {"id": "OTI", "label": "Oficina de Tecnologías de la Información"},
                        {"id": "FIPS", "label": "Facultad de Ingeniería de Producción"},
                        {"id": "ORH", "label": "Oficina de Recursos Humanos"},
                    ],
                    "validation": {
                        "required_ids": ["OBU", "FCSA", "OTI"],
                        "forbidden_ids": ["FIPS", "ORH"],
                        "feedback_error": "Incluye OBU, FCSA y OTI; excluye FIPS y ORH.",
                    },
                },
                {
                    "id": "included_systems",
                    "label": "Sistemas incluidos",
                    "type": "multiselect",
                    "required": True,
                    "options": [
                        {"id": "bienestar", "label": "Sistema de Bienestar y Salud"},
                        {"id": "planillas", "label": "Sistema de Planillas y RR. HH."},
                        {"id": "hc-movil", "label": "Sistema de Historia Clínica Móvil"},
                    ],
                    "validation": {
                        "exact_ids": ["bienestar"],
                        "feedback_error": "Solo corresponde incluir el Sistema de Bienestar y Salud.",
                    },
                },
                {
                    "id": "unsa_role",
                    "label": "Rol de la UNSA",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"id": "responsable", "label": "Responsable del tratamiento (controller)"},
                        {"id": "encargado", "label": "Encargado del tratamiento (processor)"},
                    ],
                    "validation": {"exact": "responsable"},
                },
                {
                    "id": "external_processor",
                    "label": "Encargado externo en frontera",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"id": "lab-externo", "label": "Laboratorio médico externo contratado"},
                        {"id": "ninguno", "label": "Ninguno"},
                    ],
                    "validation": {"exact": "lab-externo"},
                },
            ],
        },
        {
            "id": "exclusiones",
            "title": "3. Exclusiones y eficacia",
            "fields": [
                {
                    "id": "exclusions_justification",
                    "label": "Justificación de exclusiones y control en frontera",
                    "type": "textarea",
                    "required": True,
                    "validation": {
                        "min_words": 15,
                        "rubric": {
                            "min_words": 15,
                            "criteria": [
                                {
                                    "id": "excluidas",
                                    "label": "Identifica facultades o tratamientos excluidos",
                                    "keywords_any": ["facultades", "fips", "anonimizado"],
                                    "feedback_missing": "Indica qué facultades o datos quedan fuera.",
                                },
                                {
                                    "id": "motivo",
                                    "label": "Justifica la exclusión por etapas o anonimización",
                                    "keywords_any": ["etapa", "gradual", "anonimiz"],
                                    "feedback_missing": "Explica por qué quedan fuera en esta etapa.",
                                },
                                {
                                    "id": "frontera",
                                    "label": "Precisa contrato o control con encargado externo",
                                    "keywords_any": ["contrato", "encargo", "confidencialidad"],
                                    "feedback_missing": "Explica el control contractual con el laboratorio.",
                                },
                            ],
                            "forbidden_any": [
                                {
                                    "phrases": ["sin exclusiones", "por costo"],
                                    "feedback": "No puedes omitir exclusiones ni justificarlas por costo.",
                                }
                            ],
                        },
                    },
                },
                {
                    "id": "effectiveness_criteria",
                    "label": "Criterios de eficacia del alcance",
                    "type": "textarea",
                    "required": True,
                    "validation": {
                        "min_words": 10,
                        "rubric": {
                            "min_words": 10,
                            "criteria": [
                                {
                                    "id": "indicador",
                                    "label": "Define un indicador medible",
                                    "keywords_any": [
                                        "cantidad",
                                        "numero",
                                        "porcentaje",
                                        "incidentes",
                                    ],
                                    "feedback_missing": "Incluye un indicador medible.",
                                },
                                {
                                    "id": "alcance",
                                    "label": "Vincula el indicador con límites del alcance",
                                    "keywords_any": ["alcance", "limites", "fuera"],
                                    "feedback_missing": "Vincula la métrica con límites del alcance.",
                                },
                            ],
                        },
                    },
                },
            ],
        },
    ],
    "cross_rules": [
        {
            "id": "rule-date-order",
            "kind": "date_order",
            "label": "Revisión anual posterior a aprobación",
            "fields": ["approval_date", "review_date"],
            "params": {"min_days": 1, "max_days": 365},
            "feedback": "La revisión debe ser posterior a la aprobación y no superar 365 días.",
        },
        {
            "id": "rule-disjoint-approval",
            "kind": "disjoint",
            "label": "Segregación entre responsable y aprobador",
            "fields": ["owner_position", "approved_by"],
            "feedback": "El responsable del documento no puede autoaprobarlo.",
        },
        {
            "id": "rule-unit-sys",
            "kind": "unit_system_coherence",
            "label": "Coherencia entre unidades y sistemas",
            "fields": ["included_units", "included_systems"],
            "params": {
                "system_to_unit": {"bienestar": "OBU", "planillas": "ORH"},
                "required_unit_systems": {"OBU": ["bienestar"]},
                "support_units": ["OTI"],
            },
            "feedback": "Todo sistema incluido debe pertenecer a una unidad dentro del alcance.",
        },
    ],
}

RISK_TABLE_SPEC: dict[str, Any] = {
    "prompt": "Valora la consecuencia y probabilidad de cada escenario UNSA.",
    "scenario": "Metodología UNSA: C y P de 0 a 2, riesgo = C + P, >= 3 no aceptable.",
    "threshold": 3,
    "rows": [
        {
            "id": "r-salud",
            "asset": "Sistema de Bienestar y Salud",
            "asset_owner": "Jefe de Bienestar Universitario",
            "data_categories": ["identificación", "datos de salud"],
            "existing_controls": "Base de datos sin cifrado en disco",
            "threat": "Divulgación de datos de salud",
            "vulnerability": "Base sin cifrar",
            "risk_owner": "Jefe de Bienestar Universitario",
            "sensitive_data": True,
            "expected_consequence": 2,
            "expected_probability": 2,
            "tolerance": 1,
            "explanation": "Datos de salud exigen C=2; sin cifrado P=2 -> riesgo 4.",
        },
        {
            "id": "r-biblio",
            "asset": "Biblioteca Digital",
            "asset_owner": "Director de la Biblioteca Central",
            "data_categories": ["identificación", "historial de préstamos"],
            "existing_controls": "Acceso autenticado y respaldos",
            "threat": "Exposición del historial de préstamos",
            "vulnerability": "Registros visibles al personal",
            "risk_owner": "Director de la Biblioteca Central",
            "sensitive_data": False,
            "expected_consequence": 0,
            "expected_probability": 1,
            "tolerance": 1,
            "explanation": "Impacto bajo sobre titulares; riesgo esperado <= 2 (aceptable).",
        },
    ],
}

TREATMENT_TABLE_SPEC: dict[str, Any] = {
    "prompt": "Define el tratamiento y calcula el riesgo residual.",
    "scenario": "Riesgos no aceptables de la UNSA.",
    "options": [
        {"id": "controls", "label": "Aplicar controles"},
        {"id": "transfer", "label": "Transferir"},
        {"id": "avoid", "label": "Evitar"},
        {"id": "accept", "label": "Aceptar"},
    ],
    "soa_controls": [
        {"id": "ctrl-cifrado", "label": "Control de acceso y cifrado", "soa_applies": True},
        {"id": "ctrl-encargo", "label": "Tratar solo bajo instrucciones", "soa_applies": False},
    ],
    "owners": [
        {"id": "jefe-oti", "label": "Jefe de la OTI"},
        {"id": "jefe-bib", "label": "Director de la Biblioteca"},
    ],
    "rows": [
        {
            "id": "t1",
            "asset": "Sistema de Bienestar y Salud",
            "threat": "Divulgación de datos de salud",
            "vulnerability": "Base sin cifrar",
            "initial_consequence": 2,
            "initial_probability": 2,
            "initial_risk": 4,
            "risk_owner": "Jefe de Bienestar Universitario",
            "valid_options": ["controls"],
            "allow_accept": False,
            "valid_controls": ["ctrl-cifrado"],
            "valid_owners": ["jefe-oti"],
            "min_deadline": "2026-06-01",
            "max_deadline": "2026-12-31",
            "expected_option": "controls",
            "expected_control": "ctrl-cifrado",
            "expected_owner": "jefe-oti",
            "expected_deadline": "2026-08-31",
            "expected_residual_c": 2,
            "expected_residual_p": 0,
            "explanation": "El cifrado reduce la probabilidad a 0 manteniendo C=2 (residual 2).",
        }
    ],
}

AUDIT_CHECKLIST_SPEC: dict[str, Any] = {
    "prompt": "Verifica la lista de apoyo de auditoría.",
    "scenario": "Auditoría interna de cumplimiento PIMS.",
    "verdicts": [
        {"id": "conforme", "label": "Conforme"},
        {"id": "observacion", "label": "Observación"},
        {"id": "no_conformidad", "label": "No conformidad"},
    ],
    "items": [
        {
            "id": "pims-soa",
            "clause_ref": "6.1.3 e",
            "requirement_title": "Declaración de aplicabilidad (SoA)",
            "observed_context": "Existe «Declaración de aplicabilidad (SoA)», pero está en borrador.",
            "questions": [
                {
                    "id": "q-ok",
                    "label": "¿Está aprobada la SoA con justificaciones y aceptación residual?",
                },
                {"id": "q-bad", "label": "¿Se firmaron los contratos de limpieza física?"},
            ],
            "evidences": [
                {
                    "id": "e-ok",
                    "label": "SoA aprobada con controles, justificación y riesgos residuales",
                },
                {"id": "e-bad", "label": "Lista de asistencia a charla general"},
            ],
            "expected_question": "q-ok",
            "expected_evidence": "e-ok",
            "expected_verdict": "no_conformidad",
            "explanation": "Un documento obligatorio en borrador genera no conformidad.",
        }
    ],
}

NONCONFORMITY_SPEC: dict[str, Any] = {
    "prompt": "Completa el formulario de medida correctiva.",
    "scenario": "Hallazgo NC-02: cuenta de exdocente seguía activa.",
    "documents": [
        {"id": "pims-programa", "label": "Programa de seguridad"},
        {"id": "pims-politica", "label": "Política de privacidad"},
    ],
    "positions": [
        {"id": "jefe-oti", "label": "Jefe de la OTI"},
        {"id": "rector", "label": "Rector"},
    ],
    "cases": [
        {
            "id": "nc-02",
            "title": "NC-02 Cuenta de exdocente activa",
            "detection_context": "Detectado en revisión trimestral de accesos.",
            "detection_date": "2026-05-01",
            "correction_options": [
                {"id": "corr-ok", "label": "Desactivar de inmediato la cuenta activa"},
                {"id": "corr-bad", "label": "Rediseñar el flujo de bajas entre ORH y OTI"},
            ],
            "root_cause_options": [
                {"id": "rc-ok", "label": "No existe aviso formal de bajas de RR. HH. a TI"},
                {"id": "rc-bad", "label": "Un exdocente tenía usuario activo en el sistema"},
            ],
            "action_options": [
                {"id": "act-ok", "label": "Implantar procedimiento de baja ORH → TI en 24 h"},
                {"id": "act-bad", "label": "Desactivar esa única cuenta sin cambiar el proceso"},
            ],
            "verification_options": [
                {
                    "id": "ver-ok",
                    "label": "Muestreo de bajas de los últimos 60 días sin cuentas activas",
                },
                {"id": "ver-bad", "label": "Confirmación verbal de que se cerró la cuenta"},
            ],
            "expected_correction": "corr-ok",
            "expected_root_cause": "rc-ok",
            "expected_requires_action": True,
            "expected_action": "act-ok",
            "expected_responsible": "jefe-oti",
            "min_verification_lag_days": 30,
            "max_implementation_date": "2026-05-30",
            "expected_verification": "ver-ok",
            "expected_doc_change": True,
            "expected_document": "pims-programa",
            "explanation": "Corrección = desactivar ya; acción = flujo ORH→TI; verificar >= 30 días.",
        }
    ],
}

COMPETENCE_SPEC: dict[str, Any] = {
    "prompt": "Completa la matriz de competencias del PIMS.",
    "scenario": "Asegurar competencia e independencia en la UNSA.",
    "competencies": [
        {"id": "comp-aud", "label": "Auditoría interna ISO 19011 y privacidad"},
        {"id": "comp-bas", "label": "Sensibilización general en privacidad"},
    ],
    "trainings": [
        {"id": "r4", "label": "Ruta 4 — Auditor interno"},
        {"id": "r1", "label": "Ruta 1 — Sensibilización"},
    ],
    "evidences": [
        {"id": "ev-ok", "label": "Evaluación práctica aprobada (>= 70 %) y registro"},
        {"id": "ev-asist", "label": "Solo lista de asistencia a charla informativa"},
    ],
    "evaluators": [
        {"id": "oci", "label": "Jefe del OCI / Comité independiente"},
        {"id": "auditor", "label": "El propio auditor evaluado"},
    ],
    "rows": [
        {
            "id": "row-aud",
            "position_title": "Auditores internos",
            "role_summary": "Auditan cumplimiento e imparcialidad del PIMS",
            "expected_competency": "comp-aud",
            "expected_training": "r4",
            "expected_evidence": "ev-ok",
            "valid_evaluators": ["oci"],
            "forbidden_evaluators": ["auditor"],
            "expected_evaluator": "oci",
            "explanation": "Un auditor requiere Ruta 4, evaluación de eficacia y evaluación independiente.",
        }
    ],
}

NEW_SPECS: dict[ExerciseKind, dict[str, Any]] = {
    ExerciseKind.DOCUMENT_FORM: DOCUMENT_FORM_ALCANCE,
    ExerciseKind.RISK_TABLE: RISK_TABLE_SPEC,
    ExerciseKind.TREATMENT_TABLE: TREATMENT_TABLE_SPEC,
    ExerciseKind.AUDIT_CHECKLIST: AUDIT_CHECKLIST_SPEC,
    ExerciseKind.NONCONFORMITY_FORM: NONCONFORMITY_SPEC,
    ExerciseKind.COMPETENCE_MATRIX: COMPETENCE_SPEC,
}


def _flatten_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            keys.add(k)
            keys |= _flatten_keys(v)
    elif isinstance(value, list):
        for item in value:
            keys |= _flatten_keys(item)
    return keys


# ----------------------------------------------------------------------------- AC-009-1


@pytest.mark.ac("AC-009-1")
def test_inventario_cubre_las_16_plantillas_sin_anexo_a_literal() -> None:
    inv = (ROOT / "docs" / "practica-documental" / "inventario-plantillas.md").read_text(
        encoding="utf-8"
    )
    expected_files = [
        "Documento_sobre_el_alcance_del_SGSI_ES.docx",
        "Politica_de_seguridad_de_la_informacion_ES.docx",
        "Metodologia_de_evaluacion_y_tratamiento_de_riesgos_ES.docx",
        "Apendice_1_Cuadro_de_evaluacion_de_riesgos_ES.xlsx",
        "Declaracion_de_aplicabilidad_ES.docx",
        "Plan_de_tratamiento_del_riesgo_ES.docx",
        "Apendice_2_Cuadro_de_tratamiento_de_riesgos_ES.xlsx",
        "Apendice_3_Informe_sobre_evaluacion_y_tratamiento_ES.docx",
        "Plan_de_capacitacion_y_concienciacion_ES.docx",
        "Minutas_de_Revision_por_parte_de_la_direccion_ES.docx",
        "Procedimiento_para_medidas_correctivas_ES.docx",
        "Apendice_Formulario_para_medidas_correctivas_ES.docx",
        "Procedimiento_para_auditoria_interna_ES.docx",
        "Apendice_1_Programa_anual_de_auditoria_interna_ES.docx",
        "Apendice_2_Informe_de_auditoria_interna_ES.docx",
        "Apendice_3_Lista_de_apoyo_auditoria_interna_ES.docx",
    ]
    for name in expected_files:
        assert name in inv, f"falta plantilla en inventario: {name}"
    assert not re.findall(r"A\.\d+\.\d+", inv), "no debe reproducir IDs literales del Anexo A"


# ----------------------------------------------------------------------------- AC-009-2 / AC-009-12


@pytest.mark.ac("AC-009-2")
@pytest.mark.ac("AC-009-12")
@pytest.mark.parametrize("kind", list(NEW_SPECS))
def test_nuevos_tipos_validan_ocultan_soluciones_y_resuelven_100(kind: ExerciseKind) -> None:
    spec = NEW_SPECS[kind]
    validate_spec(kind, spec)

    public = to_public(kind, spec, seed="semilla-1")
    forbidden = {
        "validation",
        "cross_rules",
        "rubric",
        "keywords_any",
        "keyword_groups",
        "forbidden_any",
        "expected_consequence",
        "expected_probability",
        "expected_option",
        "expected_control",
        "expected_question",
        "expected_evidence",
        "expected_verdict",
        "expected_correction",
        "expected_root_cause",
        "expected_action",
        "expected_competency",
        "expected_training",
        "sensitive_data",
        "soa_applies",
        "allow_accept",
        "valid_options",
        "valid_controls",
        "valid_evaluators",
        "forbidden_evaluators",
        "explanation",
        "sample_solution",
    }
    leaked = _flatten_keys(public) & forbidden
    assert not leaked, f"{kind}: claves privadas filtradas: {leaked}"

    perfect = grade(kind, spec, solve(kind, spec))
    assert perfect.score == 100
    assert all(i.correct for i in perfect.items)

    empty = grade(kind, spec, wrong(kind))
    assert empty.score == 0


@pytest.mark.ac("AC-009-2")
@pytest.mark.parametrize(
    ("kind", "broken"),
    [
        (ExerciseKind.DOCUMENT_FORM, {**DOCUMENT_FORM_ALCANCE, "sections": []}),
        (ExerciseKind.RISK_TABLE, {**RISK_TABLE_SPEC, "rows": []}),
        (ExerciseKind.TREATMENT_TABLE, {**TREATMENT_TABLE_SPEC, "options": []}),
        (ExerciseKind.AUDIT_CHECKLIST, {**AUDIT_CHECKLIST_SPEC, "items": []}),
        (ExerciseKind.NONCONFORMITY_FORM, {**NONCONFORMITY_SPEC, "cases": []}),
        (ExerciseKind.COMPETENCE_MATRIX, {**COMPETENCE_SPEC, "competencies": []}),
    ],
)
def test_validate_spec_rechaza_specs_rotas(kind: ExerciseKind, broken: dict[str, Any]) -> None:
    with pytest.raises(InvalidExerciseSpec):
        validate_spec(kind, broken)


# ----------------------------------------------------------------------------- AC-009-3 document_form


@pytest.mark.ac("AC-009-3")
def test_document_form_alcance_detecta_errores_tipicos_y_reglas_cruzadas() -> None:
    perfect = solve(ExerciseKind.DOCUMENT_FORM, DOCUMENT_FORM_ALCANCE)
    assert grade(ExerciseKind.DOCUMENT_FORM, DOCUMENT_FORM_ALCANCE, perfect).score == 100

    # Caso con errores tipicos: fecha revision <= aprobacion, autoaprobacion, sistema ORH sin unidad, texto pobre
    bad_fields = dict(perfect["fields"])
    bad_fields["approved_by"] = "dpo"
    bad_fields["owner_position"] = "dpo"
    bad_fields["review_date"] = "2026-05-01"
    bad_fields["included_systems"] = ["bienestar", "planillas"]
    bad_fields["exclusions_justification"] = "Sin exclusiones porque es muy caro incluir todo hoy."
    res = grade(ExerciseKind.DOCUMENT_FORM, DOCUMENT_FORM_ALCANCE, {"fields": bad_fields})
    assert res.score < 70
    by_id = {i.id: i for i in res.items}
    assert not by_id["rule-date-order"].correct
    assert not by_id["rule-disjoint-approval"].correct
    assert not by_id["rule-unit-sys"].correct
    assert not by_id["exclusions_justification"].correct
    assert "costo" in by_id["exclusions_justification"].feedback.lower()


@pytest.mark.ac("AC-009-3")
def test_document_form_reglas_requires_if_y_count_matches() -> None:
    spec: dict[str, Any] = {
        "prompt": "Informe",
        "scenario": "Informe de auditoría.",
        "document_title": "Informe",
        "sections": [
            {
                "id": "s1",
                "title": "Resultados",
                "fields": [
                    {
                        "id": "has_nc",
                        "label": "¿Hay NC?",
                        "type": "select",
                        "options": [{"id": "si", "label": "Sí"}, {"id": "no", "label": "No"}],
                        "validation": {"exact": "si"},
                    },
                    {
                        "id": "nc_total",
                        "label": "Total NC",
                        "type": "text",
                        "validation": {"pattern": r"^\d+$", "sample_solution": "2"},
                    },
                    {
                        "id": "nc_list",
                        "label": "Detalle NC",
                        "type": "textarea",
                        "validation": {
                            "rubric": {
                                "min_words": 2,
                                "criteria": [
                                    {
                                        "id": "c1",
                                        "label": "Lista hallazgos",
                                        "keywords_any": ["nc"],
                                        "feedback_missing": "Detalla las NC.",
                                    }
                                ],
                            },
                            "sample_solution": "NC-01 falta política\nNC-02 SoA borrador",
                        },
                    },
                ],
            }
        ],
        "cross_rules": [
            {
                "id": "r-req",
                "kind": "requires_if",
                "label": "Si hay NC, total no puede ser 0",
                "fields": ["has_nc", "nc_total"],
                "params": {"when_in": ["si"], "forbid_any": ["0"]},
                "feedback": "Con NC declaradas el total no puede ser 0.",
            },
            {
                "id": "r-cnt",
                "kind": "count_matches",
                "label": "Conteo igual a líneas",
                "fields": ["nc_total", "nc_list"],
                "feedback": "El total numérico debe coincidir con el detalle.",
            },
        ],
    }
    validate_spec(ExerciseKind.DOCUMENT_FORM, spec)
    good = solve(ExerciseKind.DOCUMENT_FORM, spec)
    assert grade(ExerciseKind.DOCUMENT_FORM, spec, good).score == 100

    mismatch = {"fields": {"has_nc": "si", "nc_total": "0", "nc_list": "NC-01 borrador"}}
    res = grade(ExerciseKind.DOCUMENT_FORM, spec, mismatch)
    by_id = {i.id: i for i in res.items}
    assert not by_id["r-req"].correct and not by_id["r-cnt"].correct


@pytest.mark.ac("AC-009-3")
def test_document_form_respuestas_invalidas_lanzan_422() -> None:
    for bad in (
        {},
        {"fields": "x"},
        {"fields": {"included_units": "OBU"}},
        {"fields": {"doc_code": 1}},
    ):
        with pytest.raises(InvalidAnswer):
            grade(ExerciseKind.DOCUMENT_FORM, DOCUMENT_FORM_ALCANCE, bad)


# ----------------------------------------------------------------------------- AC-009-4 risk_table


@pytest.mark.ac("AC-009-4")
def test_risk_table_exige_datos_sensibles_y_no_permite_cruzar_umbral() -> None:
    # Tolerancia 1: si datos sensibles tiene C=1, P=2 -> riesgo 3 (mismo lado del umbral),
    # PERO viola la regla de consecuencia=2 en datos sensibles!
    # Y en r-biblio, C=1, P=2 -> riesgo 3 (cruza umbral >= 3 aunque distancia sea 2 vs 1)!
    ans = {
        "rows": {
            "r-salud": {"consequence": 1, "probability": 2},
            "r-biblio": {"consequence": 1, "probability": 2},
        }
    }
    res = grade(ExerciseKind.RISK_TABLE, RISK_TABLE_SPEC, ans)
    assert res.score == 0
    assert "sensibles" in res.items[0].feedback.lower()
    assert "umbral" in res.items[1].feedback.lower()

    # Con tolerancia 1 dentro del mismo lado del umbral y C=2 en sensibles si aprueba
    within_tol = {
        "rows": {
            "r-salud": {"consequence": 2, "probability": 1},  # riesgo 3 vs 4 (ambos >= 3)
            "r-biblio": {"consequence": 1, "probability": 1},  # riesgo 2 vs 1 (ambos <= 2)
        }
    }
    assert grade(ExerciseKind.RISK_TABLE, RISK_TABLE_SPEC, within_tol).score == 100

    with pytest.raises(InvalidAnswer):
        grade(
            ExerciseKind.RISK_TABLE,
            RISK_TABLE_SPEC,
            {"rows": {"r-salud": {"consequence": 5, "probability": 1}}},
        )


# ----------------------------------------------------------------------------- AC-009-5 treatment_table


@pytest.mark.ac("AC-009-5")
def test_treatment_table_valida_soa_y_coherencia_residual() -> None:
    # Elige control marcado soa_applies=False y sube o no baja bien el residual
    bad = {
        "rows": {
            "t1": {
                "option": "controls",
                "control_id": "ctrl-encargo",  # soa_applies = False
                "owner": "jefe-oti",
                "deadline": "2026-08-31",
                "residual_consequence": 2,
                "residual_probability": 0,
            }
        }
    }
    res = grade(ExerciseKind.TREATMENT_TABLE, TREATMENT_TABLE_SPEC, bad)
    assert res.score == 80  # 4 de 5 dimensiones correctas
    assert not res.items[0].correct
    assert "No aplica" in res.items[0].feedback

    # Aceptar prohibido + pretende reducir residual
    bad_accept = {
        "rows": {
            "t1": {
                "option": "accept",
                "control_id": "",
                "owner": "jefe-oti",
                "deadline": "2026-08-31",
                "residual_consequence": 1,
                "residual_probability": 0,
            }
        }
    }
    res2 = grade(ExerciseKind.TREATMENT_TABLE, TREATMENT_TABLE_SPEC, bad_accept)
    assert res2.score < 70


# ----------------------------------------------------------------------------- AC-009-7 / AC-009-8


@pytest.mark.ac("AC-009-7")
def test_nonconformity_form_exige_desfase_y_separa_correccion_de_accion() -> None:
    perfect = solve(ExerciseKind.NONCONFORMITY_FORM, NONCONFORMITY_SPEC)
    mixed = {"cases": {"nc-02": dict(perfect["cases"]["nc-02"])}}
    mixed["cases"]["nc-02"]["action"] = "act-bad"
    mixed["cases"]["nc-02"]["verification_date"] = mixed["cases"]["nc-02"]["implementation_date"]
    res = grade(ExerciseKind.NONCONFORMITY_FORM, NONCONFORMITY_SPEC, mixed)
    assert res.score == 75
    assert not res.items[0].correct
    assert "al menos 30 días" in res.items[0].feedback


@pytest.mark.ac("AC-009-8")
def test_competence_matrix_rechaza_asistencia_y_autoevaluacion() -> None:
    bad = {
        "rows": {
            "row-aud": {
                "competency_id": "comp-aud",
                "training_id": "r4",
                "evidence_id": "ev-asist",
                "evaluator_id": "auditor",
            }
        }
    }
    res = grade(ExerciseKind.COMPETENCE_MATRIX, COMPETENCE_SPEC, bad)
    assert res.score == 50  # 2 de 4 criterios
    assert "asistencia" in res.items[0].feedback
    assert "Conflicto de interés" in res.items[0].feedback
