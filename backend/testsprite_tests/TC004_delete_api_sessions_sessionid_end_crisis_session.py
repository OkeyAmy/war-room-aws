import requests
import time

BASE_URL = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json"
}
TIMEOUT = 30

def test_delete_api_sessions_sessionid_end_crisis_session():
    # Step 1: Create a new session to get session_id and chairman_token (for cleanup and testing)
    create_payload = {
        "crisis_input": "This is a valid crisis scenario input that meets length requirements."
    }

    create_response = requests.post(
        f"{BASE_URL}/api/sessions",
        json=create_payload,
        timeout=TIMEOUT,
        headers={"Content-Type": "application/json"}
    )
    assert create_response.status_code == 201, f"Expected 201, got {create_response.status_code}"
    create_data = create_response.json()
    session_id = create_data.get("session_id")
    chairman_token = create_data.get("chairman_token")
    assert session_id, "session_id missing in create session response"
    assert chairman_token, "chairman_token missing in create session response"

    auth_headers = {
        "Authorization": f"Bearer {chairman_token}",
        "Content-Type": "application/json"
    }

    try:
        # Step 2: Delete the session (end crisis session)
        delete_response = requests.delete(
            f"{BASE_URL}/api/sessions/{session_id}",
            headers=auth_headers,
            timeout=TIMEOUT
        )
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        delete_data = delete_response.json()
        assert "closed_at" in delete_data, "closed_at not in delete response"
        assert "agents_released" in delete_data, "agents_released not in delete response"

        # Step 3: Confirm subsequent GET requests with same token return 403 or 404
        # We allow either 403 or 404 as valid error codes after session end
        retry_attempts = 3
        for attempt in range(retry_attempts):
            get_response = requests.get(
                f"{BASE_URL}/api/sessions/{session_id}",
                headers=auth_headers,
                timeout=TIMEOUT
            )
            if get_response.status_code in (403, 404):
                break
            # Sometimes the system may take a moment; wait before retrying
            time.sleep(1)
        else:
            assert False, f"Expected 403 or 404 after session end, got {get_response.status_code}"

    finally:
        # Cleanup: Ensure deletion in case delete step failed or to be idempotent
        requests.delete(
            f"{BASE_URL}/api/sessions/{session_id}",
            headers=auth_headers,
            timeout=TIMEOUT
        )

test_delete_api_sessions_sessionid_end_crisis_session()
