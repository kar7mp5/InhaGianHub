import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime

from cruds import (
    upsert_reservation,
    find_reservation,
    add_popup_details,
    sync_reservations,
)

BASE_URL = "https://www.inha.ac.kr"
PRINT_URL_TEMPLATE = BASE_URL + "/facility/kr/facilityPrint.do?seq={seq}&req={req}"

# Mapping Korean keys to English
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
    """Converts raw date like '20250514' to '2025-05-14'.

    Args:
        raw_date: Raw date string from table.

    Returns:
        Formatted date string or original if format fails.
    """
    try:
        return datetime.strptime(raw_date.split("~")[0].strip(), "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return raw_date


def fetch_with_retry(url: str, max_retries: int = 3, delay: int = 2) -> str:
    """Tries to fetch a page with retry logic.

    Args:
        url: Target URL to fetch.
        max_retries: Number of retries.
        delay: Delay between retries in seconds.

    Returns:
        HTML string if successful, None otherwise.
    """
    for _ in range(max_retries):
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return res.text
        except Exception:
            time.sleep(delay)
    return None


def generate_print_link(a_tag) -> str:
    """Generates print link from anchor tag.

    Args:
        a_tag: BeautifulSoup anchor tag.

    Returns:
        Print URL or None.
    """
    if not a_tag:
        return None
    href = a_tag.get("href")
    match = re.search(r"jf_facilityPrint\('(\d+)',\s*'(\d+)'\)", href)
    if match:
        seq, req = match.groups()
        return PRINT_URL_TEMPLATE.format(seq=seq, req=req)
    return None


def parse_reservation_table(html: str) -> list:
    """Parses reservation table rows from HTML.

    Args:
        html: Page HTML.

    Returns:
        List of reservation row values and print links.
    """
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
    """Fetches and parses popup details from print link.

    Args:
        print_url: URL to fetch popup detail from.

    Returns:
        Dictionary with English key-value pairs.
    """
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
            eng_key = KEY_TRANSLATION.get(key, key)  # fallback to original if unmapped
            data[eng_key] = value

    # Extract start_time and end_time from datetime_range
    raw_time = data.get("datetime_range", "").replace("\n", "").replace("\t", "").strip()
    match = re.search(r"\d{8} ~ \d{8}\s*(\d{2}:\d{2}) ~ (\d{2}:\d{2})", raw_time)
    if match:
        data["start_time"] = match.group(1)
        data["end_time"] = match.group(2)

    return data


def crawl_facility_reservations(db_unused, facility_name: str) -> dict:
    """Main logic to crawl reservations and sync with Firestore.

    Args:
        db_unused: Placeholder for DB context.
        facility_name: Facility name to crawl.

    Returns:
        Dictionary with crawling stats.
    """
    from utils.config_loader import load_facility_config

    config = load_facility_config()
    url = config.get(facility_name)
    if not url:
        return {"status": "error", "reason": f"No URL configured for {facility_name}"}

    html = fetch_with_retry(url)
    if not html:
        return {"status": "error", "reason": "Failed to fetch page"}

    rows = parse_reservation_table(html)
    saved_count = 0
    updated_count = 0
    skipped_count = 0
    crawled_ids = set()

    if not rows:
        return {
            "status": "ok",
            "facility": facility_name,
            "saved_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "deleted_count": 0,
        }

    for row in rows:
        raw_date, place, department, event, approval, print_link = row
        date = format_date(raw_date)

        doc_id, existing = find_reservation(facility_name, date, place, event)

        doc_data = {
            "facility_name": facility_name,
            "date": date,
            "place": place,
            "department": department,
            "event": event,
            "approval": approval,
            "print_link": print_link or ""
        }

        popup_data = {}  # Initialize popup_data before using it
        if print_link:
            popup_data = fetch_popup_details(print_link)  # Populate if print link exists

        doc_id_final = doc_id if existing else f"{facility_name}_{date}_{place}_{event}"
        crawled_ids.add(doc_id_final)

        if existing:
            if any(existing.get(k) != doc_data.get(k) for k in doc_data):
                upsert_reservation(doc_id_final, doc_data)
                updated_count += 1
            else:
                skipped_count += 1
        else:
            upsert_reservation(doc_id_final, doc_data)
            if popup_data:  # Only add popup details if there's data
                add_popup_details(doc_id_final, popup_data)
            saved_count += 1

    latest_date = format_date(rows[0][0])
    deleted_count = sync_reservations(facility_name, latest_date, crawled_ids)

    return {
        "status": "ok",
        "facility": facility_name,
        "saved_count": saved_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "deleted_count": deleted_count,
    }
