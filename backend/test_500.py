from fastapi.testclient import TestClient
from main import app
import traceback

client = TestClient(app)
try:
    response = client.post("/api/sessions", json={
        "crisis_input": "Severe flooding in downtown area causing major evacuations.",
        "chairman_name": "Chairman Smith",
        "session_duration_minutes": 60
    })
    print(response.status_code)
    print(response.text)
except Exception as e:
    traceback.print_exc()
