import requests

BASE_URL = "http://localhost:8000"


def test_post_api_sessions_create_new_crisis_session():
    url = f"{BASE_URL}/api/sessions"
    payload = {
        "crisis_input": "This is a valid and sufficiently long crisis input for testing."
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data and isinstance(data["session_id"], str) and data["session_id"]
        assert "chairman_token" in data and isinstance(data["chairman_token"], str) and data["chairman_token"]
        assert "ws_url" in data and isinstance(data["ws_url"], str) and data["ws_url"]
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"


test_post_api_sessions_create_new_crisis_session()