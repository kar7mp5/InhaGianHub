from pydantic import BaseModel
from typing import Optional

class ReservationResponse(BaseModel):
    id: int
    facility_name: str
    date: str
    place: str
    department: str
    event: str
    approval: str
    print_link: Optional[str]

    class Config:
        from_attributes = True
