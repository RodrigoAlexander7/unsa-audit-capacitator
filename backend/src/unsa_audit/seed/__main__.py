import asyncio

from unsa_audit.core.config import get_settings
from unsa_audit.seed.loader import seed_all


def main() -> None:
    settings = get_settings()
    asyncio.run(seed_all(settings))
    print("Seed ficticio de la UNSA cargado y cuenta superadmin asegurada.")


if __name__ == "__main__":
    main()
