from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from models.base import Base

class Reservation(Base):
    __tablename__ = "reservation"

    id = Column(Integer, primary_key=True, index=True)
    facility_name = Column(String(100))
    date = Column(String(50))
    place = Column(String(100))
    department = Column(String(100))
    event = Column(String(200))
    approval = Column(String(20))
    print_link = Column(Text)
    
    popup_details = relationship("PopupDetail", back_populates="reservation")
