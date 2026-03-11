import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_sessions_sessionid_get_session_state():
    # Create a new crisis session to obtain valid session_id and chairman_token
    create_url = f"{BASE_URL}/api/sessions"
    create_payload = {
        "crisis_input": "Large fire outbreak in downtown area affecting multiple buildings."
    }

    session_id = None
    chairman_token = None

    try:
        create_resp = requests.post(create_url, json=create_payload, timeout=TIMEOUT)
        assert create_resp.status_code == 201, f"Session creation failed: {create_resp.text}"
        create_data = create_resp.json()
        assert "session_id" in create_data and "chairman_token" in create_data and "ws_url" in create_data
        session_id = create_data["session_id"]
        chairman_token = create_data["chairman_token"]

        # Get the full session state for the created session_id with authorization
        get_url = f"{BASE_URL}/api/sessions/{session_id}"
        headers = {
            "Authorization": f"Bearer {chairman_token}"
        }

        get_resp = requests.get(get_url, headers=headers, timeout=TIMEOUT)
        assert get_resp.status_code == 200, f"Failed to get session state: {get_resp.text}"
        session_state = get_resp.json()

        # Validate that critical keys exist in the response
        assert "status" in session_state, "Missing 'status' in session state"
        assert "timer" in session_state, "Missing 'timer' in session state"
        assert "agent_count" in session_state, "Missing 'agent_count' in session state"

    finally:
        # Cleanup: delete the created session
        if session_id and chairman_token:
            delete_url = f"{BASE_URL}/api/sessions/{session_id}"
            headers = {
                "Authorization": f"Bearer {chairman_token}"
            }
            try:
                requests.delete(delete_url, headers=headers, timeout=TIMEOUT)
            except Exception:
                pass


test_get_api_sessions_sessionid_get_session_state()