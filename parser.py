"""
parser.py

Handles parsing and validation of the raw .txt dataset used by the
Meeting Room Allocation System.

The expected dataset format is:

    ROOMS
    R101,20
    R102,10
    R103,50

    MEETINGS
    M001,HR,15,09:00-10:00
    M002,Finance,8,09:00-10:00
    ...

Two entry points are provided:

    parse_dataset(raw_text)      -> (rooms_df, meetings_df, parse_errors)
    validate_dataset(rooms, meetings) -> list of higher-level validation errors
"""

from datetime import datetime

import pandas as pd


def _parse_hhmm(value):
    """
    Parse one HH:MM token into integer minutes.

    The scheduler compares time ranges many times, so parsing once into a
    compact integer avoids repeated datetime arithmetic during allocation.
    """
    hour_str, minute_str = value.strip().split(":")
    hour = int(hour_str)
    minute = int(minute_str)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError
    return hour * 60 + minute


def _minutes_to_datetime(minutes):
    """Keep the existing arbitrary-date datetime output used by Plotly charts."""
    return datetime(1900, 1, 1, minutes // 60, minutes % 60)


def parse_time_range(time_str):
    """
    Parse a 'HH:MM-HH:MM' string into datetimes and integer minute offsets.

    Returns (start, end, start_minutes, end_minutes) or
    (None, None, None, None) if the string is malformed.
    """
    try:
        start_str, end_str = time_str.split("-")
        start_minutes = _parse_hhmm(start_str)
        end_minutes = _parse_hhmm(end_str)
        start = _minutes_to_datetime(start_minutes)
        end = _minutes_to_datetime(end_minutes)
        return start, end, start_minutes, end_minutes
    except (ValueError, AttributeError):
        return None, None, None, None


def parse_dataset(raw_text):
    """
    Parse the raw dataset text into rooms and meetings DataFrames.

    Complexity: O(N), where N is the number of non-empty dataset lines.
    Memory: O(R + M) for parsed rooms and meetings.

    Parameters
    ----------
    raw_text : str
        Full contents of the uploaded .txt file.

    Returns
    -------
    tuple(pd.DataFrame, pd.DataFrame, list[str])
        rooms_df   -> columns: room_id, capacity
        meetings_df-> columns: meeting_id, department, attendees,
                                time_slot, start_time, end_time,
                                start_minutes, end_minutes
        errors     -> list of human-readable parsing error messages
    """
    errors = []
    rooms = []
    meetings = []

    if raw_text is None or not raw_text.strip():
        return pd.DataFrame(), pd.DataFrame(), ["The uploaded file is empty."]

    lines = [line.strip() for line in raw_text.splitlines()]
    section = None

    seen_room_ids = set()
    seen_meeting_ids = set()

    for line_no, line in enumerate(lines, start=1):
        if not line:
            continue

        upper = line.upper()
        if upper == "ROOMS":
            section = "ROOMS"
            continue
        if upper == "MEETINGS":
            section = "MEETINGS"
            continue

        if section == "ROOMS":
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 2:
                errors.append(
                    f"Line {line_no}: Invalid room entry '{line}' "
                    "(expected format: RoomID,Capacity)"
                )
                continue

            room_id, capacity_str = parts

            if not room_id:
                errors.append(f"Line {line_no}: Missing room ID.")
                continue

            if room_id in seen_room_ids:
                errors.append(f"Line {line_no}: Duplicate room ID '{room_id}'.")
                continue

            try:
                capacity = int(capacity_str)
                if capacity <= 0:
                    raise ValueError
            except ValueError:
                errors.append(
                    f"Line {line_no}: Invalid capacity '{capacity_str}' for room "
                    f"'{room_id}' (must be a positive integer)."
                )
                continue

            seen_room_ids.add(room_id)
            rooms.append({"room_id": room_id, "capacity": capacity})

        elif section == "MEETINGS":
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 4:
                errors.append(
                    f"Line {line_no}: Invalid meeting entry '{line}' "
                    "(expected format: MeetingID,Department,Attendees,Time)"
                )
                continue

            meeting_id, department, attendees_str, time_str = parts

            if not meeting_id:
                errors.append(f"Line {line_no}: Missing meeting ID.")
                continue

            if not department:
                errors.append(
                    f"Line {line_no}: Missing department for meeting '{meeting_id}'."
                )
                continue

            if meeting_id in seen_meeting_ids:
                errors.append(f"Line {line_no}: Duplicate meeting ID '{meeting_id}'.")
                continue

            try:
                attendees = int(attendees_str)
                if attendees <= 0:
                    raise ValueError
            except ValueError:
                errors.append(
                    f"Line {line_no}: Invalid attendee count '{attendees_str}' for "
                    f"meeting '{meeting_id}' (must be a positive integer)."
                )
                continue

            start, end, start_minutes, end_minutes = parse_time_range(time_str)
            if start is None or end is None:
                errors.append(
                    f"Line {line_no}: Invalid time format '{time_str}' for meeting "
                    f"'{meeting_id}' (expected format: HH:MM-HH:MM)."
                )
                continue

            if end_minutes <= start_minutes:
                errors.append(
                    f"Line {line_no}: End time must be after start time for meeting "
                    f"'{meeting_id}'."
                )
                continue

            seen_meeting_ids.add(meeting_id)
            meetings.append(
                {
                    "meeting_id": meeting_id,
                    "department": department,
                    "attendees": attendees,
                    "time_slot": time_str,
                    "start_time": start,
                    "end_time": end,
                    "start_minutes": start_minutes,
                    "end_minutes": end_minutes,
                }
            )

        else:
            errors.append(
                f"Line {line_no}: Data found outside of ROOMS/MEETINGS sections: "
                f"'{line}'."
            )

    rooms_df = pd.DataFrame(rooms, columns=["room_id", "capacity"])
    meetings_df = pd.DataFrame(
        meetings,
        columns=[
            "meeting_id",
            "department",
            "attendees",
            "time_slot",
            "start_time",
            "end_time",
            "start_minutes",
            "end_minutes",
        ],
    )

    return rooms_df, meetings_df, errors


def validate_dataset(rooms_df, meetings_df):
    """
    Perform dataset-level (cross-record) validation after initial parsing.

    Complexity: O(M), after O(1) max-capacity lookup from the rooms DataFrame.
    Memory: O(K), where K is the number of validation messages returned.

    Parameters
    ----------
    rooms_df : pd.DataFrame
    meetings_df : pd.DataFrame

    Returns
    -------
    list[str]
        Human-readable validation error / warning messages.
    """
    errors = []

    if rooms_df is None or rooms_df.empty:
        errors.append("No valid rooms were found in the dataset.")

    if meetings_df is None or meetings_df.empty:
        errors.append("No valid meetings were found in the dataset.")

    if (
        rooms_df is not None
        and not rooms_df.empty
        and meetings_df is not None
        and not meetings_df.empty
    ):
        max_capacity = rooms_df["capacity"].max()
        oversized = meetings_df[meetings_df["attendees"] > max_capacity]
        for _, row in oversized.iterrows():
            errors.append(
                f"Meeting '{row['meeting_id']}' requests {row['attendees']} "
                f"attendees, which exceeds the largest available room capacity "
                f"of {max_capacity}."
            )

    return errors
