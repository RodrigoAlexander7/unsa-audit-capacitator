"""Carga idempotente del dataset ficticio y de la cuenta superadmin."""

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.core.config import Settings
from unsa_audit.core.database import create_engine, create_session_factory
from unsa_audit.identity.application.use_cases import EnsureSuperadmin
from unsa_audit.identity.infrastructure.security import Argon2PasswordHasher
from unsa_audit.identity.infrastructure.sqlalchemy_user_repository import SqlAlchemyUserRepository
from unsa_audit.learning.application.use_cases import SyncContent
from unsa_audit.learning.infrastructure.content_loader import FileContentSource
from unsa_audit.learning.infrastructure.sqlalchemy_repository import SqlAlchemyLearningRepository
from unsa_audit.seed.university_data import UniversityDataset, build_university_dataset
from unsa_audit.university.infrastructure.models import (
    DataOwnerModel,
    OrgUnitModel,
    PersonModel,
    PositionModel,
    ProcessingActivityModel,
    SystemModel,
)


async def load_university(
    session_factory: async_sessionmaker[AsyncSession], dataset: UniversityDataset | None = None
) -> UniversityDataset:
    """Reemplaza el contenido de las tablas university por el dataset ficticio."""
    ds = dataset or build_university_dataset()
    async with session_factory() as session, session.begin():
        for model in (
            DataOwnerModel,
            ProcessingActivityModel,
            SystemModel,
            PersonModel,
            PositionModel,
            OrgUnitModel,
        ):
            await session.execute(delete(model))

        session.add_all(
            OrgUnitModel(
                id=u.id, parent_id=u.parent_id, kind=u.kind.value, name=u.name, code=u.code
            )
            for u in ds.org_units
        )
        await session.flush()
        session.add_all(
            PositionModel(
                id=p.id,
                org_unit_id=p.org_unit_id,
                title=p.title,
                reports_to_position_id=p.reports_to_position_id,
            )
            for p in ds.positions
        )
        await session.flush()
        session.add_all(
            PersonModel(
                id=p.id, full_name=p.full_name, kind=p.kind.value, position_id=p.position_id
            )
            for p in ds.people
        )
        session.add_all(
            SystemModel(
                id=s.id,
                name=s.name,
                description=s.description,
                owner_org_unit_id=s.owner_org_unit_id,
                data_categories=list(s.data_categories),
            )
            for s in ds.systems
        )
        await session.flush()
        session.add_all(
            DataOwnerModel(system_id=o.system_id, person_id=o.person_id, role=o.role.value)
            for o in ds.data_owners
        )
        session.add_all(
            ProcessingActivityModel(
                id=a.id,
                org_unit_id=a.org_unit_id,
                name=a.name,
                purpose=a.purpose,
                legal_basis=a.legal_basis,
                data_categories=list(a.data_categories),
                retention=a.retention,
            )
            for a in ds.processing_activities
        )
    return ds


async def sync_content(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings
) -> tuple[int, int]:
    """Sincroniza `content/routes` a la BD (rutas y modulos). Idempotente."""
    use_case = SyncContent(
        SqlAlchemyLearningRepository(session_factory), FileContentSource(settings.content_dir)
    )
    return await use_case.execute()


async def ensure_superadmin(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    if not settings.superadmin_password:
        raise RuntimeError("Define SUPERADMIN_PASSWORD en .env para crear la cuenta superadmin.")
    use_case = EnsureSuperadmin(
        SqlAlchemyUserRepository(session_factory),
        Argon2PasswordHasher(),
        settings.superadmin_email,
        settings.superadmin_password,
    )
    await use_case.execute()


async def seed_all(settings: Settings) -> None:
    engine = create_engine(settings.database_url)
    try:
        session_factory = create_session_factory(engine)
        await load_university(session_factory)
        await sync_content(session_factory, settings)
        await ensure_superadmin(session_factory, settings)
    finally:
        await engine.dispose()
