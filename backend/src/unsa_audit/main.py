"""Composition root: unico lugar donde se conectan puertos con adaptadores."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from unsa_audit.core.config import Settings, get_settings
from unsa_audit.core.database import create_engine, create_session_factory
from unsa_audit.documents.application.use_cases import (
    GetChangeRequest,
    GetDiff,
    GetDocument,
    GetVersion,
    ListChangeRequests,
    ListDocuments,
    ListVersions,
    ProposeChange,
    ResolveChangeRequest,
)
from unsa_audit.documents.infrastructure.sqlalchemy_repository import SqlAlchemyDocumentRepository
from unsa_audit.documents.interface.router import router as documents_router
from unsa_audit.health.application.check_health import CheckHealth, DatabaseProbe
from unsa_audit.health.infrastructure.sqlalchemy_probe import SqlAlchemyDatabaseProbe
from unsa_audit.health.interface.router import router as health_router
from unsa_audit.identity.application.use_cases import GetCurrentUser, Login, RegisterUser
from unsa_audit.identity.infrastructure.security import Argon2PasswordHasher, JwtTokenService
from unsa_audit.identity.infrastructure.sqlalchemy_user_repository import SqlAlchemyUserRepository
from unsa_audit.identity.interface.router import router as identity_router
from unsa_audit.learning.application.use_cases import (
    CompleteReadingModule,
    EnrollInRoute,
    GetModule,
    GetRoute,
    ListRoutes,
    SubmitAttempt,
)
from unsa_audit.learning.infrastructure.sqlalchemy_repository import SqlAlchemyLearningRepository
from unsa_audit.learning.infrastructure.sqlalchemy_university_facts import (
    SqlAlchemyUniversityFacts,
)
from unsa_audit.learning.interface.router import router as learning_router
from unsa_audit.university.application.use_cases import GetOrgTree, GetOrgUnitDetail, ListSystems
from unsa_audit.university.infrastructure.sqlalchemy_repository import (
    SqlAlchemyUniversityReadRepository,
)
from unsa_audit.university.interface.router import router as university_router


def create_app(
    settings: Settings | None = None,
    probe: DatabaseProbe | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    users = SqlAlchemyUserRepository(session_factory)
    hasher = Argon2PasswordHasher()
    tokens = JwtTokenService(settings.jwt_secret, settings.jwt_expire_minutes)
    university = SqlAlchemyUniversityReadRepository(session_factory)
    learning = SqlAlchemyLearningRepository(session_factory)
    university_facts = SqlAlchemyUniversityFacts(session_factory)
    documents = SqlAlchemyDocumentRepository(session_factory)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await engine.dispose()

    app = FastAPI(title="UNSA Audit Capacitator (POC)", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    app.state.check_health = CheckHealth(probe or SqlAlchemyDatabaseProbe(engine))
    app.state.register_user = RegisterUser(users, hasher, settings.superadmin_email)
    app.state.login = Login(users, hasher, tokens)
    app.state.get_current_user = GetCurrentUser(users, tokens)
    app.state.get_org_tree = GetOrgTree(university)
    app.state.get_org_unit_detail = GetOrgUnitDetail(university)
    app.state.list_systems = ListSystems(university)
    app.state.list_routes = ListRoutes(learning)
    app.state.get_route = GetRoute(learning)
    app.state.enroll_in_route = EnrollInRoute(learning)
    app.state.get_module = GetModule(learning, university_facts)
    app.state.submit_attempt = SubmitAttempt(learning, university_facts)
    app.state.complete_reading = CompleteReadingModule(learning)
    app.state.list_documents = ListDocuments(documents)
    app.state.get_document = GetDocument(documents)
    app.state.list_versions = ListVersions(documents)
    app.state.get_version = GetVersion(documents)
    app.state.get_diff = GetDiff(documents)
    app.state.propose_change = ProposeChange(documents)
    app.state.list_change_requests = ListChangeRequests(documents)
    app.state.get_change_request = GetChangeRequest(documents)
    app.state.resolve_change_request = ResolveChangeRequest(documents)

    app.include_router(health_router)
    app.include_router(identity_router)
    app.include_router(university_router)
    app.include_router(learning_router)
    app.include_router(documents_router)
    return app


def run() -> None:
    uvicorn.run("unsa_audit.main:app", host="0.0.0.0", port=8000, reload=False)


def __getattr__(name: str) -> FastAPI:
    # `uvicorn unsa_audit.main:app` crea la app de forma perezosa.
    if name == "app":
        return create_app()
    raise AttributeError(name)
