import argparse
import asyncio

from unsa_audit.core.config import get_settings
from unsa_audit.seed.loader import seed_all, seed_demo_cohort


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m unsa_audit.seed",
        description="Carga la BD ficticia de la UNSA, el contenido de las rutas, los documentos "
        "institucionales y la cuenta superadmin.",
    )
    parser.add_argument(
        "--reset-documents",
        action="store_true",
        help="borra documentos, versiones y solicitudes de cambio y los recarga desde content/ "
        "(por defecto se conserva lo creado desde la aplicacion)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="ademas crea 12 participantes demo (@demo.unsa.example, contraseña Demo-1234) "
        "con avances variados; es idempotente",
    )
    parser.add_argument(
        "--reset-demo",
        action="store_true",
        help="elimina las cuentas @demo.unsa.example y @e2e.unsa.example con su progreso "
        "y recrea el cohorte demo",
    )
    args = parser.parse_args()
    settings = get_settings()
    asyncio.run(seed_all(settings, reset_documents=args.reset_documents))
    print("Seed cargado: universidad ficticia, rutas, documentos y cuenta superadmin.")
    if args.demo or args.reset_demo:
        result = asyncio.run(seed_demo_cohort(settings, reset=args.reset_demo))
        print(
            f"Demo: {result.created} participantes creados, {result.skipped} ya existian, "
            f"{result.removed} eliminados."
        )


if __name__ == "__main__":
    main()
