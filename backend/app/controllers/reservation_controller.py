from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config.db import get_db
from services.crawling_service import crawl_facility_reservations
from schemas.reservation_schema import ReservationResponse
from models.reservation_model import Reservation
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from config.db import get_db
from models.reservation_model import Reservation
# from schemas.reservation_schema import ReservationResponse
from typing import List, Optional
from schemas.reservation_schema import ReservationResponse

router = APIRouter()

@router.post("/crawl/{facility_name}")
def crawl_facility(facility_name: str, db: Session = Depends(get_db)):
    """
    Trigger crawling for the specified facility and format the response.
    """
    result = crawl_facility_reservations(db, facility_name)

    if result.get("status") == "error":
        return {
            "success": False,
            "error": result.get("reason")
        }

    return {
        "success": True,
        "message": f"Crawling completed for {facility_name}",
        "saved_count": result.get("saved_count", 0)
    }

@router.get("/reservations")
def get_reservations(facility_name: str = None, date: str = None, db: Session = Depends(get_db)):
    """
    Get all reservations, optionally filtered by facility name and date.
    """
    try:
        query = db.query(Reservation)

        if facility_name:
            query = query.filter(Reservation.facility_name == facility_name)
        if date:
            query = query.filter(Reservation.date == date)

        reservations = query.all()

        return {
            "success": True,
            "count": len(reservations),
            "data": reservations
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
