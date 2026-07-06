# Meeting Room Allocation System

A clean, dark-themed, single-user Streamlit dashboard that automatically
assigns meeting rooms to meeting requests using a **Best-Fit Greedy
Scheduling Algorithm**, then visualizes the resulting schedule with
Plotly charts and analytics.

No database, no authentication, no external services — everything runs
locally from a single `.txt` dataset.

---

## Project Overview

You upload a plain-text dataset describing available rooms and requested
meetings. The app parses and validates the data, runs a greedy allocation
algorithm that avoids double-booking rooms, and gives you:

- A live dashboard with key scheduling metrics
- A sortable/searchable schedule table (color-coded by status)
- A conflict table explaining why any meeting couldn't be placed
- Six Plotly visualizations of the schedule
- A block of derived analytics (utilization, peak hour, success rate, etc.)
- A one-click CSV export of the final schedule

---

## Features

- 📂 **Upload-driven** — no manual data entry, just drop in a `.txt` file
- ✅ **Robust validation** — invalid rooms, capacities, times, IDs, and
  duplicate entries are caught with friendly error messages
- ⚡ **Best-Fit Greedy Algorithm** — approx. `O(M × R)` allocation that
  always tries the smallest sufficient room first
- 📊 **Six chart types** — pie, bar, horizontal bar, donut, timeline,
  and heatmap, all in a matching dark theme
- 🧮 **Derived analytics** — most/least occupied room, average
  utilization, unused capacity, peak hour, top department, success and
  conflict rates
- 🔎 **Sortable & searchable schedule table** with green/red status
  coding
- ⬇ **CSV export** of the generated schedule
- 🎨 **Pure black dark theme** with an electric-cyan accent throughout

---

## Screenshots

![Dashboard view 1](docs/Screenshot%202026-07-06%20092920.png)

![Dashboard view 2](docs/Screenshot%202026-07-06%20092954.png)

![Dashboard view 3](docs/Screenshot%202026-07-06%20093009.png)

![Dashboard view 4](docs/Screenshot%202026-07-06%20093035.png)

---

## Installation

1. Clone or download this project folder.
2. (Recommended) create a virtual environment:

   ```bash
   & "C:\Users\HP\AppData\Local\Programs\Python\Python310\python.exe" -m venv .venv
   .venv\Scripts\Activate.ps1   # Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Running Locally

From the project directory:

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints in your terminal (usually
`http://localhost:8501`).

1. Upload a `.txt` dataset from the sidebar (or use `sample_dataset.txt`
   included in this repo).
2. Click **⚡ Generate Schedule**.
3. Explore the dashboard, charts, and analytics.
4. Click **⬇ Download Schedule CSV** to export the results.
5. Click **↺ Reset** to start over with a new dataset.

---

## Sample Dataset

`sample_dataset.txt` is included and looks like this:

```text
ROOMS
R101,20
R102,10
R103,50

MEETINGS
M001,HR,15,09:00-10:00
M002,Finance,8,09:00-10:00
M003,Engineering,45,10:00-11:00
M004,Marketing,18,09:30-10:30
M005,Sales,12,11:00-12:00
```

**Format rules:**

- The file has two sections, `ROOMS` and `MEETINGS`, each on its own line.
- Room rows: `RoomID,Capacity` (capacity must be a positive integer).
- Meeting rows: `MeetingID,Department,Attendees,StartTime-EndTime`
  (times in 24-hour `HH:MM` format).
- Blank lines are ignored; IDs must be unique.

---

## Scheduling Algorithm Explanation

The allocator uses a **Best-Fit Greedy** strategy:

1. **Sort rooms by capacity**, ascending — smallest room first.
2. **Sort meetings chronologically** by start time.
3. For each meeting, walk through the sorted rooms and assign the
   **first (smallest) room** that:
   - has capacity ≥ the meeting's attendee count, **and**
   - has no existing booking that overlaps the meeting's time slot.
4. If no room satisfies both conditions, the meeting is recorded as a
   **conflict**, along with a specific reason (either "no room large
   enough exists" or "all suitable rooms are already booked").

This greedy approach keeps larger rooms free for meetings that actually
need them. The optimized implementation sorts rooms and meetings in
**O(R log R + M log M)**, uses binary search to skip undersized rooms,
and checks room booking overlaps in **O(log B)** for `B` bookings in a
candidate room. Worst-case allocation can still scan many feasible rooms,
but it avoids the previous linear booking scan.

A secondary consistency check (`detect_conflicts` in `scheduler.py`)
independently re-scans the final schedule to confirm no room ended up
double-booked, acting as a safety net on top of the allocation pass.

---

## Project Structure

```text
meeting-room-allocator/
│── app.py                # Streamlit UI, dashboard, charts, analytics
│── scheduler.py           # schedule_meetings(), detect_conflicts()
│── parser.py              # parse_dataset(), validate_dataset()
│── sample_dataset.txt     # Example dataset
│── requirements.txt
│── README.md
```

---

## Future Improvements

- Support recurring meetings and multi-day scheduling
- Allow manual drag-and-drop reassignment of conflicted meetings
- Add room amenities/equipment matching (projector, video conferencing)
- Persist datasets and schedules between sessions (optional local DB)
- Support CSV/JSON dataset uploads in addition to `.txt`
- Add per-department utilization breakdowns and cost estimates

## Deployed Link 
https://roomsync-kz93vdlj3ritgr7pnnc9v3.streamlit.app/
