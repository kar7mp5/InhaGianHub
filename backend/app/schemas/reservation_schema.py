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
    print_link: Optional[str]  # <-- 여기! None 허용

    class Config:
        from_attributes = True  # Pydantic v2 대응
