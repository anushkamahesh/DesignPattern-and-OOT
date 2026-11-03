from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.application.overview.dto import LocationOverviewDto
from src.application.overview.facade import LocationOverviewFacade, create_overview_facade
from src.domain.locations.errors import LocationNotFoundError
from src.infrastructure.persistence.session import get_db

router = APIRouter(prefix="/api", tags=["Overview"])


def get_facade(db: Session = Depends(get_db)) -> LocationOverviewFacade:
    return create_overview_facade(db)


@router.get(
    "/locations/{location_id}/overview",
    response_model=LocationOverviewDto,
    summary="One-call dashboard snapshot of a location",
)
def get_overview(location_id: UUID, facade: LocationOverviewFacade = Depends(get_facade)):
    try:
        return facade.get_overview(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc