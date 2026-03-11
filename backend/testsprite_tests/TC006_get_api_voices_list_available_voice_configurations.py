import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_voices_list_available_voice_configurations():
    url = f"{BASE_URL}/api/voices"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict), "Response should be a list or dict of voice configurations"
        # If dict, it should contain keys that indicate voice data (loosely checking keys)
        if isinstance(data, dict):
            assert any(key.lower().find("voice") != -1 or key.lower().find("id") != -1 for key in data.keys()), "Response dict should contain voice-related keys"
        # If list, check elements are dicts with voice-related keys
        if isinstance(data, list):
            assert all(isinstance(item, dict) for item in data), "All items in response list should be dicts"
            if data:
                item = data[0]
                assert any(key.lower().find("voice") != -1 or key.lower().find("id") != -1 for key in item.keys()), "Voice configuration items should contain voice-related keys"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_get_api_voices_list_available_voice_configurations()