"""Project configuration and path management."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SOURCE_DIR = DATA_DIR / "source"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
FEATURES_DIR = DATA_DIR / "features"
EVENTS_DIR = DATA_DIR / "events"
LOGS_DIR = BASE_DIR / "logs"
WAREHOUSE_PATH = DATA_DIR / "warehouse.duckdb"

FACULTIES = ["Economics", "IT", "Management", "Law", "Engineering"]
FACULTY_PREFIX = {
    "Economics": "ECO",
    "IT": "IT",
    "Management": "MGT",
    "Law": "LAW",
    "Engineering": "ENG",
}
STUDENT_STATUSES = ["active", "academic_leave", "graduated"]
LMS_ACTIVITY_TYPES = [
    "login",
    "course_view",
    "material_download",
    "assignment_submit",
    "forum_post",
]
ROOM_EVENT_TYPES = ["entered_room", "left_room"]
STREAM_EVENT_TYPES = [
    "lms_login",
    "assignment_submitted",
    "course_material_viewed",
    "entered_building",
    "left_building",
]


def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    for directory in (
        DATA_DIR,
        SOURCE_DIR,
        BRONZE_DIR,
        SILVER_DIR,
        GOLD_DIR,
        FEATURES_DIR,
        EVENTS_DIR,
        LOGS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
