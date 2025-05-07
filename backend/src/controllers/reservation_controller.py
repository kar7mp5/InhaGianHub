from fastapi import APIRouter, HTTPException
from services import crawl_facility_reservations
from cruds import (
    get_all_reservations,
    get_reservations_by_filter,
    get_popup_details_by_reservation_id
)
import re
from datetime import datetime

FACILITIES = ["대강당", "중강당", "소강당", "5남소강당"]

router = APIRouter()

@router.post("/crawl/{facility_name:regex(^(?!all$).+)}")
def crawl_facility(facility_name: str):
    """Trigger crawling for the specified facility and format the response.

    Args:
        facility_name: The name of the facility to crawl.

    Returns:
        A dictionary with success status and crawling summary.
    """
    result = crawl_facility_reservations(None, facility_name)

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

@router.post("/crawl/all")
def crawl_all():
    for facility in FACILITIES:
        print(facility)
        result = crawl_facility_reservations(None, facility)
        if result.get("status") == "error":
            continue
    return {"status": "ok"}

@router.get("/api/reservations")
def get_reservations(facility_name: str = None, date: str = None):
    """Get all reservations, optionally filtered by facility name and date.
    Also parses '일시' field to extract start_time and end_time.

    Args:
        facility_name: Optional facility filter.
        date: Optional date filter.

    Returns:
        A response dict with reservation list and parsed time fields.
    """
    try:
        if facility_name or date:
            reservations = get_reservations_by_filter(facility_name, date)
        else:
            reservations = get_all_reservations()

        for r in reservations:
            extract_time_fields(r)

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


@router.get("/api/reservations/{reservation_id}/details")
def get_popup_details(reservation_id: str):
    details = get_popup_details_by_reservation_id(reservation_id)
    if not details:
        return {
            "status": "not_found",
            "message": f"No popup details found for reservation ID {reservation_id}",
            "data": []
        }

    formatted_data = []
    for d in details:
        if d["key"] in ["start_time", "end_time"]:
            formatted_data.append(d)
        elif d["key"] == "일시":
            match = re.search(r"\d{8} ~ \d{8}\s+(\d{2}:\d{2}) ~ (\d{2}:\d{2})", d["value"].replace("\n", "").replace("\t", "").strip())
            if match:
                formatted_data.append({"key": "start_time", "value": format_time(match.group(1))})
                formatted_data.append({"key": "end_time", "value": format_time(match.group(2))})
        else:
            formatted_data.append(d)

    return {
        "status": "ok",
        "reservation_id": reservation_id,
        "data": formatted_data
    }



@router.get("/api/popup-details/{reservation_id}")
def get_popup_details_raw(reservation_id: str):
    """Raw popup detail response by reservation ID (key-value dict).

    Args:
        reservation_id: Firestore reservation doc ID.

    Returns:
        A dictionary of raw popup detail key-values.
    """
    details = get_popup_details_by_reservation_id(reservation_id)
    if not details:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {d["key"]: d["value"] for d in details}


def format_time(time_str: str) -> str:
    """Format time to HH:MM or return original if invalid.

    Args:
        time_str: Raw time string.

    Returns:
        A cleaned time string.
    """
    try:
        return datetime.strptime(time_str, "%H:%M").strftime("%H:%M")
    except ValueError:
        return time_str


def extract_time_fields(reservation: dict) -> None:
    """Extract start and end time from '일시' in a reservation dict.

    Args:
        reservation: Dictionary representing a reservation.

    Returns:
        None. Modifies dict in-place.
    """
    ilsi = reservation.get("일시", "")
    match = re.search(r"(\\d{8}) ~ (\\d{8})\\s+(\\d{2}:\\d{2}) ~ (\\d{2}:\\d{2})", ilsi)
    if match:
        reservation["start_time"] = match.group(3)
        reservation["end_time"] = match.group(4)