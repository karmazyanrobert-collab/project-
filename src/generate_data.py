"""Synthetic source data generator for the university data platform."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from src.config import (
    FACULTIES,
    FACULTY_PREFIX,
    LMS_ACTIVITY_TYPES,
    ROOM_EVENT_TYPES,
    SOURCE_DIR,
    STUDENT_STATUSES,
    ensure_directories,
)

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)


def _generate_students(n: int = 300) -> pd.DataFrame:
    """Generate student records with intentional data quality issues."""
    rows = []
    for i in range(1, n + 1):
        faculty = random.choice(FACULTIES)
        prefix = FACULTY_PREFIX[faculty]
        group_num = random.randint(101, 303)
        rows.append(
            {
                "student_id": i,
                "full_name": fake.name(),
                "faculty": faculty,
                "group_id": f"{prefix}-{group_num}",
                "enrollment_year": random.randint(2019, 2024),
                "status": random.choices(
                    STUDENT_STATUSES, weights=[0.85, 0.1, 0.05]
                )[0],
            }
        )

    df = pd.DataFrame(rows)

    # Intentional issues
    dup_idx = random.sample(range(len(df)), 3)
    for idx in dup_idx:
        duplicate = df.iloc[idx].copy()
        duplicate["full_name"] = fake.name()
        df = pd.concat([df, pd.DataFrame([duplicate])], ignore_index=True)

    null_name_idx = random.sample(range(len(df)), 3)
    df.loc[null_name_idx, "full_name"] = None

    return df


def _generate_courses(n: int = 20) -> pd.DataFrame:
    """Generate course catalog."""
    course_names = [
        "Microeconomics",
        "Macroeconomics",
        "Python Programming",
        "Data Structures",
        "Corporate Finance",
        "Marketing Strategy",
        "Civil Law",
        "Criminal Law",
        "Thermodynamics",
        "Circuit Analysis",
        "Database Systems",
        "Machine Learning",
        "Operations Management",
        "Business Analytics",
        "International Trade",
        "Software Engineering",
        "Constitutional Law",
        "Structural Mechanics",
        "Statistics",
        "Project Management",
    ]
    rows = []
    for i in range(1, n + 1):
        faculty = FACULTIES[(i - 1) % len(FACULTIES)]
        rows.append(
            {
                "course_id": i,
                "course_name": course_names[i - 1],
                "faculty": faculty,
                "credits": random.choice([3, 4, 5, 6]),
            }
        )
    return pd.DataFrame(rows)


def _generate_grades(students: pd.DataFrame, courses: pd.DataFrame, min_rows: int = 2000) -> pd.DataFrame:
    """Generate grade records with some out-of-range values and duplicates."""
    student_ids = students["student_id"].unique().tolist()
    course_ids = courses["course_id"].tolist()
    rows = []
    grade_id = 1
    start_date = datetime(2024, 9, 1)

    while len(rows) < min_rows:
        student_id = random.choice(student_ids)
        course_id = random.choice(course_ids)
        grade_date = start_date + timedelta(days=random.randint(0, 240))
        rows.append(
            {
                "grade_id": grade_id,
                "student_id": student_id,
                "course_id": course_id,
                "grade": round(random.gauss(72, 15), 1),
                "grade_date": grade_date.strftime("%Y-%m-%d"),
            }
        )
        grade_id += 1

    df = pd.DataFrame(rows)

    # Intentional bad grades
    bad_indices = random.sample(range(len(df)), 5)
    bad_values = [-5, 120, 150, -10, 105]
    for idx, val in zip(bad_indices, bad_values):
        df.at[idx, "grade"] = val

    # Duplicate grade_id
    dup_indices = random.sample(range(len(df)), 3)
    for idx in dup_indices:
        duplicate = df.iloc[idx].copy()
        duplicate["grade"] = random.uniform(50, 90)
        df = pd.concat([df, pd.DataFrame([duplicate])], ignore_index=True)

    return df


def _generate_assignments(students: pd.DataFrame, courses: pd.DataFrame, min_rows: int = 3000) -> pd.DataFrame:
    """Generate assignment submission records."""
    student_ids = students["student_id"].unique().tolist()
    course_ids = courses["course_id"].tolist()
    assignment_names = [
        "Homework 1",
        "Homework 2",
        "Lab Work",
        "Midterm Essay",
        "Final Project",
        "Quiz",
        "Case Study",
        "Presentation",
    ]
    rows = []
    assignment_id = 1
    base_date = datetime(2024, 9, 15)

    while len(rows) < min_rows:
        student_id = random.choice(student_ids)
        course_id = random.choice(course_ids)
        deadline = base_date + timedelta(days=random.randint(0, 200))
        submitted = random.random() < 0.78
        submitted_at = None
        score = None
        if submitted:
            submitted_at = (deadline - timedelta(days=random.randint(-3, 5))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            score = round(random.gauss(75, 12), 1)
            score = max(0, min(100, score))

        rows.append(
            {
                "assignment_id": assignment_id,
                "student_id": student_id,
                "course_id": course_id,
                "assignment_name": random.choice(assignment_names),
                "submitted": submitted,
                "score": score,
                "deadline": deadline.strftime("%Y-%m-%d"),
                "submitted_at": submitted_at,
            }
        )
        assignment_id += 1

    return pd.DataFrame(rows)


def _generate_lms_activity(students: pd.DataFrame, min_rows: int = 5000) -> pd.DataFrame:
    """Generate LMS activity events."""
    student_ids = students["student_id"].unique().tolist()
    rows = []
    activity_id = 1
    start_time = datetime(2025, 1, 1, 8, 0, 0)

    while len(rows) < min_rows:
        student_id = random.choice(student_ids)
        activity_time = start_time + timedelta(
            minutes=random.randint(0, 60 * 24 * 120),
            seconds=random.randint(0, 59),
        )
        rows.append(
            {
                "activity_id": activity_id,
                "student_id": student_id,
                "activity_type": random.choice(LMS_ACTIVITY_TYPES),
                "activity_time": activity_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_minutes": random.randint(1, 180),
            }
        )
        activity_id += 1

    return pd.DataFrame(rows)


def _generate_rooms(min_rooms: int = 30) -> pd.DataFrame:
    """Generate campus room inventory."""
    buildings = [f"B{i}" for i in range(1, 6)]
    room_types = ["lecture", "lab", "seminar", "computer_lab"]
    rows = []
    room_id = 1

    for building_id in buildings:
        rooms_in_building = max(6, min_rooms // len(buildings))
        for room_num in range(1, rooms_in_building + 1):
            rows.append(
                {
                    "room_id": f"R-{building_id}-{room_num:02d}",
                    "building_id": building_id,
                    "room_type": random.choice(room_types),
                    "capacity": random.choice([30, 40, 50, 60, 80, 100, 120]),
                }
            )
            room_id += 1
            if len(rows) >= min_rooms:
                break
        if len(rows) >= min_rooms:
            break

    return pd.DataFrame(rows)


def _generate_room_events(students: pd.DataFrame, rooms: pd.DataFrame, min_rows: int = 3000) -> pd.DataFrame:
    """Generate room entry/exit events."""
    student_ids = students["student_id"].unique().tolist()
    rows = []
    event_id = 1
    start_time = datetime(2025, 2, 1, 7, 0, 0)

    while len(rows) < min_rows:
        room = rooms.sample(1).iloc[0]
        student_id = random.choice(student_ids)
        event_time = start_time + timedelta(
            minutes=random.randint(0, 60 * 24 * 90),
            seconds=random.randint(0, 59),
        )
        rows.append(
            {
                "event_id": event_id,
                "student_id": student_id,
                "room_id": room["room_id"],
                "building_id": room["building_id"],
                "event_type": random.choice(ROOM_EVENT_TYPES),
                "event_time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        event_id += 1

    return pd.DataFrame(rows)


def generate_source_data() -> dict[str, int]:
    """Generate all source CSV files and return row counts per dataset."""
    ensure_directories()

    students = _generate_students()
    courses = _generate_courses()
    grades = _generate_grades(students, courses)
    assignments = _generate_assignments(students, courses)
    lms_activity = _generate_lms_activity(students)
    rooms = _generate_rooms()
    room_events = _generate_room_events(students, rooms)

    datasets = {
        "students.csv": students,
        "courses.csv": courses,
        "grades.csv": grades,
        "assignments.csv": assignments,
        "lms_activity.csv": lms_activity,
        "rooms.csv": rooms,
        "room_events.csv": room_events,
    }

    counts: dict[str, int] = {}
    for filename, df in datasets.items():
        path = SOURCE_DIR / filename
        df.to_csv(path, index=False)
        counts[filename] = len(df)
        print(f"  Generated {filename}: {len(df)} rows")

    return counts


if __name__ == "__main__":
    generate_source_data()
