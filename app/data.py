"""
Generates room booking data across a fixed date range, using hardcoded
reference data (subjects, rooms, lecturers, student groups) rather than
randomly generated names. A fixed random seed is still used to decide
*which* room/subject/lecturer/group combination fills each slot, so the
dataset is completely deterministic: it is built once when this module
is imported (see BOOKINGS at the bottom) and never regenerated again, so
it stays identical for the lifetime of the running server and is
identical again the next time the server starts.
"""

import random
from datetime import date, timedelta
from app.models import RoomBooking

random.seed(42)

# --- Fixed reference data, as specified in the assessment brief ---

SUBJECTS = [    
    "Software Development",
    "Cyber Security",
    "Group Project",
    "User Experience",
    "Data and Algorithms",
    "Computer Vision",
    "Artificial Intelligence",
    "Data Science",
]

ROOMS = [
    "CM006", "CM009", "CM010", "CM014", "CM015", "CM016", "CM017",
    "CM018", "CM019", "CM025", "CM026", "CM101", "CM210", "CM234",
]

LECTURERS = [
    "Dr Mark Lochrie",
    "Dr Oliver Kerr",
    "Dr Matt Horton",
    "Ms Julie Allen",
    "Mr Jonathan Edwards",
    "Mr Chris Finnigan",
    "Dr John King",
    "Dr Martin Bateman",
    "Dr Wilson Costa",
]

STUDENT_GROUPS = [
    f"Year {year} - Group {group}"
    for year in (1, 2, 3)
    for group in ("A", "B", "C")
]

BOOKING_START_DATE = date(2026, 10, 1)
BOOKING_END_DATE = date(2027, 8, 5)

PERIODS = [
    (1, "09:00", "10:00"),
    (2, "10:00", "11:00"),
    (3, "11:15", "12:15"),
    (4, "12:15", "13:15"),
    (5, "14:00", "15:00"),
    (6, "15:00", "16:00"),
]

# Probability that any given room/period slot on a weekday is actually booked.
# Keeps the data realistic (not every room is used every single period).
BOOKING_FILL_RATE = 0.55


def _weekdays_between(start: date, end: date):
    """Yield every Monday-Friday date between start and end inclusive."""
    current = start
    while current <= end:
        if current.weekday() < 5:  # 0=Monday ... 4=Friday
            yield current
        current += timedelta(days=1)


def generate_bookings() -> list[RoomBooking]:
    bookings = []
    booking_id = 1

    for booking_date in _weekdays_between(BOOKING_START_DATE, BOOKING_END_DATE):
        day_name = booking_date.strftime("%A")

        for period, start_time, end_time in PERIODS:
            # Shuffle rooms independently each period so bookings are spread
            # out rather than always filling the same rooms first.
            available_rooms = ROOMS.copy()
            random.shuffle(available_rooms)
            num_to_book = int(len(available_rooms) * BOOKING_FILL_RATE)

            for room in available_rooms[:num_to_book]:
                bookings.append(
                    RoomBooking(
                        id=booking_id,
                        date=booking_date.isoformat(),
                        day_of_week=day_name,
                        room=room,
                        period=period,
                        start_time=start_time,
                        end_time=end_time,
                        subject=random.choice(SUBJECTS),
                        lecturer=random.choice(LECTURERS),
                        student_group=random.choice(STUDENT_GROUPS),
                    )
                )
                booking_id += 1

    return bookings


# Generated exactly once, at import time, and cached here. Every request
# reads from this same list -- nothing regenerates or reshuffles it while
# the server is running, so results are stable across requests.
BOOKINGS: list[RoomBooking] = generate_bookings()
