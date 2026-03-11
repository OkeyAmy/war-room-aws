import requests
import time

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_delete_api_sessions_end_crisis_session():
    # Step 1: Create a new session to obtain session_id and chairman_token
    session_create_url = f"{BASE_URL}/api/sessions"
    session_create_payload = {
        "crisis_input": "A valid detailed crisis input to bootstrap scenario for testing deletion."
    }
    session_create_resp = requests.post(session_create_url, json=session_create_payload, timeout=TIMEOUT)
    assert session_create_resp.status_code == 201, f"Expected 201 Created but got {session_create_resp.status_code}"
    session_create_data = session_create_resp.json()
    session_id = session_create_data.get("session_id")
    chairman_token = session_create_data.get("chairman_token")
    assert session_id, "session_id not returned on session creation"
    assert chairman_token, "chairman_token not returned on session creation"

    headers = {"Authorization": f"Bearer {chairman_token}"}
    session_url = f"{BASE_URL}/api/sessions/{session_id}"

    try:
        # Step 2: Delete the session to end the crisis session
        delete_resp = requests.delete(session_url, headers=headers, timeout=TIMEOUT)
        assert delete_resp.status_code == 200, f"Expected 200 OK on DELETE but got {delete_resp.status_code}"
        delete_data = delete_resp.json()
        assert "closed_at" in delete_data, "Response missing 'closed_at'"
        assert "agents_released" in delete_data, "Response missing 'agents_released'"

        # Step 3: Confirm that subsequent GET requests with same token return 403 or 404
        get_resp = requests.get(session_url, headers=headers, timeout=TIMEOUT)
        assert get_resp.status_code in (403, 404), (
            f"Expected 403 or 404 on GET after deletion but got {get_resp.status_code}"
        )

    finally:
        # Cleanup: Try to delete the session if it still exists (idempotent)
        try:
            requests.delete(session_url, headers=headers, timeout=TIMEOUT)
        except Exception:
            pass

test_delete_api_sessions_end_crisis_session()