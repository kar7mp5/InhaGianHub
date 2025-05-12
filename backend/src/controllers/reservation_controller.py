from fastapi import APIRouter, HTTPException, Query
from services import crawl_facility_reservations
from cruds import (
    get_all_reservations,
    get_reservations_by_filter,
    get_popup_details_by_reservation_id
)
import re
from datetime import datetime

router = APIRouter()

# Predefined room name to Firestore-safe ID mapping
ROOM_ID_MAPPING = {
    "대강당": "daegangdang",
    "중강당": "junggangdang",
    "소강당": "sogangdang",
    "5남소강당": "5nam_sogangdang"
}


@router.post("/crawl/{room_id}")
def crawl_facility(room_id: str):
    """
    Trigger crawling for a specific facility and return status.

    Args:
        room_id (str): The room ID to crawl.

    Returns:
        dict: Result of crawling including save count and status.
    """
    result = crawl_facility_reservations(None, room_id)

    if result.get("status") == "error":
        return {
            "success": False,
            "error": result.get("reason")
        }

    return {
        "success": True,
        "message": f"Crawling completed for {room_id}",
        "saved_count": result.get("saved_count", 0)
    }


@router.post("/crawl-all")
def crawl_all():
    """
    Crawl all predefined facilities using mapped room IDs.

    Returns:
        dict: Crawl status summary for each facility.
    """
    summary = []

    for name, room_id in ROOM_ID_MAPPING.items():
        print(f"Crawling: {name} as room_id={room_id}")
        result = crawl_facility_reservations(None, room_id)
        summary.append({
            "name": name,
            "room_id": room_id,
            "result": result
        })

    return {
        "status": "ok",
        "facilities_crawled": len(ROOM_ID_MAPPING),
        "results": summary
    }


@router.get("/api/reservations")
def get_reservations(
    room_id: str = Query(..., description="Room ID to filter by"),
    date: str = Query(..., description="Date (YYYY-MM-DD) to filter by")
):
    """
    Retrieve reservations from Firestore filtered by room and date.

    Args:
        room_id (str): Room ID to filter by.
        date (str): Date (YYYY-MM-DD) to filter by.

    Returns:
        dict: Reservation list with start and end time fields parsed.
    """
    try:
        reservations = get_reservations_by_filter(room_id, date)
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


@router.get("/api/reservations/{room_id}/{reservation_id}/details")
def get_popup_details(room_id: str, reservation_id: str):
    """
    Get parsed popup details for a specific reservation document.

    Args:
        room_id (str): Room ID in Firestore.
        reservation_id (str): Reservation document ID.

    Returns:
        dict: Formatted popup detail data.
    """
    details = get_popup_details_by_reservation_id(room_id, reservation_id)
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


@router.get("/api/popup-details/{room_id}/{reservation_id}")
def get_popup_details_raw(room_id: str, reservation_id: str):
    """
    Get raw popup detail key-value data for a reservation.

    Args:
        room_id (str): Room ID in Firestore.
        reservation_id (str): Reservation document ID.

    Returns:
        dict: Raw key-value detail dictionary.
    """
    details = get_popup_details_by_reservation_id(room_id, reservation_id)
    if not details:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {d["key"]: d["value"] for d in details}


def format_time(time_str: str) -> str:
    """
    Format time string to HH:MM, fallback to original on failure.

    Args:
        time_str (str): Raw time string.

    Returns:
        str: Validated HH:MM string or original.
    """
    try:
        return datetime.strptime(time_str, "%H:%M").strftime("%H:%M")
    except ValueError:
        return time_str


def extract_time_fields(reservation: dict) -> None:
    """
    Extracts time range from '일시' field in reservation data.

    Args:
        reservation (dict): Reservation dictionary.

    Returns:
        None: Modifies dictionary in-place.
    """
    ilsi = reservation.get("일시", "")
    match = re.search(r"(\d{8}) ~ (\d{8})\s+(\d{2}:\d{2}) ~ (\d{2}:\d{2})", ilsi)
    if match:
        reservation["start_time"] = match.group(3)
        reservation["end_time"] = match.group(4)
