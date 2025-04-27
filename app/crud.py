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

from app import database

def create_reservation(db, reservation_data):
    """
    Insert a reservation record into the database.

    Args:
        db: Database session.
        reservation_data: Reservation ORM object.

    Returns:
        Inserted reservation object.
    """
    db.add(reservation_data)
    db.commit()
    db.refresh(reservation_data)
    return reservation_data

def create_popup_detail(db, popup_data):
    """
    Insert popup detail data into the database.

    Args:
        db: Database session.
        popup_data: PopupDetail ORM object.
    """
    db.add(popup_data)
    db.commit()
