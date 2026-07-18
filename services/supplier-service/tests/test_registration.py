import io


def test_register_supplier_returns_201_registered_status(client):
    response = client.post(
        "/suppliers", json={"legal_name": "Acme Supplies", "contact_email": "acme@example.com"}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "registered"
    assert body["legal_name"] == "Acme Supplies"


def test_register_supplier_rejects_invalid_email(client):
    response = client.post("/suppliers", json={"legal_name": "Acme", "contact_email": "not-an-email"})
    assert response.status_code == 400


def test_get_supplier_404_when_missing(client):
    assert client.get("/suppliers/9999").status_code == 404


def test_list_suppliers_filters_by_status(client, supplier_id):
    response = client.get("/suppliers?status=registered")
    body = response.get_json()
    assert any(s["id"] == supplier_id for s in body)

    response = client.get("/suppliers?status=approved")
    assert response.get_json() == []


def test_upload_document_returns_metadata(client, supplier_id):
    data = {
        "file": (io.BytesIO(b"pdf bytes here"), "w9.pdf"),
        "document_type": "w9",
    }
    response = client.post(
        f"/suppliers/{supplier_id}/documents", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["document_type"] == "w9"
    assert body["filename"] == "w9.pdf"


def test_upload_document_requires_document_type(client, supplier_id):
    data = {"file": (io.BytesIO(b"bytes"), "w9.pdf")}
    response = client.post(
        f"/suppliers/{supplier_id}/documents", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 400


def test_list_documents_returns_uploaded_documents(client, supplier_id):
    client.post(
        f"/suppliers/{supplier_id}/documents",
        data={"file": (io.BytesIO(b"bytes"), "w9.pdf"), "document_type": "w9"},
        content_type="multipart/form-data",
    )
    response = client.get(f"/suppliers/{supplier_id}/documents")
    body = response.get_json()
    assert len(body) == 1
    assert body[0]["document_type"] == "w9"
