"""
scheduler.py

Implements the Best-Fit Greedy Scheduling Algorithm for the
Meeting Room Allocation System.

Algorithm overview
-------------------
1. Sort rooms by capacity (ascending).
2. Sort meetings chronologically by precomputed start minute.
3. Use bisect_left() to skip rooms that are too small, then scan feasible
   rooms from smallest to largest to preserve best-fit greedy behavior.
4. Keep each room's bookings sorted by start minute and use binary search to
   check only the neighboring bookings that can overlap.
5. If no suitable room is found, record the meeting as a conflict.

Complexity
----------
Let M be meetings, R be rooms, F be the number of capacity-feasible rooms
checked for a meeting, and B be bookings in a checked room.

Sorting costs O(R log R + M log M). Allocation costs
O(sum(F * log B)) after the O(log R) capacity lower-bound lookup for each
meeting. Worst case remains O(M * R * log M), but the previous linear booking
scan O(B) is reduced to O(log B), and undersized rooms are skipped with binary
search instead of repeated per-room checks. Memory is O(R + M).
"""

from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, DefaultDict, List, Sequence, Tuple

import pandas as pd


@dataclass(frozen=True)
class RoomOption:
    """A compact room record avoids repeated pandas row access in hot loops."""

    room_id: Any
    capacity: int


@dataclass(frozen=True)
class MeetingRequest:
    """A compact meeting record caches fields used repeatedly by allocation."""

    meeting_id: Any
    department: Any
    attendees: int
    time_slot: str
    start_time: Any
    end_time: Any
    start_minutes: int
    end_minutes: int


def _time_to_minutes(value):
    """Fallback for older DataFrames that do not yet include minute columns."""
    return value.hour * 60 + value.minute


def _meeting_records(meetings_df):
    """
    Convert meeting rows once before scheduling.

    This avoids repeated Series lookups inside the allocation loop and keeps
    backward compatibility with DataFrames created before start_minutes and
    end_minutes were added by the parser.
    """
    if meetings_df is None or meetings_df.empty:
        return []

    records = meetings_df.sort_values(by="start_time", ascending=True).to_dict("records")
    meetings = []
    for record in records:
        start_minutes = record.get("start_minutes")
        end_minutes = record.get("end_minutes")
        if start_minutes is None or pd.isna(start_minutes):
            start_minutes = _time_to_minutes(record["start_time"])
        if end_minutes is None or pd.isna(end_minutes):
            end_minutes = _time_to_minutes(record["end_time"])

        meetings.append(
            MeetingRequest(
                meeting_id=record["meeting_id"],
                department=record["department"],
                attendees=int(record["attendees"]),
                time_slot=record["time_slot"],
                start_time=record["start_time"],
                end_time=record["end_time"],
                start_minutes=int(start_minutes),
                end_minutes=int(end_minutes),
            )
        )
    return meetings


def _room_options(rooms_df):
    """Sort rooms once and expose parallel capacities for bisect_left()."""
    rooms_sorted = rooms_df.sort_values(by="capacity", ascending=True)
    rooms = [
        RoomOption(room_id=record["room_id"], capacity=int(record["capacity"]))
        for record in rooms_sorted.to_dict("records")
    ]
    capacities = [room.capacity for room in rooms]
    return rooms, capacities


def _has_overlap(starts: Sequence[int], bookings: Sequence[Tuple[int, int]], start: int, end: int) -> bool:
    """
    Check overlap in O(log B) by inspecting only adjacent sorted bookings.

    In a start-sorted interval list, only the booking immediately before the
    insertion point and the booking at the insertion point can overlap a new
    interval. All earlier bookings end no later than the previous neighbor, and
    all later bookings start after the next neighbor.
    """
    insert_at = bisect_left(starts, start)

    if insert_at > 0 and bookings[insert_at - 1][1] > start:
        return True

    if insert_at < len(bookings) and bookings[insert_at][0] < end:
        return True

    return False


def _build_schedule_row(meeting, assigned_room, assigned_capacity, status):
    """Create a consistent schedule row for both successful and conflicted meetings."""
    return {
        "meeting_id": meeting.meeting_id,
        "department": meeting.department,
        "assigned_room": assigned_room,
        "attendees": meeting.attendees,
        "room_capacity": assigned_capacity,
        "time_slot": meeting.time_slot,
        "start_time": meeting.start_time,
        "end_time": meeting.end_time,
        "start_minutes": meeting.start_minutes,
        "end_minutes": meeting.end_minutes,
        "status": status,
    }


def _build_conflict_row(meeting, reason):
    """Create a consistent conflict row for unscheduled meetings."""
    return {
        "meeting_id": meeting.meeting_id,
        "department": meeting.department,
        "attendees": meeting.attendees,
        "requested_time": meeting.time_slot,
        "reason": reason,
    }


def schedule_meetings(rooms_df, meetings_df):
    """
    Run the best-fit greedy scheduling algorithm.

    Parameters
    ----------
    rooms_df : pd.DataFrame
        Columns: room_id, capacity
    meetings_df : pd.DataFrame
        Columns: meeting_id, department, attendees, time_slot,
                 start_time, end_time, start_minutes, end_minutes

    Returns
    -------
    tuple(pd.DataFrame, pd.DataFrame)
        schedule_df  -> one row per meeting, with assigned room and status
        conflicts_df -> one row per unscheduled meeting, with a reason
    """
    schedule_rows = []
    conflict_rows = []

    if rooms_df is None or rooms_df.empty or meetings_df is None or meetings_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    rooms, capacities = _room_options(rooms_df)
    meetings = _meeting_records(meetings_df)
    max_capacity = capacities[-1] if capacities else 0

    # defaultdict removes repeated setup checks while preserving one sorted
    # booking list per room. Starts are kept separately for fast bisect lookups.
    room_bookings: DefaultDict[Any, List[Tuple[int, int]]] = defaultdict(list)
    room_booking_starts: DefaultDict[Any, List[int]] = defaultdict(list)

    for meeting in meetings:
        assigned_room = None
        assigned_capacity = None

        # Capacity lower-bound search skips every room that cannot ever fit the
        # meeting, while the following scan keeps the original best-fit order.
        first_feasible = bisect_left(capacities, meeting.attendees)

        for room in rooms[first_feasible:]:
            starts = room_booking_starts[room.room_id]
            bookings = room_bookings[room.room_id]

            if _has_overlap(starts, bookings, meeting.start_minutes, meeting.end_minutes):
                continue

            assigned_room = room.room_id
            assigned_capacity = room.capacity
            break

        if assigned_room is not None:
            # Meetings are processed by nondecreasing start time, so appending
            # keeps each room schedule sorted without paying O(B) insertion cost.
            room_bookings[assigned_room].append((meeting.start_minutes, meeting.end_minutes))
            room_booking_starts[assigned_room].append(meeting.start_minutes)
            schedule_rows.append(
                _build_schedule_row(
                    meeting,
                    assigned_room,
                    assigned_capacity,
                    "Scheduled",
                )
            )
        else:
            reason = _determine_conflict_reason(meeting, first_feasible < len(rooms), max_capacity)
            conflict_rows.append(_build_conflict_row(meeting, reason))
            schedule_rows.append(
                _build_schedule_row(
                    meeting,
                    "N/A",
                    None,
                    "Conflict",
                )
            )

    schedule_df = pd.DataFrame(schedule_rows)
    conflicts_df = pd.DataFrame(conflict_rows)

    return schedule_df, conflicts_df


def _determine_conflict_reason(meeting, has_fitting_room, max_capacity):
    """Build a human-readable explanation without rescanning room data."""
    if not has_fitting_room:
        return (
            f"No room has sufficient capacity ({meeting.attendees} attendees "
            f"requested, largest room holds {max_capacity})."
        )

    return (
        f"All rooms large enough for {meeting.attendees} attendees were "
        f"already booked during {meeting.time_slot}."
    )


def detect_conflicts(schedule_df):
    """
    Independent verification pass over a generated schedule.

    Confirms that no two 'Scheduled' meetings assigned to the same room
    have overlapping time slots. This acts as a safety net / sanity check
    on top of the allocation performed in schedule_meetings().

    Complexity: O(S log S) for S scheduled meetings due to sorting, then O(S)
    for adjacent interval checks. Memory is O(S) for record conversion.

    Parameters
    ----------
    schedule_df : pd.DataFrame
        Output of schedule_meetings() (the schedule_df return value).

    Returns
    -------
    list[str]
        Descriptions of any double-booking issues found. Empty if the
        schedule is internally consistent.
    """
    issues = []

    if schedule_df is None or schedule_df.empty:
        return issues

    scheduled = schedule_df[schedule_df["status"] == "Scheduled"].copy()
    if scheduled.empty:
        return issues

    # Minute columns make conflict verification integer-based. The fallback
    # keeps compatibility with schedules produced before this optimization.
    if "start_minutes" not in scheduled.columns:
        scheduled["start_minutes"] = scheduled["start_time"].map(_time_to_minutes)
    if "end_minutes" not in scheduled.columns:
        scheduled["end_minutes"] = scheduled["end_time"].map(_time_to_minutes)

    scheduled = scheduled.sort_values(["assigned_room", "start_minutes"])

    for room_id, group in scheduled.groupby("assigned_room", sort=False):
        rows = group.to_dict("records")
        for current_row, next_row in zip(rows, rows[1:]):
            if int(current_row["end_minutes"]) > int(next_row["start_minutes"]):
                issues.append(
                    f"Room {room_id}: '{current_row['meeting_id']}' overlaps "
                    f"with '{next_row['meeting_id']}'."
                )

    return issues
