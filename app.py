"""
app.py

Meeting Room Allocation System
-------------------------------
A single-page, dark-themed Streamlit dashboard that ingests a plain-text
dataset of rooms and meetings, runs a best-fit greedy scheduling algorithm,
and visualizes the resulting conflict-free schedule with Plotly.

Run with:
    streamlit run app.py
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from parser import parse_dataset, validate_dataset
from scheduler import detect_conflicts, schedule_meetings

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RoomSync",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
BG = "#000000"
TEXT = "#FFFFFF"
MUTED = "#777777"
BORDER = "#1a1a1a"
ACCENT = "#00E5FF"
GREEN = "#22C55E"
GREEN_SOFT = "rgba(34, 197, 94, 0.14)"
RED = "#EF4444"
RED_SOFT = "rgba(239, 68, 68, 0.14)"

PLOTLY_TEMPLATE = "plotly_dark"
CHART_COLORWAY = [ACCENT, "#7C4DFF", GREEN, "#FFB020", RED, "#3D5AFE"]


def inject_css():
    """Inject global dark-theme CSS overrides."""
    st.markdown(
        f"""
        <style>
        #MainMenu, footer, header[data-testid="stHeader"] {{
            visibility: hidden;
            height: 0;
        }}
        html, body, [data-testid="stAppViewContainer"], .main,
        [data-testid="stAppViewContainer"] > section,
        .block-container, [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child {{
            background-color: {BG} !important;
            color: {TEXT} !important;
        }}
        [data-testid="stSidebar"] {{
            border-right: 1px solid {BORDER};
        }}
        .block-container {{
            padding-top: 2rem;
            max-width: 1100px;
        }}
        h1 {{
            color: {TEXT} !important;
            font-size: 3rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em;
            line-height: 1.1 !important;
            margin-bottom: 0.4rem !important;
        }}
        h2, h3 {{
            color: {TEXT} !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em;
        }}
        h2 {{ font-size: 2rem !important; }}
        h3 {{ font-size: 1.4rem !important; }}
        .main p, .main span, .main label, .main li,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {{
            color: {TEXT};
        }}
        .app-subtitle {{
            color: {MUTED};
            font-size: 1rem;
            margin-top: 0;
            margin-bottom: 2.5rem;
            font-weight: 400;
        }}
        .section-title {{
            font-size: 2rem;
            font-weight: 700;
            margin: 3rem 0 1.2rem 0;
            color: {TEXT};
            letter-spacing: -0.02em;
        }}
        .metric-card {{
            background: transparent;
            border: none;
            padding: 0.5rem 0;
            height: 100%;
        }}
        .metric-label {{
            color: {MUTED};
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.4rem;
        }}
        .metric-value {{
            color: {TEXT};
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.02em;
        }}
        .info-card {{
            background: transparent;
            border: none;
            padding: 0.5rem 0;
            margin-bottom: 0.5rem;
        }}
        .info-card .label {{
            color: {MUTED};
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        .info-card .value {{
            color: {TEXT};
            font-size: 1.6rem;
            font-weight: 700;
            margin-top: 0.2rem;
            letter-spacing: -0.02em;
        }}
        [data-testid="stDataFrame"] {{
            border: none;
            border-top: 1px solid {BORDER};
        }}
        .stButton > button {{
            background-color: transparent;
            color: {TEXT} !important;
            border: 1px solid {BORDER};
            border-radius: 0;
            font-weight: 600;
            padding: 0.6rem 1rem;
            width: 100%;
        }}
        .stButton > button:hover {{
            border-color: {TEXT};
            background-color: transparent;
            color: {TEXT} !important;
        }}
        .stButton > button:disabled {{
            background-color: transparent;
            color: {MUTED} !important;
            border-color: {BORDER};
            opacity: 0.6;
        }}
        .stButton > button p,
        .stButton > button span,
        .stButton > button div {{
            color: inherit !important;
        }}
        .stDownloadButton > button {{
            background-color: transparent;
            color: {TEXT} !important;
            border: 1px solid {BORDER};
            border-radius: 0;
            font-weight: 500;
            width: 100%;
        }}
        .stDownloadButton > button:hover {{
            border-color: {TEXT};
            color: {TEXT} !important;
        }}
        .stDownloadButton > button:disabled {{
            color: {MUTED} !important;
            border-color: {BORDER};
            opacity: 0.6;
        }}
        .stDownloadButton > button p,
        .stDownloadButton > button span,
        .stDownloadButton > button div {{
            color: inherit !important;
        }}
        [data-testid="stFileUploader"] {{
            background-color: transparent;
            border: 1px dashed {BORDER};
            border-radius: 0;
            padding: 0.5rem;
        }}
        [data-testid="stFileUploader"] label,
        [data-testid="stFileUploader"] span,
        [data-testid="stFileUploader"] small {{
            color: {TEXT} !important;
        }}
        [data-testid="stFileUploader"] button {{
            background-color: transparent !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER} !important;
        }}
        [data-testid="stTextInput"] input {{
            background-color: {BG} !important;
            color: {TEXT} !important;
            border: 1px solid {BORDER};
            border-radius: 0;
        }}
        [data-testid="stTextInput"] label {{
            color: {MUTED} !important;
        }}
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary span {{
            color: {TEXT} !important;
        }}
        hr {{
            border: none;
            border-top: 1px solid {BORDER};
            margin: 1.5rem 0;
        }}
        [data-testid="stAlert"] {{
            background-color: transparent;
            border: 1px solid {BORDER};
            border-radius: 0;
            color: {TEXT};
        }}
        [data-testid="stExpander"] {{
            border: none;
            border-top: 1px solid {BORDER};
            border-radius: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
def init_session_state():
    defaults = {
        "rooms_df": None,
        "meetings_df": None,
        "schedule_df": None,
        "conflicts_df": None,
        "parse_errors": [],
        "validation_errors": [],
        "generated": False,
        "raw_text": None,
        "uploaded_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_all():
    for key in [
        "rooms_df",
        "meetings_df",
        "schedule_df",
        "conflicts_df",
        "parse_errors",
        "validation_errors",
        "generated",
        "raw_text",
        "uploaded_name",
    ]:
        st.session_state[key] = None if key != "generated" else False
    st.session_state["parse_errors"] = []
    st.session_state["validation_errors"] = []


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("### Dataset")
        uploaded_file = st.file_uploader(
            "Upload dataset (.txt)", type=["txt"], key="uploader"
        )

        if uploaded_file is not None:
            raw_text = uploaded_file.read().decode("utf-8", errors="replace")
            if raw_text != st.session_state.get("raw_text") or uploaded_file.name != st.session_state.get(
                "uploaded_name"
            ):
                st.session_state["raw_text"] = raw_text
                st.session_state["uploaded_name"] = uploaded_file.name
                rooms_df, meetings_df, parse_errors = parse_dataset(raw_text)
                validation_errors = validate_dataset(rooms_df, meetings_df)
                st.session_state["rooms_df"] = rooms_df
                st.session_state["meetings_df"] = meetings_df
                st.session_state["parse_errors"] = parse_errors
                st.session_state["validation_errors"] = validation_errors
                st.session_state["generated"] = False
                st.session_state["schedule_df"] = None
                st.session_state["conflicts_df"] = None

        st.markdown("---")

        can_generate = (
            st.session_state.get("rooms_df") is not None
            and not st.session_state["rooms_df"].empty
            and st.session_state.get("meetings_df") is not None
            and not st.session_state["meetings_df"].empty
            and len(st.session_state.get("parse_errors", [])) == 0
        )

        if st.button("Generate Schedule", disabled=not can_generate):
            schedule_df, conflicts_df = schedule_meetings(
                st.session_state["rooms_df"], st.session_state["meetings_df"]
            )
            st.session_state["schedule_df"] = schedule_df
            st.session_state["conflicts_df"] = conflicts_df
            st.session_state["generated"] = True

        if st.button("Reset"):
            reset_all()
            st.rerun()

        st.markdown("---")

        if st.session_state.get("generated") and st.session_state.get("schedule_df") is not None:
            export_df = build_export_dataframe(st.session_state["schedule_df"])
            csv_bytes = export_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Schedule CSV",
                data=csv_bytes,
                file_name="generated_schedule.csv",
                mime="text/csv",
            )
        else:
            st.download_button(
                "Download Schedule CSV", data="", file_name="generated_schedule.csv", disabled=True
            )

        st.markdown("---")

        with st.expander("Algorithm"):
            st.markdown(
                """
                **Best-Fit Greedy Scheduling**

                1. Rooms are sorted by capacity, smallest first.
                2. Meetings are processed in chronological order.
                3. Each meeting is assigned the *smallest* room that
                   fits its attendees and has no time overlap.
                4. Meetings that can't fit anywhere are marked as
                   **conflicts** with a reason.

                Complexity: sorting is **O(R log R + M log M)**;
                allocation uses capacity and booking binary searches.
                """
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_export_dataframe(schedule_df):
    """Prepare a clean, human-readable DataFrame for CSV export."""
    if schedule_df is None or schedule_df.empty:
        return pd.DataFrame()

    export_df = schedule_df.copy()
    export_df = export_df.rename(
        columns={
            "meeting_id": "Meeting ID",
            "department": "Department",
            "assigned_room": "Assigned Room",
            "attendees": "Attendees",
            "room_capacity": "Room Capacity",
            "time_slot": "Time Slot",
            "status": "Status",
        }
    )
    return export_df[
        [
            "Meeting ID",
            "Department",
            "Assigned Room",
            "Attendees",
            "Room Capacity",
            "Time Slot",
            "Status",
        ]
    ]


def style_schedule_table(schedule_df):
    """Apply green/red row coloring based on scheduling status."""

    def highlight(row):
        if row["Status"] == "Scheduled":
            return [f"background-color: {GREEN_SOFT}; color: {GREEN}"] * len(row)
        return [f"background-color: {RED_SOFT}; color: {RED}"] * len(row)

    display_df = schedule_df[
        [
            "meeting_id",
            "department",
            "assigned_room",
            "attendees",
            "room_capacity",
            "time_slot",
            "status",
        ]
    ].rename(
        columns={
            "meeting_id": "Meeting ID",
            "department": "Department",
            "assigned_room": "Assigned Room",
            "attendees": "Attendees",
            "room_capacity": "Capacity",
            "time_slot": "Time Slot",
            "status": "Status",
        }
    )

    return display_df.style.apply(highlight, axis=1)


def time_to_minutes(t):
    return t.hour * 60 + t.minute


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
def render_header():
    st.markdown("# Meeting Room Allocation")
    st.markdown(
        '<div class="app-subtitle">Conflict-free room scheduling</div>',
        unsafe_allow_html=True,
    )


def render_upload_errors():
    parse_errors = st.session_state.get("parse_errors", [])
    validation_errors = st.session_state.get("validation_errors", [])

    if parse_errors:
        with st.container():
            st.error(
                f"Found {len(parse_errors)} issue(s) while parsing the dataset:"
            )
            for err in parse_errors:
                st.markdown(f"- {err}")

    if validation_errors:
        with st.container():
            st.warning(
                f"Found {len(validation_errors)} validation issue(s):"
            )
            for err in validation_errors:
                st.markdown(f"- {err}")


def render_dataset_preview():
    rooms_df = st.session_state.get("rooms_df")
    meetings_df = st.session_state.get("meetings_df")

    if rooms_df is None or meetings_df is None:
        return
    if rooms_df.empty and meetings_df.empty:
        return

    st.markdown('<div class="section-title">Dataset Preview</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Rooms**")
        if not rooms_df.empty:
            st.dataframe(
                rooms_df.rename(columns={"room_id": "Room ID", "capacity": "Capacity"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No rooms parsed yet.")

    with col2:
        st.markdown("**Meetings**")
        if not meetings_df.empty:
            display = meetings_df[["meeting_id", "department", "attendees", "time_slot"]].rename(
                columns={
                    "meeting_id": "Meeting ID",
                    "department": "Department",
                    "attendees": "Attendees",
                    "time_slot": "Time Slot",
                }
            )
            st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.info("No meetings parsed yet.")


def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_metrics():
    rooms_df = st.session_state.get("rooms_df")
    meetings_df = st.session_state.get("meetings_df")
    schedule_df = st.session_state.get("schedule_df")

    total_rooms = len(rooms_df) if rooms_df is not None else 0
    total_meetings = len(meetings_df) if meetings_df is not None else 0

    if schedule_df is not None and not schedule_df.empty:
        scheduled_count = int((schedule_df["status"] == "Scheduled").sum())
        conflict_count = int((schedule_df["status"] == "Conflict").sum())
    else:
        scheduled_count = 0
        conflict_count = 0

    utilization = compute_room_utilization(rooms_df, schedule_df)
    avg_utilization = f"{utilization['utilization_pct'].mean():.1f}%" if not utilization.empty else "0.0%"

    st.markdown('<div class="section-title">Dashboard Metrics</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    with cols[0]:
        metric_card("Total Rooms", total_rooms)
    with cols[1]:
        metric_card("Total Meetings", total_meetings)
    with cols[2]:
        metric_card("Scheduled Meetings", scheduled_count)
    with cols[3]:
        metric_card("Conflicts", conflict_count)
    with cols[4]:
        metric_card("Room Utilization %", avg_utilization)


def compute_room_utilization(rooms_df, schedule_df):
    """
    Compute utilization percentage per room, defined as:
        (sum of booked minutes) / (span of the scheduling day in minutes)

    The "day span" is derived from the earliest start and latest end
    across all scheduled meetings, so utilization reflects how much of
    the *active* meeting window each room is occupied.

    Complexity: O(R + S), where R is rooms and S is scheduled meetings.
    Memory: O(R + S) for the grouped duration table and merged result.
    """
    if rooms_df is None or rooms_df.empty or schedule_df is None or schedule_df.empty:
        return pd.DataFrame(columns=["room_id", "capacity", "booked_minutes", "utilization_pct"])

    scheduled = schedule_df[schedule_df["status"] == "Scheduled"].copy()
    if scheduled.empty:
        result = rooms_df.copy()
        result["booked_minutes"] = 0
        result["utilization_pct"] = 0.0
        return result

    # Reuse parser-created minute offsets so utilization is computed with
    # vectorized integer math instead of per-row datetime subtraction.
    if "start_minutes" not in scheduled.columns:
        scheduled["start_minutes"] = scheduled["start_time"].map(time_to_minutes)
    if "end_minutes" not in scheduled.columns:
        scheduled["end_minutes"] = scheduled["end_time"].map(time_to_minutes)

    day_span_minutes = max(
        int(scheduled["end_minutes"].max()) - int(scheduled["start_minutes"].min()),
        1,
    )
    scheduled["booked_minutes"] = scheduled["end_minutes"] - scheduled["start_minutes"]

    booked_by_room = (
        scheduled.groupby("assigned_room", sort=False)["booked_minutes"]
        .sum()
        .rename_axis("room_id")
        .reset_index()
    )

    result = rooms_df.merge(booked_by_room, on="room_id", how="left")
    result["booked_minutes"] = result["booked_minutes"].fillna(0)
    result["utilization_pct"] = (result["booked_minutes"] / day_span_minutes * 100.0).clip(upper=100.0)
    return result[["room_id", "capacity", "booked_minutes", "utilization_pct"]]


def render_schedule_table():
    schedule_df = st.session_state.get("schedule_df")
    if schedule_df is None or schedule_df.empty:
        return

    st.markdown('<div class="section-title">Schedule Table</div>', unsafe_allow_html=True)

    search_term = st.text_input(
        "Search schedule", key="schedule_search"
    )

    display_df = schedule_df.copy()
    if search_term:
        mask = (
            display_df["meeting_id"].astype(str).str.contains(search_term, case=False, na=False)
            | display_df["department"].astype(str).str.contains(search_term, case=False, na=False)
            | display_df["assigned_room"].astype(str).str.contains(search_term, case=False, na=False)
            | display_df["status"].astype(str).str.contains(search_term, case=False, na=False)
        )
        display_df = display_df[mask]

    if display_df.empty:
        st.info("No rows match your search.")
        return

    styled = style_schedule_table(display_df)
    st.dataframe(styled, use_container_width=True, hide_index=True)


def render_conflict_table():
    conflicts_df = st.session_state.get("conflicts_df")
    if conflicts_df is None:
        return

    st.markdown('<div class="section-title">Conflict Table</div>', unsafe_allow_html=True)

    if conflicts_df.empty:
        st.success("No conflicts — every meeting was successfully scheduled.")
        return

    display = conflicts_df.rename(
        columns={
            "meeting_id": "Meeting ID",
            "department": "Department",
            "requested_time": "Requested Time",
            "reason": "Reason",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------
def apply_dark_layout(fig, title=None):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, size=11),
        colorway=CHART_COLORWAY,
        title=dict(text=title, font=dict(size=18, color=TEXT)) if title else None,
        margin=dict(l=20, r=10, t=45 if title else 15, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, zerolinecolor=BORDER),
    )
    return fig


def render_charts():
    schedule_df = st.session_state.get("schedule_df")
    rooms_df = st.session_state.get("rooms_df")

    if schedule_df is None or schedule_df.empty:
        return

    st.markdown('<div class="section-title">Visualizations</div>', unsafe_allow_html=True)

    scheduled = schedule_df[schedule_df["status"] == "Scheduled"]
    conflicts = schedule_df[schedule_df["status"] == "Conflict"]

    # --- Row 1: Pie chart + Bar chart ------------------------------------
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        status_counts = schedule_df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_pie = px.pie(
            status_counts,
            names="Status",
            values="Count",
            hole=0.0,
            color="Status",
            color_discrete_map={"Scheduled": GREEN, "Conflict": RED},
        )
        fig_pie.update_traces(textinfo="percent+label")
        apply_dark_layout(fig_pie, "Meeting Status")
        st.plotly_chart(fig_pie, use_container_width=True)

    with row1_col2:
        if not scheduled.empty:
            room_counts = (
                scheduled.groupby("assigned_room")["meeting_id"]
                .count()
                .reset_index()
                .rename(columns={"meeting_id": "Meetings"})
                .sort_values("assigned_room")
            )
            fig_bar = px.bar(
                room_counts,
                x="assigned_room",
                y="Meetings",
                text="Meetings",
                labels={"assigned_room": "Room"},
                color_discrete_sequence=[ACCENT],
            )
            fig_bar.update_traces(textposition="outside")
            apply_dark_layout(fig_bar, "Meetings Assigned per Room")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No scheduled meetings to chart yet.")

    # --- Row 2: Horizontal bar + Donut -----------------------------------
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        dept_counts = (
            schedule_df.groupby("department")["meeting_id"]
            .count()
            .reset_index()
            .rename(columns={"meeting_id": "Meetings"})
            .sort_values("Meetings", ascending=True)
        )
        fig_hbar = px.bar(
            dept_counts,
            x="Meetings",
            y="department",
            orientation="h",
            text="Meetings",
            labels={"department": "Department"},
            color_discrete_sequence=["#7C4DFF"],
        )
        fig_hbar.update_traces(textposition="outside")
        apply_dark_layout(fig_hbar, "Department-wise Meeting Count")
        st.plotly_chart(fig_hbar, use_container_width=True)

    with row2_col2:
        utilization = compute_room_utilization(rooms_df, schedule_df)
        if not utilization.empty:
            fig_donut = px.pie(
                utilization,
                names="room_id",
                values="utilization_pct",
                hole=0.55,
            )
            fig_donut.update_traces(textinfo="percent+label")
            apply_dark_layout(fig_donut, "Room Utilization %")
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No utilization data available yet.")

    # --- Row 3: Timeline ---------------------------------------------------
    if not scheduled.empty:
        timeline_df = scheduled.copy()
        timeline_df["Room"] = timeline_df["assigned_room"]
        fig_timeline = px.timeline(
            timeline_df,
            x_start="start_time",
            x_end="end_time",
            y="Room",
            color="department",
            hover_data={"meeting_id": True, "attendees": True},
            labels={"department": "Department"},
        )
        fig_timeline.update_yaxes(autorange="reversed")
        apply_dark_layout(fig_timeline, "Meetings Throughout the Day")
        st.plotly_chart(fig_timeline, use_container_width=True)

    # --- Row 4: Heatmap ------------------------------------------------
    if not scheduled.empty and rooms_df is not None and not rooms_df.empty:
        render_occupancy_heatmap(scheduled, rooms_df)


def render_occupancy_heatmap(scheduled_df, rooms_df):
    """
    Render a room-occupancy-by-time-slot heatmap using half-hour buckets.

    Complexity: O(R + T + S), where T is visible half-hour slots and S is
    scheduled meetings. Memory is O(R * T) for the displayed heatmap matrix.
    """
    scheduled_df = scheduled_df.copy()
    if "start_minutes" not in scheduled_df.columns:
        scheduled_df["start_minutes"] = scheduled_df["start_time"].map(time_to_minutes)
    if "end_minutes" not in scheduled_df.columns:
        scheduled_df["end_minutes"] = scheduled_df["end_time"].map(time_to_minutes)

    first_start = int(scheduled_df["start_minutes"].min())
    last_end = int(scheduled_df["end_minutes"].max())
    day_start_minutes = (first_start // 60) * 60
    day_end_minutes = ((last_end + 59) // 60) * 60

    slot_minutes = 30
    slot_offsets = list(range(day_start_minutes, day_end_minutes, slot_minutes))
    day_start = min(scheduled_df["start_time"]).replace(minute=0, second=0, microsecond=0)
    slots = [day_start + timedelta(minutes=offset - day_start_minutes) for offset in slot_offsets]

    room_ids = sorted(rooms_df["room_id"].tolist())
    room_index = {room_id: idx for idx, room_id in enumerate(room_ids)}
    matrix = np.zeros((len(room_ids), len(slots)))

    # Mark each meeting's occupied slot range directly instead of checking every
    # room/slot/meeting combination. This preserves the same half-hour overlap
    # semantics with substantially less repeated work.
    for record in scheduled_df.to_dict("records"):
        r_idx = room_index.get(record["assigned_room"])
        if r_idx is None:
            continue
        start_idx = max(0, (int(record["start_minutes"]) - day_start_minutes) // slot_minutes)
        end_idx = min(
            len(slots),
            (int(record["end_minutes"]) - day_start_minutes + slot_minutes - 1) // slot_minutes,
        )
        matrix[r_idx, start_idx:end_idx] = 1

    slot_labels = [s.strftime("%H:%M") for s in slots]

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=slot_labels,
            y=room_ids,
            colorscale=[[0, "#111315"], [1, ACCENT]],
            showscale=False,
            xgap=3,
            ygap=3,
        )
    )
    apply_dark_layout(fig_heatmap, "Room Occupancy by Time Slot")
    fig_heatmap.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_heatmap, use_container_width=True)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
def render_analytics():
    schedule_df = st.session_state.get("schedule_df")
    rooms_df = st.session_state.get("rooms_df")

    if schedule_df is None or schedule_df.empty:
        return

    st.markdown('<div class="section-title">Analytics</div>', unsafe_allow_html=True)

    scheduled = schedule_df[schedule_df["status"] == "Scheduled"]
    total_meetings = len(schedule_df)
    scheduled_count = len(scheduled)
    conflict_count = total_meetings - scheduled_count

    utilization = compute_room_utilization(rooms_df, schedule_df)

    if not utilization.empty:
        most_occupied = utilization.loc[utilization["utilization_pct"].idxmax()]
        least_occupied = utilization.loc[utilization["utilization_pct"].idxmin()]
        avg_utilization = utilization["utilization_pct"].mean()
        total_capacity_minutes_equivalent = utilization["capacity"].sum()
        unused_capacity = compute_unused_capacity(rooms_df, scheduled)
    else:
        most_occupied = None
        least_occupied = None
        avg_utilization = 0.0
        unused_capacity = 0

    peak_hour = compute_peak_hour(scheduled)
    top_department = compute_top_department(schedule_df)

    success_rate = (scheduled_count / total_meetings * 100.0) if total_meetings else 0.0
    conflict_rate = (conflict_count / total_meetings * 100.0) if total_meetings else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        analytics_card(
            "Most Occupied Room",
            most_occupied["room_id"] if most_occupied is not None else "—",
            f"{most_occupied['utilization_pct']:.1f}% utilized" if most_occupied is not None else "",
        )
    with col2:
        analytics_card(
            "Least Occupied Room",
            least_occupied["room_id"] if least_occupied is not None else "—",
            f"{least_occupied['utilization_pct']:.1f}% utilized" if least_occupied is not None else "",
        )
    with col3:
        analytics_card("Average Room Utilization", f"{avg_utilization:.1f}%")
    with col4:
        analytics_card("Unused Capacity", f"{unused_capacity} seats")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        analytics_card("Peak Meeting Hour", peak_hour)
    with col6:
        analytics_card("Top Department", top_department)
    with col7:
        analytics_card("Scheduling Success Rate", f"{success_rate:.1f}%")
    with col8:
        analytics_card("Conflict Rate", f"{conflict_rate:.1f}%")


def analytics_card(label, value, sub=None):
    sub_html = f'<div style="color:{MUTED}; font-size:0.8rem; margin-top:0.2rem;">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="info-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def compute_unused_capacity(rooms_df, scheduled_df):
    """
    Sum of (room capacity - attendees) across all scheduled meetings,
    representing seats that were booked but not filled.
    """
    if rooms_df is None or rooms_df.empty or scheduled_df is None or scheduled_df.empty:
        return 0

    unused = scheduled_df["room_capacity"] - scheduled_df["attendees"]
    return int(unused.clip(lower=0).sum())


def compute_peak_hour(scheduled_df):
    """Return the busiest starting hour in O(S) time and O(H) memory."""
    if scheduled_df is None or scheduled_df.empty:
        return "—"

    # Prefer cached minute offsets and fall back to datetimes for older data.
    if "start_minutes" in scheduled_df.columns:
        hours = scheduled_df["start_minutes"] // 60
    else:
        hours = scheduled_df["start_time"].apply(lambda t: t.hour)
    if hours.empty:
        return "—"

    peak = int(hours.value_counts().idxmax())
    return f"{peak:02d}:00 - {peak + 1:02d}:00"


def compute_top_department(schedule_df):
    if schedule_df is None or schedule_df.empty:
        return "—"
    counts = schedule_df["department"].value_counts()
    if counts.empty:
        return "—"
    return counts.idxmax()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    inject_css()
    init_session_state()
    render_sidebar()
    render_header()

    render_upload_errors()

    rooms_df = st.session_state.get("rooms_df")
    meetings_df = st.session_state.get("meetings_df")

    if rooms_df is None and meetings_df is None:
        st.info(
            "Upload a `.txt` dataset from the sidebar, then click **Generate Schedule**."
        )
        with st.expander("Dataset format"):
            st.code(
                "ROOMS\n"
                "R101,20\n"
                "R102,10\n"
                "R103,50\n\n"
                "MEETINGS\n"
                "M001,HR,15,09:00-10:00\n"
                "M002,Finance,8,09:00-10:00\n"
                "M003,Engineering,45,10:00-11:00\n"
                "M004,Marketing,18,09:30-10:30\n"
                "M005,Sales,12,11:00-12:00\n",
                language="text",
            )
        return

    render_dataset_preview()

    if not st.session_state.get("generated"):
        st.info("Dataset loaded. Click **Generate Schedule** in the sidebar.")
        return

    # Consistency safety-net check (does not alter results, just surfaces issues)
    consistency_issues = detect_conflicts(st.session_state["schedule_df"])
    if consistency_issues:
        st.error("Internal consistency check found issues:")
        for issue in consistency_issues:
            st.markdown(f"- {issue}")

    render_dashboard_metrics()
    render_schedule_table()
    render_conflict_table()
    render_charts()
    render_analytics()


if __name__ == "__main__":
    main()
