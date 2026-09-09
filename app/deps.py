"""
Shared dependency used across endpoints to enforce that every caller
supplies their student ID, and to record that call in the NoSQL log.
"""

from fastapi import Query, Request
from app.logging_db import log_call


def require_student_id(
    request: Request,
    student_id: str = Query(
        ...,
        min_length=1,
        description="Your student ID number. Required on every request; each "
                    "call is recorded in the audit log along with a timestamp.",
        examples=["12345678"],
    ),
) -> str:
    """
    FastAPI dependency: makes `student_id` a required query parameter on
    any route that uses it, and logs the call (student ID, endpoint,
    method, other query params, timestamp) to the NoSQL log store.
    """
    other_params = {k: v for k, v in request.query_params.items() if k != "student_id"}
    log_call(
        student_id=student_id,
        endpoint=request.url.path,
        method=request.method,
        query_params=other_params,
    )
    return student_id
