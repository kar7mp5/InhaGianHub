from datetime import datetime
import requests
import re
import time
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models.reservation_model import Reservation
from models.popup_detail_model import PopupDetail
from utils.config_loader import load_facility_config

BASE_URL = "https://www.inha.ac.kr"
PRINT_URL_TEMPLATE = BASE_URL + "/facility/kr/facilityPrint.do?seq={seq}&req={req}"

def format_date(raw_date: str) -> str:
    """
    Convert date range string to 'YYYY-MM-DD' format.

    Args:
        raw_date (str): Date string in format 'YYYYMMDD ~ YYYYMMDD'.

    Returns:
        str: Formatted date as 'YYYY-MM-DD'.
    """
    start_date = raw_date.split('~')[0].strip()
    try:
        return datetime.strptime(start_date, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return start_date

def fetch_with_retry(url, max_retries=3, delay=2):
    """
    Fetch URL content with retry logic.

    Args:
        url (str): Target URL to fetch.
        max_retries (int): Number of retry attempts.
        delay (int): Delay between retries in seconds.

    Returns:
        str or None: HTML content if successful, else None.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.text
        except Exception:
            pass
        time.sleep(delay)
    return None

def generate_print_link(a_tag):
    """
    Generate print link from anchor tag.

    Args:
        a_tag (Tag): BeautifulSoup anchor tag.

    Returns:
        str or None: Generated print URL or None.
    """
    if not a_tag:
        return None
    href = a_tag.get('href')
    match = re.search(r"jf_facilityPrint\('(\d+)',\s*'(\d+)'\)", href)
    if match:
        seq, req = match.groups()
        return PRINT_URL_TEMPLATE.format(seq=seq, req=req)
    return None

def parse_reservation_table(html_content):
    """
    Parse reservation table from HTML content.

    Args:
        html_content (str): HTML content containing reservation table.

    Returns:
        list: List of reservation rows.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if not table:
        return []

    rows = []
    for row in table.find('tbody').find_all('tr'):
        cols = row.find_all('td')
        values = [col.get_text(strip=True) for col in cols[:-1]]
        a_tag = cols[-1].find('a')
        print_link = generate_print_link(a_tag)
        rows.append(values + [print_link])
    return rows

def fetch_popup_details(print_url):
    """
    Fetch detailed popup data as dictionary.

    Args:
        print_url (str): URL for the popup details.

    Returns:
        dict: Key-value pairs from the popup table.
    """
    details = {}
    if not print_url:
        return details

    html = fetch_with_retry(print_url)
    if not html:
        return details

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', attrs={'width': '600px'})
    if not table:
        return details

    for row in table.find_all('tr'):
        th = row.find('th')
        td = row.find('td')
        if th and td:
            key = th.get_text(strip=True)
            value = td.get_text(separator=' ', strip=True)
            details[key] = value
    return details

def crawl_facility_reservations(db: Session, facility_name: str) -> dict:
    """
    Crawl reservation data for a specific facility and store it in the database.

    Args:
        db (Session): SQLAlchemy database session.
        facility_name (str): Name of the facility to crawl.

    Returns:
        dict: Summary of the crawling process including counts.
    """
    config = load_facility_config()
    target_url = config.get(facility_name)

    if not target_url:
        return {"status": "error", "reason": f"No URL configured for {facility_name}"}

    html_content = fetch_with_retry(target_url)
    if not html_content:
        return {"status": "error", "reason": "Failed to fetch facility page"}

    reservations = parse_reservation_table(html_content)
    if not reservations:
        return {
            "status": "ok",
            "facility": facility_name,
            "total_found": 0,
            "saved_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "message": "No reservations found."
        }

    saved_count = 0
    updated_count = 0
    skipped_count = 0

    for res in reservations:
        # Direct unpacking without validation (initial approach)
        date_range, place, department, event, approval, print_link = res

        date = format_date(date_range)

        existing = db.query(Reservation).filter_by(
            facility_name=facility_name,
            date=date,
            place=place,
            event=event
        ).first()

        if existing:
            is_updated = False
            if existing.department != department:
                existing.department = department
                is_updated = True
            if existing.approval != approval:
                existing.approval = approval
                is_updated = True
            if existing.print_link != (print_link or ""):
                existing.print_link = print_link or ""
                is_updated = True

            if is_updated:
                db.commit()
                updated_count += 1
            else:
                skipped_count += 1
            continue

        reservation_entry = Reservation(
            facility_name=facility_name,
            date=date,
            place=place,
            department=department,
            event=event,
            approval=approval,
            print_link=print_link or ""
        )
        db.add(reservation_entry)
        db.commit()
        db.refresh(reservation_entry)

        if print_link:
            popup_data = fetch_popup_details(print_link)
            for key, value in popup_data.items():
                db.add(PopupDetail(
                    reservation_id=reservation_entry.id,
                    key=key,
                    value=value
                ))
            db.commit()

        saved_count += 1

    return {
        "status": "ok",
        "facility": facility_name,
        "total_found": len(reservations),
        "saved_count": saved_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "message": f"{facility_name}: {saved_count} saved, {updated_count} updated, {skipped_count} skipped."
    }
