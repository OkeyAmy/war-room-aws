import requests

BASE_URL = "http://localhost:8000"

def test_tc005_get_api_health_comprehensive_health_check():
    url = f"{BASE_URL}/api/health"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    # Validate response content type and structure (assuming JSON)
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"
    # The response should contain comprehensive system health information; since schema is not detailed,
    # check for expected keys commonly present in health info if any appear in example or just check data is dict.
    assert isinstance(data, dict), "Response JSON should be an object"
    # Additional minimal checks (keys like 'status', 'uptime', 'components' might be typical)
    assert 'status' in data, "Response JSON should contain 'status' key"
    # The 'status' should indicate healthy (accept common healthy statuses including 'degraded')
    assert data['status'].lower() in ('ok', 'healthy', 'running', 'available', 'degraded'), (
        f"Health status unexpected: {data['status']}"
    )

test_tc005_get_api_health_comprehensive_health_check()
