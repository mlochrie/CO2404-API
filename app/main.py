from fastapi import FastAPI, HTTPException, Query, Depends
from typing import List, Optional
from datetime import date as date_type

from app.data import BOOKINGS, ROOMS, SUBJECTS, BOOKING_START_DATE, BOOKING_END_DATE
from app.models import RoomBooking, RoomAvailability
from app.deps import require_student_id
from app.logging_db import get_all_logs, get_logs_for_student

app = FastAPI(
    title="Room Availability API",
    description=(
        "A demo API serving dummy room booking data for computing modules, "
        "built for CO2404 coursework. Interactive docs are provided "
        "automatically by Swagger UI (via OpenAPI) at /docs.\n\n"
        "Every data endpoint requires a `student_id` query parameter. Each "
        "call is recorded in a NoSQL (TinyDB) audit log along with a "
        "timestamp, which can be reviewed via the /logs endpoint."
    ),
    version="2.0.0",
)


@app.get("/", tags=["Info"])
def root():
    """Basic info endpoint, useful as a health check. Does not require a student ID."""
    return {
        "message": "Room Booking API is running.",
        "date_range": f"{BOOKING_START_DATE.isoformat()} to {BOOKING_END_DATE.isoformat()}",
        "docs": "/docs",
        "openapi_spec": "/openapi.json",
        "note": "All data endpoints below require a `student_id` query parameter.",
    }


@app.get("/rooms", tags=["Reference Data"])
def get_rooms(student_id: str = Depends(require_student_id)):
    """Return the list of bookable rooms. Requires `student_id`."""
    return ROOMS


@app.get("/subjects", tags=["Reference Data"])
def get_subjects(student_id: str = Depends(require_student_id)):
    """Return the list of subjects that can be booked. Requires `student_id`."""
    return SUBJECTS


@app.get("/bookings", response_model=List[RoomBooking], tags=["Bookings"])
def get_bookings(
    student_id: str = Depends(require_student_id),
    room: Optional[str] = Query(None, description="Filter by room code, e.g. 'CM006'"),
    subject: Optional[str] = Query(None, description="Filter by subject name"),
    date: Optional[str] = Query(None, description="Filter by exact date, format YYYY-MM-DD"),
    date_from: Optional[str] = Query(None, description="Filter bookings on/after this date"),
    date_to: Optional[str] = Query(None, description="Filter bookings on/before this date"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip, for pagination"),
):
    """
    Return room bookings, optionally filtered by room, subject, or date range.
    Requires `student_id`. Results are paginated via `limit`/`offset`.
    """
    results = BOOKINGS

    if room:
        results = [b for b in results if b.room.upper() == room.upper()]
    if subject:
        results = [b for b in results if b.subject.lower() == subject.lower()]
    if date:
        results = [b for b in results if b.date == date]
    if date_from:
        results = [b for b in results if b.date >= date_from]
    if date_to:
        results = [b for b in results if b.date <= date_to]

    return results[offset: offset + limit]


@app.get("/bookings/{booking_id}", response_model=RoomBooking, tags=["Bookings"])
def get_booking(booking_id: int, student_id: str = Depends(require_student_id)):
    """Return a single booking by its id. Requires `student_id`."""
    for booking in BOOKINGS:
        if booking.id == booking_id:
            return booking
    raise HTTPException(status_code=404, detail=f"Booking with id {booking_id} not found")


@app.get("/rooms/{room}/bookings", response_model=List[RoomBooking], tags=["Rooms"])
def get_room_bookings(
    room: str,
    student_id: str = Depends(require_student_id),
    date_from: Optional[str] = Query(None, description="Filter bookings on/after this date"),
    date_to: Optional[str] = Query(None, description="Filter bookings on/before this date"),
):
    """Return every booking for a specific room. Requires `student_id`."""
    if room.upper() not in ROOMS:
        raise HTTPException(status_code=404, detail=f"Room '{room}' does not exist")

    results = [b for b in BOOKINGS if b.room.upper() == room.upper()]
    if date_from:
        results = [b for b in results if b.date >= date_from]
    if date_to:
        results = [b for b in results if b.date <= date_to]
    return results


@app.get("/rooms/{room}/availability", response_model=RoomAvailability, tags=["Rooms"])
def check_room_availability(
    room: str,
    date: str = Query(..., description="Date to check, format YYYY-MM-DD"),
    period: int = Query(..., ge=1, le=6, description="Period number, 1-6"),
    student_id: str = Depends(require_student_id),
):
    """
    Check whether a specific room is free during a given period on a given
    date. Requires `student_id`. Returns the clashing booking if the room
    is already in use.
    """
    if room.upper() not in ROOMS:
        raise HTTPException(status_code=404, detail=f"Room '{room}' does not exist")

    try:
        date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format")

    clash = next(
        (b for b in BOOKINGS
         if b.room.upper() == room.upper() and b.date == date and b.period == period),
        None,
    )

    return RoomAvailability(
        room=room.upper(),
        date=date,
        period=period,
        is_available=clash is None,
        booking=clash,
    )


@app.get("/logs", tags=["Audit Log"])
def get_logs(student_id: Optional[str] = Query(None, description="Filter logs to just this student ID")):
    """
    Return the NoSQL audit log of API calls (student ID, endpoint, method,
    query params, timestamp). This endpoint itself is NOT logged and does
    not require a student ID, so it can be used to inspect usage.
    """
    if student_id:
        return get_logs_for_student(student_id)
    return get_all_logs()
