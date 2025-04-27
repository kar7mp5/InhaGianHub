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

from app.database import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey

class Reservation(Base):
    """
    ORM model for the reservations table.
    """
    __tablename__ = 'reservations'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(50))
    place = Column(String(100))
    department = Column(String(100))
    event = Column(String(200))
    approval = Column(String(20))
    print_link = Column(Text)
    room = Column(String(50))

class PopupDetail(Base):
    """
    ORM model for the popup_details table.
    """
    __tablename__ = 'popup_details'

    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey('reservations.id'))
    key = Column(String(100))
    value = Column(Text)
