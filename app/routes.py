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

import logging
from fastapi import APIRouter
from app.crawler import crawl_and_store
from app.database import engine, SessionLocal
from sqlalchemy import text, inspect

router = APIRouter()

# Setup logger
logger = logging.getLogger(__name__)

@router.post("/crawl")
def trigger_crawling():
    """
    Trigger the crawling process to fetch facility reservation data 
    and store it into the database.
    """
    logger.info("Crawling process triggered via API.")
    crawl_and_store()
    logger.info("Crawling completed successfully.")
    return {"message": "Crawling completed and data stored."}

@router.get("/db-status")
def db_status():
    """
    Retrieve the list of all tables in the connected database.
    """
    logger.info("Fetching database status (list of tables).")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.debug(f"Tables found: {tables}")
    return {"tables": tables}

@router.get("/facilities")
def get_facilities():
    """
    Fetch all facility records from the database.
    """
    logger.info("Request received: Fetch all facilities.")
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT r.id, f.name as facility, r.date, r.department, r.event 
            FROM reservations r
            JOIN facilities f ON r.facility_id = f.id
        """)).mappings().all()
        logger.info(f"Fetched {len(result)} facility records.")
        return {"facilities": result}
    finally:
        db.close()

@router.get("/reservations")
def get_reservations():
    """
    Retrieve all reservation records along with their facility names.
    """
    logger.info("Request received: Fetch all reservations.")
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT r.id, f.name as facility, r.date, r.department, r.event 
            FROM reservations r
            JOIN facilities f ON r.facility_id = f.id
        """)).mappings().all()
        logger.info(f"Fetched {len(result)} reservations.")
        return {"reservations": [dict(row) for row in result]}
    finally:
        db.close()

@router.get("/reservations/{facility_id}")
def get_reservations_by_facility(facility_id: int):
    """
    Retrieve reservations for a specific facility.
    """
    logger.info(f"Fetching reservations for facility_id={facility_id}.")
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, date, department, event 
            FROM reservations 
            WHERE facility_id = :fid
        """), {"fid": facility_id}).mappings().all()
        logger.info(f"Found {len(result)} reservations for facility_id={facility_id}.")
        return {"reservations": [dict(row) for row in result]}
    finally:
        db.close()

@router.get("/popup/{reservation_id}")
def get_popup_details(reservation_id: int):
    """
    Retrieve popup detail information for a specific reservation.
    """
    logger.info(f"Fetching popup details for reservation_id={reservation_id}.")
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT `key`, `value` 
            FROM popup_details 
            WHERE reservation_id = :rid
        """), {"rid": reservation_id}).mappings().all()
        logger.info(f"Fetched {len(result)} popup details for reservation_id={reservation_id}.")
        return {"popup_details": [dict(row) for row in result]}
    finally:
        db.close()
