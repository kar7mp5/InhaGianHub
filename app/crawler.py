# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# © 2025 MinSup Kim

import requests
import yaml
import re
import time
from bs4 import BeautifulSoup
from app.database import SessionLocal
import logging

BASE_URL = "https://www.inha.ac.kr"
PRINT_URL_TEMPLATE = BASE_URL + "/facility/kr/facilityPrint.do?seq={seq}&req={req}"

logger = logging.getLogger(__name__)

def load_config():
    """
    Load facility URLs from the configuration file.

    Returns:
        dict: Facility names mapped to their URLs.
    """
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)['facilities']

def fetch_with_retry(url, max_retries=3, delay=2):
    """
    Fetch HTML content from a URL with retry logic.

    Args:
        url (str): Target URL.
        max_retries (int): Number of retries.
        delay (int): Delay between retries.

    Returns:
        str: HTML content if successful, else None.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.warning(f"Retry {attempt+1} failed for {url}: {e}")
        time.sleep(delay)
    logger.error(f"Failed to fetch {url}")
    return None

def generate_print_link(a_tag):
    """
    Generate print link from anchor tag.

    Args:
        a_tag (Tag): BeautifulSoup <a> tag.

    Returns:
        str or None: Generated URL or None.
    """
    if not a_tag:
        return None
    href = a_tag.get('href')
    match = re.search(r"jf_facilityPrint\('(\d+)',\s*'(\d+)'\)", href)
    return PRINT_URL_TEMPLATE.format(seq=match.group(1), req=match.group(2)) if match else None

def _crawl_process():
    """
    Core crawling process to fetch reservation and popup details.
    """
    db = SessionLocal()
    config = load_config()

    for facility_name, url in config.items():
        db.execute("INSERT IGNORE INTO facilities (name) VALUES (:name)", {"name": facility_name})
        db.commit()
        facility_id = db.execute("SELECT id FROM facilities WHERE name=:name", {"name": facility_name}).fetchone()[0]

        html = fetch_with_retry(url)
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        for row in table.find('tbody').find_all('tr'):
            cols = row.find_all('td')
            values = [col.get_text(strip=True) for col in cols[:-1]]
            print_link = generate_print_link(cols[-1].find('a'))

            db.execute("""
                INSERT INTO reservations (facility_id, date, place, department, event, approval, print_link)
                VALUES (:facility_id, :date, :place, :department, :event, :approval, :print_link)
            """, {
                "facility_id": facility_id,
                "date": values[0], "place": values[1],
                "department": values[2], "event": values[3],
                "approval": values[4], "print_link": print_link
            })
        db.commit()

        reservations = db.execute("SELECT id, print_link FROM reservations WHERE facility_id=:fid", {"fid": facility_id})
        for res_id, link in reservations.fetchall():
            if not link:
                continue
            popup_html = fetch_with_retry(link)
            soup = BeautifulSoup(popup_html, 'html.parser')
            table = soup.find('table', attrs={'width': '600px'})
            if not table:
                continue
            for row in table.find_all('tr'):
                th, td = row.find('th'), row.find('td')
                if th and td:
                    db.execute("""
                        INSERT INTO popup_details (reservation_id, `key`, `value`)
                        VALUES (:rid, :key, :value)
                    """, {"rid": res_id, "key": th.get_text(strip=True), "value": td.get_text(separator=' ', strip=True)})
        db.commit()
    db.close()

def crawl_and_store():
    """
    Public method to trigger crawling.
    """
    logger.info("Crawling started.")
    _crawl_process()
    logger.info("Crawling completed.")
