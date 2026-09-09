# Room Booking API

A demo REST API serving dummy room booking data for computing modules,
built with **FastAPI**. FastAPI automatically generates an OpenAPI spec and
serves interactive **Swagger UI** documentation out of the box — no extra
configuration needed.

Every data endpoint requires the caller to supply their **student ID**, and
every call is recorded in a **NoSQL audit log** (student ID, endpoint,
timestamp) in **MongoDB**, via the `pymongo` driver.

## Project structure

```
timetable_api/
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI app + all routes
│   ├── models.py       # Pydantic schemas (RoomBooking, RoomAvailability)
│   ├── data.py          # Hardcoded reference data + booking generation (fixed seed)
│   ├── deps.py           # Shared dependency: requires + logs student_id
│   └── logging_db.py     # MongoDB connection and logging functions
├── .env.example          # Template for your Atlas connection details
├── .gitignore             # Excludes .env and Python artifacts
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

This project connects to **MongoDB Atlas**. To configure it:

1. In Atlas, go to your cluster → **Connect** → **Drivers**, and copy the
   connection string. It looks like:
   ```
   mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
   ```
2. Replace `<username>` and `<password>` with a real database user's
   credentials (Atlas → **Database Access**, not your Atlas login).
3. Make sure your current IP address is allowed under Atlas →
   **Network Access** (or temporarily allow `0.0.0.0/0` for testing —
   remove this before submitting/deploying anywhere public).
4. Copy `.env.example` to `.env` in the project root and fill in your
   real connection string:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   MONGO_URI=mongodb+srv://youruser:yourpassword@yourcluster.mongodb.net/?retryWrites=true&w=majority
   MONGO_DB_NAME=room_booking_api
   ```

The `.env` file is loaded automatically (via `python-dotenv`) when the app
starts, and is already excluded in `.gitignore` so your credentials won't
end up committed anywhere. No manual collection setup is needed — MongoDB
creates the database and the `api_calls` collection automatically the
first time a document is inserted.

## Running the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. If the Atlas
connection details are wrong or your IP isn't whitelisted, calls that
require `student_id` will fail with a connection/timeout error when they
try to log — check `.env` and Atlas Network Access first if that happens.

## Swagger UI

Once running, open your browser to:

- **Swagger UI (interactive docs):** http://localhost:8000/docs
- **Raw OpenAPI spec (JSON):** http://localhost:8000/openapi.json
- **ReDoc (alternative docs view):** http://localhost:8000/redoc

## Student ID requirement

Every data endpoint now requires a **`student_id`** query parameter, e.g.:

```
GET /rooms?student_id=12345678
GET /bookings?student_id=12345678&room=CM006
```

Calling an endpoint without it returns a `422 Unprocessable Entity` error
automatically — FastAPI enforces this because `student_id` is declared as a
required parameter (no default value) in `app/deps.py`.

This is implemented as a single shared **dependency**
(`require_student_id` in `app/deps.py`), injected into every route with
`Depends(require_student_id)`, rather than repeating the parameter and
logging logic in each route function individually. This is worth
mentioning in your write-up as an example of the DRY principle applied via
FastAPI's dependency injection system.

## The audit log (NoSQL)

Every time `require_student_id` runs, it writes a document to the
`api_calls` collection in MongoDB:

```json
{
  "student_id": "12345678",
  "endpoint": "/bookings",
  "method": "GET",
  "query_params": { "room": "CM006", "limit": "2" },
  "timestamp": "2026-09-03T12:16:31.027852+00:00"
}
```

You can browse this collection directly with MongoDB Compass, `mongosh`,
or any MongoDB GUI, in addition to via the API itself:

```
GET /logs                       # every logged call, most recent first
GET /logs?student_id=12345678   # only calls made with that student ID
```

`/logs` itself is **not** logged and does **not** require a `student_id`,
so it can be used freely to demonstrate the audit trail (e.g. in a viva or
screenshot for your report).

## The booking data

- **Subjects:** Software Development, Cyber Security, Group Project, User
  Experience, Data and Algorithms, Computer Vision, Artificial Intelligence,
  Data Science
- **Rooms:** CM006, CM009, CM010, CM014, CM015, CM016, CM017, CM018, CM019,
  CM025, CM026, CM101, CM210, CM234
- **Lecturers:** a fixed list of 9 named lecturers (see `app/data.py`)
- **Student groups:** Year 1/2/3, each with Group A/B/C
- **Date range:** 01/10/2026 to 05/08/2027, weekdays only
- **Periods per day:** 6 (09:00–10:00 through 15:00–16:00)

All of the above are hardcoded lists in `app/data.py` — nothing is
generated with `Faker` or any other name-generation library. A fixed
random seed (42) is still used to decide *which* room/subject/lecturer/
group combination fills each slot, so the dataset is fully reproducible.

Bookings are generated **exactly once**, when the app starts (see the
`BOOKINGS` list at the bottom of `app/data.py`), and every request reads
from that same in-memory list. Nothing regenerates or reshuffles it while
the server is running, so results are stable across requests — and
because the random seed is fixed, they're identical again the next time
the server restarts too.

## Endpoints

| Method | Path                        | Requires `student_id`? | Description                                          |
|--------|-----------------------------|:-----------------------:|-------------------------------------------------------|
| GET    | `/`                          | No                       | Health check / basic info                              |
| GET    | `/rooms`                     | Yes                      | List all bookable room codes                            |
| GET    | `/subjects`                  | Yes                      | List all subjects                                       |
| GET    | `/bookings`                  | Yes                      | List bookings, filterable + paginated                    |
| GET    | `/bookings/{booking_id}`     | Yes                      | Get a single booking by id                               |
| GET    | `/rooms/{room}/bookings`     | Yes                      | All bookings for one room                                |
| GET    | `/rooms/{room}/availability` | Yes                      | Check if a room is free at a given date + period          |
| GET    | `/logs`                      | No                       | View the NoSQL audit log of calls (optionally filtered)   |

## Notes for your write-up

- FastAPI's dependency injection (`Depends`) is what enforces the required
  parameter *and* triggers logging consistently across every route,
  without duplicating that logic in each function.
- Validation is automatic and type-checked: a missing `student_id`, or an
  out-of-range `period`, returns a structured `422` error with no manual
  error-handling code needed.
- MongoDB is a document-oriented NoSQL database, so each logged call is
  stored as a JSON-like document (a `dict` in Python, a BSON document in
  Mongo) rather than a row in a relational table — worth contrasting with
  SQL in your write-up if the brief asks for that comparison.
- The connection is configured via environment variables (`MONGO_URI`,
  `MONGO_DB_NAME`) loaded from a `.env` file, rather than hardcoded —
  standard practice so credentials aren't committed to source control.
  This is worth a line in your report as a security/good-practice point.
- Atlas connection strings use the `mongodb+srv://` scheme, which relies
  on DNS SRV records — that's why `dnspython` is a required dependency
  even though it's never imported directly in the code.
