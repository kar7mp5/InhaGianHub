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
