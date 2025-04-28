from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.base import Base

class PopupDetail(Base):
    """
    ORM model for popup detail data.
    """
    __tablename__ = "popup_detail"

    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservation.id"))
    key = Column(String(100))
    value = Column(Text)   # <-- 여기 Text 타입으로 수정!

    reservation = relationship("Reservation", back_populates="popup_details")
