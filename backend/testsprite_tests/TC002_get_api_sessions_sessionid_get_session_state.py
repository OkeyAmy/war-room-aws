import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_sessions_sessionid_get_session_state():
    # First create a new crisis session to get a valid session_id and chairman_token
    create_payload = {
        "crisis_input": "A severe storm is approaching the city, causing power outages and flooding.",
        "chairman_name": "TestChairman",
        "session_duration_minutes": 60
    }
    create_response = requests.post(
        f"{BASE_URL}/api/sessions",
        json=create_payload,
        timeout=TIMEOUT
    )
    assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}"
    create_data = create_response.json()
    assert "session_id" in create_data and "chairman_token" in create_data and "ws_url" in create_data

    session_id = create_data["session_id"]
    chairman_token = create_data["chairman_token"]

    # Use try-finally to ensure the session is ended after test
    try:
        headers = {
            "Authorization": f"Bearer {chairman_token}"
        }
        get_response = requests.get(
            f"{BASE_URL}/api/sessions/{session_id}",
            headers=headers,
            timeout=TIMEOUT
        )
        assert get_response.status_code == 200, f"Expected 200, got {get_response.status_code}"
        session_data = get_response.json()
        # Assert response contains keys "status", "timer", and "agent_count"
        assert "status" in session_data, "Response missing 'status'"
        assert "timer" in session_data, "Response missing 'timer'"
        assert "agent_count" in session_data, "Response missing 'agent_count'"
    finally:
        # End the session to clean up
        headers = {
            "Authorization": f"Bearer {chairman_token}"
        }
        requests.delete(
            f"{BASE_URL}/api/sessions/{session_id}",
            headers=headers,
            timeout=TIMEOUT
        )

test_get_api_sessions_sessionid_get_session_state()