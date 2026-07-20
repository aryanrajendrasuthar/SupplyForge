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


def test_approve_requires_authentication(client, supplier_id):
    response = client.post(f"/suppliers/{supplier_id}/approve")
    assert response.status_code == 401


def test_approve_requires_approver_role(client, supplier_id):
    password = "correct horse battery staple"
    client.post("/auth/register", json={"email": "analyst@example.com", "password": password, "role": "analyst"})
    client.post("/auth/login", json={"email": "analyst@example.com", "password": password})

    response = client.post(f"/suppliers/{supplier_id}/approve")
    assert response.status_code == 403


def test_cannot_approve_before_under_review(approver_client, supplier_id):
    response = approver_client.post(f"/suppliers/{supplier_id}/approve")
    assert response.status_code == 409


def test_full_approval_workflow(approver_client, supplier_id):
    _upload_document(approver_client, supplier_id)
    approver_client.post(f"/suppliers/{supplier_id}/submit-for-review")

    response = approver_client.post(f"/suppliers/{supplier_id}/approve")
    assert response.status_code == 200
    assert response.get_json()["status"] == "approved"


def test_rejection_workflow_requires_reason(approver_client, supplier_id):
    _upload_document(approver_client, supplier_id)
    approver_client.post(f"/suppliers/{supplier_id}/submit-for-review")

    response = approver_client.post(f"/suppliers/{supplier_id}/reject", json={})
    assert response.status_code == 400

    response = approver_client.post(
        f"/suppliers/{supplier_id}/reject", json={"reason": "missing insurance certificate"}
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "rejected"


def test_deactivate_requires_approved_status(approver_client, supplier_id):
    response = approver_client.post(
        f"/suppliers/{supplier_id}/deactivate", json={"reason": "no longer active"}
    )
    assert response.status_code == 409


def test_deactivate_succeeds_after_approval(approver_client, supplier_id):
    _upload_document(approver_client, supplier_id)
    approver_client.post(f"/suppliers/{supplier_id}/submit-for-review")
    approver_client.post(f"/suppliers/{supplier_id}/approve")

    response = approver_client.post(
        f"/suppliers/{supplier_id}/deactivate", json={"reason": "no longer active"}
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "deactivated"


def test_audit_log_records_every_transition(approver_client, supplier_id):
    _upload_document(approver_client, supplier_id)
    approver_client.post(f"/suppliers/{supplier_id}/submit-for-review")
    approver_client.post(f"/suppliers/{supplier_id}/approve")
    approver_client.post(f"/suppliers/{supplier_id}/deactivate", json={"reason": "no longer active"})

    response = approver_client.get(f"/suppliers/{supplier_id}/audit-log")
    entries = response.get_json()

    assert [e["new_status"] for e in entries] == [
        "registered",
        "under_review",
        "approved",
        "deactivated",
    ]
    assert entries[0]["previous_status"] is None
    assert entries[-1]["actor"] == "approver@example.com"
    assert entries[-1]["reason"] == "no longer active"
