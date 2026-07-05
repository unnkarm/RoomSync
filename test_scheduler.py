from parser import parse_dataset
from scheduler import detect_conflicts, schedule_meetings


def test_empty_inputs_return_empty_frames():
    schedule_df, conflicts_df = schedule_meetings(None, None)
    assert schedule_df.empty
    assert conflicts_df.empty


def test_conflict_detection_handles_no_issues():
    raw_text = """ROOMS
R101,20
R102,10

MEETINGS
M001,HR,5,09:00-10:00
M002,Finance,3,10:00-11:00
"""
    rooms_df, meetings_df, errors = parse_dataset(raw_text)
    assert not errors

    schedule_df, conflicts_df = schedule_meetings(rooms_df, meetings_df)
    assert conflicts_df.empty
    assert detect_conflicts(schedule_df) == []
