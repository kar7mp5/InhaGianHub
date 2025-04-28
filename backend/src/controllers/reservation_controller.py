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
from models.popup_detail_model import PopupDetail
from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends, BackgroundTasks

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

from datetime import datetime
import re
from datetime import datetime

@router.get("/reservations/{reservation_id}/details")
def get_popup_details(reservation_id: int, db: Session = Depends(get_db)):
    """
    Retrieve popup details linked to a specific reservation.
    """
    details = db.query(PopupDetail).filter_by(reservation_id=reservation_id).all()

    if not details:
        return {
            "status": "not_found",
            "message": f"No popup details found for reservation ID {reservation_id}",
            "data": []  # Empty data list if no details found
        }

    formatted_data = []
    for d in details:
        if d.key == "일시":  # "일시" contains both date and time
            try:
                # Use regular expressions to extract date and time ranges
                match = re.match(r"(\d{8}) ~ (\d{8}) (\d{2}:\d{2}) ~ (\d{2}:\d{2})", d.value)
                if match:
                    start_date = match.group(1)
                    end_date = match.group(2)
                    start_time = match.group(3)
                    end_time = match.group(4)

                    # Add start_time and end_time to the formatted data
                    formatted_data.append({
                        "key": "start_time",
                        "value": format_time(start_time)  # Ensure time is in HH:MM format
                    })
                    formatted_data.append({
                        "key": "end_time",
                        "value": format_time(end_time)  # Ensure time is in HH:MM format
                    })
                else:
                    print(f"[WARN] Invalid date-time format for {d.value}")
                    continue  # Skip this record if the format doesn't match
            except Exception as e:
                print(f"[ERROR] Error processing {d.key}: {d.value} - Error: {e}")
                continue  # Skip this record if there's an issue

        else:
            formatted_data.append({
                "key": d.key,
                "value": d.value
            })

    return {
        "status": "ok",
        "reservation_id": reservation_id,
        "data": formatted_data
    }

# Helper function to format time
def format_time(time_str: str) -> str:
    """
    Converts a time string (HH:MM) to the desired format for frontend (HH:MM).
    
    Args:
        time_str (str): Time string in "HH:MM" format.

    Returns:
        str: Formatted time string.
    """
    try:
        # Ensure that the time is in the correct "HH:MM" format
        time_obj = datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime("%H:%M")
    except ValueError:
        # If time format is incorrect, return the original string
        return time_str  # Return the original value if format is invalid

# start/end_time 추출 함수 예시
def parse_start_time(link: str):
    # 실제 팝업 내용을 기반으로 시간 파싱 로직 필요
    return "10:00"

def parse_end_time(link: str):
    return "12:00"

@router.get("/popup-details/{reservation_id}")
def get_popup_details(reservation_id: int, db: Session = Depends(get_db)):
    res = db.query(Reservation).filter_by(id=reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {detail.key: detail.value for detail in res.popup_details}