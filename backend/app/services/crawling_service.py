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

from datetime import datetime

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
        formatted_date = datetime.strptime(start_date, "%Y%m%d").strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        print(f"❌ Invalid date format: {raw_date}")
        return start_date  # Fallback to raw if parsing fails

def fetch_with_retry(url, max_retries=3, delay=2):
    """Fetch URL content with retry logic."""
    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.text
            else:
                print(f"⚠️ Attempt {attempt}: Status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed: {e}")
        time.sleep(delay)
    print(f"❌ Failed to fetch {url} after {max_retries} attempts.")
    return None

def generate_print_link(a_tag):
    """Generate print link from anchor tag."""
    if not a_tag:
        return None
    href = a_tag.get('href')
    match = re.search(r"jf_facilityPrint\('(\d+)',\s*'(\d+)'\)", href)
    if match:
        seq, req = match.groups()
        return PRINT_URL_TEMPLATE.format(seq=seq, req=req)
    return None

def parse_reservation_table(html_content):
    """Parse reservation table from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if not table:
        print("❌ Reservation table not found.")
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
    """Fetch detailed popup data as dictionary."""
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
    Crawl reservation data and return result summary.
    """
    config = load_facility_config()
    target_url = config.get(facility_name)

    if not target_url:
        return {"status": "error", "reason": f"No URL for {facility_name}"}

    html_content = fetch_with_retry(target_url)
    if not html_content:
        return {"status": "error", "reason": "Failed to fetch main page"}

    reservations = parse_reservation_table(html_content)
    if not reservations:
        return {"status": "ok", "saved_count": 0}

    saved_count = 0

    for res in reservations:
        date_range, place, department, event, approval, print_link = res
        date = format_date(date_range)

        exists = db.query(Reservation).filter_by(
            facility_name=facility_name,
            date=date,
            place=place,
            department=department,
            event=event
        ).first()

        if exists:
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

        popup_data = fetch_popup_details(print_link)
        for key, value in popup_data.items():
            db.add(PopupDetail(
                reservation_id=reservation_entry.id,
                key=key,
                value=value
            ))
        db.commit()
        saved_count += 1

    return {"status": "ok", "saved_count": saved_count}
