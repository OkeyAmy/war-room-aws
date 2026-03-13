import requests

BASE_URL = "http://localhost:8000"

def test_TC001_post_api_sessions_create_new_crisis_session():
    url = f"{BASE_URL}/api/sessions"
    payload = {
        "crisis_input": "A major cyber attack is crippling the city's power grid across multiple districts.",
        "chairman_name": "Chairman Smith",
        "session_duration_minutes": 60
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        assert response.status_code == 201, f"Expected status 201 but got {response.status_code}"
        data = response.json()
        assert "session_id" in data, "Response missing session_id"
        assert "chairman_token" in data, "Response missing chairman_token"
        assert "ws_url" in data, "Response missing ws_url"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_TC001_post_api_sessions_create_new_crisis_session()