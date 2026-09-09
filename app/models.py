from pydantic import BaseModel
from typing import Optional


class RoomBooking(BaseModel):
    id: int
    date: str            # ISO format, e.g. "2026-10-05"
    day_of_week: str      # e.g. "Monday"
    room: str             # e.g. "CM006"
    period: int           # e.g. 1, 2, 3...
    start_time: str       # e.g. "09:00"
    end_time: str         # e.g. "10:00"
    subject: str          # e.g. "Software Development"
    lecturer: str
    student_group: str    # e.g. "Year 2 - Group A"


class RoomAvailability(BaseModel):
    room: str
    date: str
    period: int
    is_available: bool
    booking: Optional[RoomBooking] = None
