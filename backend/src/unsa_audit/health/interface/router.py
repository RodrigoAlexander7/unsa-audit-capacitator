from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from unsa_audit.health.application.check_health import CheckHealth

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    database: str


@router.get("/health", response_model=HealthResponse)
async def health(request: Request, response: Response) -> HealthResponse:
    use_case: CheckHealth = request.app.state.check_health
    report = await use_case.execute()
    if not report.database_up:
        response.status_code = 503
    return HealthResponse(
        status=report.status,
        database="up" if report.database_up else "down",
    )
