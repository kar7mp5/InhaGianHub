import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime

from firebase import db
from utils import load_facility_config
from datetime import datetime, timedelta

from cruds import (
    upsert_reservation,
    find_reservation,
    add_popup_details,
    sync_reservations,
    hash_reservation
)

BASE_URL = "https://www.inha.ac.kr"
PRINT_URL_TEMPLATE = BASE_URL + "/facility/kr/facilityPrint.do?seq={seq}&req={req}"

KEY_TRANSLATION = {
    "장소": "place",
    "일시": "datetime_range",
    "대여물품": "rental_items",
    "부서명": "department",
    "행사명": "event",
    "단체명": "organization",
    "승인여부": "approval",
    "start_time": "start_time",
    "end_time": "end_time"
}


def format_date(raw_date: str) -> str:
    """Convert raw date like '20250514' to '2025-05-14'."""
    try:
        return datetime.strptime(raw_date.split("~")[0].strip(), "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return raw_date


def fetch_with_retry(url: str, max_retries: int = 3, delay: int = 2) -> str:
    """Fetch page contents with retries and proper headers."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.inha.ac.kr/"
    }
    for _ in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                return res.text
        except Exception as e:
            print(f"⚠️ request failed: {e}")
            time.sleep(delay)
    return None


def generate_print_link(a_tag) -> str:
    """Extract print link URL from anchor tag."""
    if not a_tag:
        return None
    href = a_tag.get("href")
    match = re.search(r"jf_facilityPrint\('(\d+)',\s*'(\d+)'\)", href)
    if match:
        seq, req = match.groups()
        return PRINT_URL_TEMPLATE.format(seq=seq, req=req)
    return None


def parse_reservation_table(html: str) -> list:
    """Extract reservation rows from facility table."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []
    rows = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        values = [col.get_text(strip=True) for col in cols[:-1]]
        print_link = generate_print_link(cols[-1].find("a"))
        rows.append(values + [print_link])
    return rows


def fetch_popup_details(print_url: str) -> dict:
    """Fetch detail popup data from print page."""
    if not print_url:
        return {}

    html = fetch_with_retry(print_url)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", attrs={"width": "600px"})
    data = {}

    for row in table.find_all("tr"):
        if row.find("th") and row.find("td"):
            key = row.find("th").text.strip()
            value = row.find("td").text.strip()
            eng_key = KEY_TRANSLATION.get(key, key)
            data[eng_key] = value

    raw_time = data.get("datetime_range", "").replace("\n", "").replace("\t", "").strip()
    match = re.search(r"\d{8} ~ \d{8}\s*(\d{2}:\d{2}) ~ (\d{2}:\d{2})", raw_time)
    if match:
        data["start_time"] = match.group(1)
        data["end_time"] = match.group(2)

    return data


def delete_outdated_reservations(room_id: str, before_date: str) -> int:
    """
    Delete all reservations in a room before the given date (exclusive).
    """
    delete_count = 0
    query = db.collection("rooms").document(room_id).collection("reservations") \
        .where("date", "<", before_date)

    docs = list(query.stream())

    for doc in docs:
        doc.reference.delete()
        delete_count += 1

    return delete_count


def crawl_facility_reservations(db_unused, room_id: str) -> dict:
    """
    Main logic to crawl reservations and sync with Firestore (room-based structure).

    Args:
        db_unused: Placeholder for DB context.
        room_id (str): Room ID (facility name) to crawl.

    Returns:
        dict: Crawling summary including counts of saves, updates, skips, and deletions.
    """
    config = load_facility_config()
    url = config.get(room_id)
    if not url:
        return {"status": "error", "reason": f"No URL configured for {room_id}"}

    html = fetch_with_retry(url)
    if not html:
        return {"status": "error", "reason": "Failed to fetch page"}

    rows = parse_reservation_table(html)
    saved_count = 0
    updated_count = 0
    skipped_count = 0
    crawled_ids = set()

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    outdated_deleted_count = delete_outdated_reservations(room_id, yesterday)

    if not rows:
        return {
            "status": "ok",
            "facility": room_id,
            "saved_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "deleted_count": 0,
            "outdated_deleted_count": outdated_deleted_count
        }

    for row in rows:
        raw_date, place, department, event, approval, print_link = row
        date = format_date(raw_date)

        doc_data = {
            "room_id": room_id,
            "date": date,
            "place": place,
            "department": department,
            "event": event,
            "approval": approval,
            "print_link": print_link or ""
        }

        popup_data = {}
        if print_link:
            popup_data = fetch_popup_details(print_link)

        reservation_id, existing = find_reservation(room_id, date, event)
        if not reservation_id:
            reservation_id = hash_reservation(doc_data)

        crawled_ids.add(reservation_id)

        if existing:
            if any(existing.get(k) != doc_data.get(k) for k in doc_data):
                upsert_reservation(room_id, reservation_id, doc_data)
                updated_count += 1
            else:
                skipped_count += 1
        else:
            upsert_reservation(room_id, reservation_id, doc_data)
            if popup_data:
                add_popup_details(room_id, reservation_id, popup_data)
            saved_count += 1

    latest_date = format_date(rows[0][0])
    deleted_count = sync_reservations(room_id, latest_date, crawled_ids)

    return {
        "status": "ok",
        "facility": room_id,
        "saved_count": saved_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "deleted_count": deleted_count,
        "outdated_deleted_count": outdated_deleted_count
    }