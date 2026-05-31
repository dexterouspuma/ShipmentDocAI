"""Full document lifecycle through the API in local mode:
upload -> (in-process extraction) -> open -> edit -> approve -> cover sheet.
"""


def test_full_lifecycle(client, sample_pdf):
    # Upload -> local extraction runs in-process on enqueue.
    r = client.post(
        "/documents?document_type=arrival_notice",
        files={"file": ("an.pdf", sample_pdf, "application/pdf")},
    )
    assert r.status_code == 201
    doc_id = r.json()["id"]

    # After in-process extraction the document should be 'extracted' with data.
    r = client.get(f"/documents/{doc_id}")
    doc = r.json()
    assert doc["status"] == "extracted"
    assert doc["extracted"]["bl_number"]["value"] == "EGLV143026058813"
    assert doc["min_confidence"] is not None and doc["min_confidence"] < 0.8

    # Open for review.
    r = client.post(f"/documents/{doc_id}/open")
    assert r.status_code == 200 and r.json()["status"] == "in_review"

    # Edit a field (analyst correction) -> audited.
    r = client.patch(f"/documents/{doc_id}/fields",
                     json={"field_path": "goods_description",
                           "new_value": "PLASTIC HOUSEHOLD GOODS & STORAGE BINS"})
    assert r.status_code == 200
    gd = r.json()["extracted"]["goods_description"]
    assert gd["value"].endswith("BINS") and gd["edited"] is True

    # Approve.
    r = client.post(f"/documents/{doc_id}/approve")
    assert r.status_code == 200 and r.json()["status"] == "approved"

    # Generate cover sheet (PDF).
    r = client.post(f"/documents/{doc_id}/cover-sheet?fmt=pdf")
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    assert "attachment" in r.headers.get("content-disposition", "")

    # Audit trail should record the actions.
    r = client.get(f"/documents/{doc_id}/audit")
    actions = [a["action"] for a in r.json()]
    assert "opened" in actions and "edited_field" in actions and "approved" in actions
    assert "generated_cover_sheet" in actions
