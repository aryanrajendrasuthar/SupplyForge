import io


def _upload_document(client, supplier_id):
    client.post(
        f"/suppliers/{supplier_id}/documents",
        data={"file": (io.BytesIO(b"bytes"), "w9.pdf"), "document_type": "w9"},
        content_type="multipart/form-data",
    )


def test_submit_for_review_requires_a_document(client, supplier_id):
    response = client.post(f"/suppliers/{supplier_id}/submit-for-review")
    assert response.status_code == 400


def test_submit_for_review_succeeds_once_document_uploaded(client, supplier_id):
    _upload_document(client, supplier_id)
    response = client.post(f"/suppliers/{supplier_id}/submit-for-review")
    assert response.status_code == 200
    assert response.get_json()["status"] == "under_review"


def test_cannot_approve_before_under_review(client, supplier_id):
    response = client.post(f"/suppliers/{supplier_id}/approve", json={"approved_by": "approver@example.com"})
    assert response.status_code == 409


def test_full_approval_workflow(client, supplier_id):
    _upload_document(client, supplier_id)
    client.post(f"/suppliers/{supplier_id}/submit-for-review")

    response = client.post(f"/suppliers/{supplier_id}/approve", json={"approved_by": "approver@example.com"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "approved"


def test_rejection_workflow_requires_reason(client, supplier_id):
    _upload_document(client, supplier_id)
    client.post(f"/suppliers/{supplier_id}/submit-for-review")

    response = client.post(f"/suppliers/{supplier_id}/reject", json={"rejected_by": "approver@example.com"})
    assert response.status_code == 400

    response = client.post(
        f"/suppliers/{supplier_id}/reject",
        json={"rejected_by": "approver@example.com", "reason": "missing insurance certificate"},
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "rejected"


def test_deactivate_requires_approved_status(client, supplier_id):
    response = client.post(
        f"/suppliers/{supplier_id}/deactivate",
        json={"deactivated_by": "admin@example.com", "reason": "no longer active"},
    )
    assert response.status_code == 409


def test_deactivate_succeeds_after_approval(client, supplier_id):
    _upload_document(client, supplier_id)
    client.post(f"/suppliers/{supplier_id}/submit-for-review")
    client.post(f"/suppliers/{supplier_id}/approve", json={"approved_by": "approver@example.com"})

    response = client.post(
        f"/suppliers/{supplier_id}/deactivate",
        json={"deactivated_by": "admin@example.com", "reason": "no longer active"},
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "deactivated"


def test_audit_log_records_every_transition(client, supplier_id):
    _upload_document(client, supplier_id)
    client.post(f"/suppliers/{supplier_id}/submit-for-review")
    client.post(f"/suppliers/{supplier_id}/approve", json={"approved_by": "approver@example.com"})
    client.post(
        f"/suppliers/{supplier_id}/deactivate",
        json={"deactivated_by": "admin@example.com", "reason": "no longer active"},
    )

    response = client.get(f"/suppliers/{supplier_id}/audit-log")
    entries = response.get_json()

    assert [e["new_status"] for e in entries] == [
        "registered",
        "under_review",
        "approved",
        "deactivated",
    ]
    assert entries[0]["previous_status"] is None
    assert entries[-1]["actor"] == "admin@example.com"
    assert entries[-1]["reason"] == "no longer active"
