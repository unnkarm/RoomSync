"""
scheduler.py

Implements the Best-Fit Greedy Scheduling Algorithm for the
Meeting Room Allocation System.

Algorithm overview
-------------------
1. Sort rooms by capacity (ascending).
2. Sort meetings chronologically by start time.
3. For each meeting, scan rooms from smallest to largest capacity and
   assign the first (smallest) room that:
       a) has capacity >= number of attendees, and
       b) has no existing booking that overlaps the meeting's time slot.
4. If no suitable room is found, the meeting is recorded as a conflict
   with a reason.

With M meetings and R rooms, each meeting scans at most R rooms, and for
each room checks its existing bookings (bounded by M in the worst case),
giving an approximate O(M x R) time complexity for the allocation pass.
"""

import pandas as pd


def _overlaps(start1, end1, start2, end2):
    """Return True if time range [start1, end1) overlaps [start2, end2)."""
    return start1 < end2 and start2 < end1


def schedule_meetings(rooms_df, meetings_df):
    """
    Run the best-fit greedy scheduling algorithm.

    Parameters
    ----------
    rooms_df : pd.DataFrame
        Columns: room_id, capacity
    meetings_df : pd.DataFrame
        Columns: meeting_id, department, attendees, time_slot,
                 start_time, end_time

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

    rooms_sorted = rooms_df.sort_values(by="capacity", ascending=True).reset_index(
        drop=True
    )
    meetings_sorted = meetings_df.sort_values(
        by="start_time", ascending=True
    ).reset_index(drop=True)

    # Track bookings per room as a list of (start, end) tuples.
    room_bookings = {room_id: [] for room_id in rooms_sorted["room_id"]}

    for _, meeting in meetings_sorted.iterrows():
        assigned_room = None
        assigned_capacity = None

        for _, room in rooms_sorted.iterrows():
            if room["capacity"] < meeting["attendees"]:
                continue

            has_conflict = any(
                _overlaps(meeting["start_time"], meeting["end_time"], b_start, b_end)
                for (b_start, b_end) in room_bookings[room["room_id"]]
            )

            if not has_conflict:
                assigned_room = room["room_id"]
                assigned_capacity = room["capacity"]
                break

        if assigned_room is not None:
            room_bookings[assigned_room].append(
                (meeting["start_time"], meeting["end_time"])
            )
            schedule_rows.append(
                {
                    "meeting_id": meeting["meeting_id"],
                    "department": meeting["department"],
                    "assigned_room": assigned_room,
                    "attendees": meeting["attendees"],
                    "room_capacity": assigned_capacity,
                    "time_slot": meeting["time_slot"],
                    "start_time": meeting["start_time"],
                    "end_time": meeting["end_time"],
                    "status": "Scheduled",
                }
            )
        else:
            reason = _determine_conflict_reason(meeting, rooms_sorted)
            conflict_rows.append(
                {
                    "meeting_id": meeting["meeting_id"],
                    "department": meeting["department"],
                    "attendees": meeting["attendees"],
                    "requested_time": meeting["time_slot"],
                    "reason": reason,
                }
            )
            schedule_rows.append(
                {
                    "meeting_id": meeting["meeting_id"],
                    "department": meeting["department"],
                    "assigned_room": "N/A",
                    "attendees": meeting["attendees"],
                    "room_capacity": None,
                    "time_slot": meeting["time_slot"],
                    "start_time": meeting["start_time"],
                    "end_time": meeting["end_time"],
                    "status": "Conflict",
                }
            )

    schedule_df = pd.DataFrame(schedule_rows)
    conflicts_df = pd.DataFrame(conflict_rows)

    return schedule_df, conflicts_df


def _determine_conflict_reason(meeting, rooms_sorted):
    """Build a human-readable explanation for why a meeting could not be scheduled."""
    fitting_rooms = rooms_sorted[rooms_sorted["capacity"] >= meeting["attendees"]]

    if fitting_rooms.empty:
        max_cap = rooms_sorted["capacity"].max()
        return (
            f"No room has sufficient capacity ({meeting['attendees']} attendees "
            f"requested, largest room holds {max_cap})."
        )

    return (
        f"All rooms large enough for {meeting['attendees']} attendees were "
        f"already booked during {meeting['time_slot']}."
    )


def detect_conflicts(schedule_df):
    """
    Independent verification pass over a generated schedule.

    Confirms that no two 'Scheduled' meetings assigned to the same room
    have overlapping time slots. This acts as a safety net / sanity check
    on top of the allocation performed in schedule_meetings().

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

    scheduled = schedule_df[schedule_df["status"] == "Scheduled"]

    for room_id, group in scheduled.groupby("assigned_room"):
        group = group.sort_values("start_time")
        rows = group.to_dict("records")
        for i in range(len(rows) - 1):
            current_row = rows[i]
            next_row = rows[i + 1]
            if current_row["end_time"] > next_row["start_time"]:
                issues.append(
                    f"Room {room_id}: '{current_row['meeting_id']}' overlaps "
                    f"with '{next_row['meeting_id']}'."
                )

    return issues
