import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_health_comprehensive_health_check():
    url = f"{BASE_URL}/api/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        assert False, f"Request to {url} failed: {e}"
    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
    try:
        data = response.json()
    except Exception as e:
        assert False, f"Response is not a valid JSON: {e}"
    # Check that response contains keys indicative of comprehensive system health information
    # Since no specific schema is given, we check that response is a non-empty dict
    assert isinstance(data, dict), "Response JSON is not a dictionary"
    assert len(data) > 0, "Response JSON is empty"

test_get_api_health_comprehensive_health_check()