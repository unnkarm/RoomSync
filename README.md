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

The allocator now uses an **Optimized Best-Fit Greedy** strategy with
capacity buckets, a min-heap for idle-room tracking, and binary-search-based
overlap checks.

1. **Sort rooms by capacity** and group them into capacity buckets.
2. **Sort meetings chronologically** by start time.
3. For each meeting, find the **smallest sufficient capacity bucket**
   that can fit the attendees.
4. Within that bucket, use the heap/booking structure to quickly find a
   room whose previous bookings have already finished before the new
   meeting starts.
5. If no room satisfies both capacity and overlap constraints, the meeting
   is marked as a **conflict** with a reason such as insufficient room
   capacity or all suitable rooms already being booked.

### Latest algorithm

The current implementation in `scheduler.py` is a **capacity-indexed
best-fit greedy scheduler**. It is deterministic, fast for interactive use,
and preserves a clear explanation of why each meeting was assigned or rejected.

### Latest time complexity

The full scheduling pipeline now runs in approximately:

- **O(R log R)** for room preprocessing and ordering
- **O(M log M)** for meeting preprocessing and chronological sorting
- **O(M log R)** for the allocation loop in practice

So the latest overall time complexity is:

**O(R log R + M log M + M log R)**

### Latest space complexity

The scheduler uses:

- **O(R + M)** space for the room state, meeting records, and schedule/conflict
  outputs

If you include the dashboard heatmap/visualization layer, the UI can use
additional temporary space proportional to the displayed time grid, but the
core scheduling logic remains **O(R + M)**.

### Three strong approaches for this problem

| Approach | Core idea | Time complexity | Space complexity | Why it works / trade-off |
| --- | --- | --- | --- | --- |
| Optimized Best-Fit Greedy (chosen) | Assign each meeting to the smallest feasible room while avoiding overlaps | O(R log R + M log M + M log R) | O(R + M) | Fast, deterministic, and easy to explain; ideal for a live dashboard and large practical datasets. |
| Integer Programming / CP-SAT | Model each meeting-room assignment as a binary decision and enforce capacity/overlap constraints | Exponential worst-case, often practical for small/medium instances | O(V + E) for the model size | Gives exact optimum when needed, but is slower and heavier for interactive use. |
| Graph-based / Flow-based scheduling | Treat meetings as intervals and rooms as resources in a conflict graph or network flow model | Roughly O(M^2) for simple graph formulations, or higher for flow implementations | O(M + R) to O(VE) depending on formulation | Strong for structured variants, but more complex to implement and less natural for arbitrary meeting lengths and room capacities. |

### Why this method was selected

The **optimized best-fit greedy** approach was chosen because it offers the
best trade-off for this project:

- it produces high-quality schedules quickly,
- it is easy to reason about and maintain,
- it scales well for interactive Streamlit usage,
- and it keeps the implementation simple enough for a single-user local app.

A secondary consistency check (`detect_conflicts` in `scheduler.py`)
independently re-scans the final schedule to confirm that no room ended up
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
