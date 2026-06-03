from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from models.checkout import CheckoutResponse, UpdateObsRequest
from services.checkouts import Checkouts

router = APIRouter(prefix="/checkouts", tags=["checkouts"])


@router.get("/today", response_model=list[CheckoutResponse])
def get_today_checkouts(db: Session = Depends(get_db)):
    return Checkouts.getTodayCheckouts(db)


@router.get("/processed", response_model=list[CheckoutResponse])
def get_processed_checkouts(db: Session = Depends(get_db)):
    return Checkouts.getProcessedCheckouts(db)


@router.patch("/{id}/observations", response_model=dict)
def update_observations(id: int, body: UpdateObsRequest, db: Session = Depends(get_db)):
    updated = Checkouts.updateCheckoutObservations(id, body.obs, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Checkout não encontrado")
    return {"message": "Observações atualizadas"}


@router.patch("/{id}/process", response_model=dict)
def process_checkout(id: int, db: Session = Depends(get_db)):
    updated = Checkouts.processCheckout(id, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Checkout não encontrado")
    return {"message": "Checkout processado"}
