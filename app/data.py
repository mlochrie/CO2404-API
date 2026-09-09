"""
Generates realistic-looking dummy room booking data across a fixed date
range. Uses a fixed random seed so the data is identical every time the
app restarts -- handy for demoing and for writing automated tests against
known values.
"""

import random
from datetime import date, timedelta
from faker import Faker
from app.models import RoomBooking

fake = Faker("en_GB")
Faker.seed(42)
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
    "Data Science"
]

ROOMS = [
    "CM006", "CM009", "CM010", "CM014", "CM015", "CM016", "CM017",
    "CM018", "CM019", "CM025", "CM026", "CM101", "CM210", "CM234",
]

BOOKING_START_DATE = date(2026, 10, 1)
BOOKING_END_DATE = date(2027, 4, 15)

PERIODS = [
    (1, "09:00", "10:00"),
    (2, "10:00", "11:00"),
    (3, "11:15", "12:15"),
    (4, "12:15", "13:15"),
    (5, "14:00", "15:00"),
    (6, "15:00", "16:00"),
]

STUDENT_GROUPS = [
    f"Year {year} - Group {group}"
    for year in (1, 2, 3)
    for group in ("A", "B", "C")
]

LECTURERS = ["Dr Mark Lochrie", "Dr Oliver Kerr", "Dr Matt Horton", "Ms Julie Allen", "Mr Jonathan Edwards", "Mr Chris Finigan", "Dr John King", "Dr Martin Bateman", "Dr Wilson Costa"]

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


# Generated once at import time, acting as our "database" for the demo.
BOOKINGS: list[RoomBooking] = generate_bookings()
