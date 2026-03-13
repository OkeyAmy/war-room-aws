import requests

BASE_URL = "http://localhost:8000"

def test_TC003_patch_api_sessions_sessionid_update_settings():
    # Step 1: Create a new session to get session_id and chairman_token
    create_payload = {
        "crisis_input": "Initial crisis scenario setup for testing pause feature in session.",
        "chairman_name": "Test Chairman",
        "session_duration_minutes": 60
    }
    try:
        create_resp = requests.post(
            f"{BASE_URL}/api/sessions",
            json=create_payload,
            timeout=30
        )
        assert create_resp.status_code == 201, f"Expected 201 on session creation, got {create_resp.status_code}"
        create_data = create_resp.json()
        session_id = create_data.get("session_id")
        chairman_token = create_data.get("chairman_token")
        assert session_id, "session_id missing from create response"
        assert chairman_token, "chairman_token missing from create response"
        
        # Step 2: Update session settings: pause the session
        patch_url = f"{BASE_URL}/api/sessions/{session_id}"
        headers = {
            "Authorization": f"Bearer {chairman_token}"
        }
        patch_payload = {"paused": True}

        patch_resp = requests.patch(
            patch_url,
            json=patch_payload,
            headers=headers,
            timeout=30
        )
        assert patch_resp.status_code == 200, f"Expected 200 on session update, got {patch_resp.status_code}"
        patch_data = patch_resp.json()

        # Validate that updated_fields includes 'paused'
        updated_fields = patch_data.get("updated_fields")
        assert updated_fields is not None, "updated_fields missing in patch response"
        assert "paused" in updated_fields, "paused field not included in updated_fields"

        # Validate that current_state is included and paused is true in current_state
        current_state = patch_data.get("current_state")
        assert current_state is not None, "current_state missing in patch response"
        assert current_state.get("paused") is True, "current_state paused field is not true"

    finally:
        # Cleanup: Delete the session
        if 'session_id' in locals() and 'chairman_token' in locals():
            try:
                del_resp = requests.delete(
                    f"{BASE_URL}/api/sessions/{session_id}",
                    headers={"Authorization": f"Bearer {chairman_token}"},
                    timeout=30
                )
                # We do not assert here since deletion might fail silently if session already removed
            except Exception:
                pass

test_TC003_patch_api_sessions_sessionid_update_settings()