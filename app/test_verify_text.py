from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_verify_text_endpoint():
    payload = {"text": "Government declares XYZ outbreak"}
    response = client.post("/verify_text/", json=payload)

    # Status should be 200
    assert response.status_code == 200

    data = response.json()

    # Check keys exist
    assert "verdict" in data
    assert "confidence" in data
    assert "evidence_links" in data

    # Type checks
    assert isinstance(data["verdict"], str)
    assert isinstance(data["confidence"], float)
    assert isinstance(data["evidence_links"], list)

    # Optional: ensure confidence is between 0 and 1
    assert 0.0 <= data["confidence"] <= 1.0
