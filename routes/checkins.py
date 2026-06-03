from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from models.checkin import CheckinResponse, UpdateObsRequest
from services.checkins import Checkins

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.get("/pending", response_model=list[CheckinResponse])
def get_pending_checkins(db: Session = Depends(get_db)):
    return Checkins.getPendingCheckins(db)


@router.get("/processed", response_model=list[CheckinResponse])
def get_processed_checkins(db: Session = Depends(get_db)):
    return Checkins.getProcessedCheckins(db)


@router.patch("/{id}/observations", response_model=dict)
def update_observations(id: int, body: UpdateObsRequest, db: Session = Depends(get_db)):
    updated = Checkins.updateObservations(id, body.obs, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Checkin não encontrado")
    return {"message": "Observações atualizadas"}


@router.patch("/{id}/process", response_model=dict)
def process_checkin(id: int, db: Session = Depends(get_db)):
    updated = Checkins.processCheckin(id, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Checkin não encontrado")
    return {"message": "Checkin processado"}
