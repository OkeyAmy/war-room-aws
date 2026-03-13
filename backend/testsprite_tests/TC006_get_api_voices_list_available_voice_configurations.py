import requests

BASE_URL = "http://localhost:8000"

def test_get_api_voices_list_available_voice_configurations():
    url = f"{BASE_URL}/api/voices"
    try:
        response = requests.get(url, timeout=30)
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict), "Response is not a list or dict"
        # Basic content checks: expect non-empty list or dict that represents voice configurations
        if isinstance(data, list):
            assert len(data) > 0, "Voices list is empty"
            # Each item could be dict representing voice config
            for voice in data:
                assert isinstance(voice, dict), "Voice configuration item is not a dict"
                # Expect some common keys, e.g., 'name', 'language', or similar - since no exact schema given, check keys presence
                assert any(k in voice for k in ['name', 'id', 'language', 'gender']), "Voice configuration missing expected keys"
        elif isinstance(data, dict):
            # If dict, expect keys for voice types or similar
            assert len(data.keys()) > 0, "Voices dict is empty"
    except requests.exceptions.RequestException as e:
        assert False, f"HTTP request failed: {str(e)}"


test_get_api_voices_list_available_voice_configurations()