import argparse
import asyncio

from unsa_audit.core.config import get_settings
from unsa_audit.seed.loader import seed_all


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
    args = parser.parse_args()
    asyncio.run(seed_all(get_settings(), reset_documents=args.reset_documents))
    print("Seed cargado: universidad ficticia, rutas, documentos y cuenta superadmin.")


if __name__ == "__main__":
    main()
