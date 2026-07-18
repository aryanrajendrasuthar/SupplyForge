from app import process_message


def test_process_message_reports_not_implemented():
    result = process_message({"record_id": "rec-1"})
    assert result == {"status": "not_implemented", "record_id": "rec-1"}
