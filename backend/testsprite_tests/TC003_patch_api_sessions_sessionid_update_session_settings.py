import requests
import websocket
import threading
import json
import time

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_patch_api_sessions_sessionid_update_session_settings():
    session_id = None
    chairman_token = None
    ws_url = None
    ws_events = []

    def on_message(ws, message):
        try:
            event = json.loads(message)
            if event.get("type") == "session_paused":
                ws_events.append(event)
        except Exception:
            pass

    def on_error(ws, error):
        pass  # We ignore WS errors for now; can be enhanced if needed.

    def on_close(ws, close_status_code, close_msg):
        pass

    try:
        # Step 1: Create a new session (POST /api/sessions)
        create_payload = {
            "crisis_input": "A major power outage affecting multiple cities.",
            "chairman_name": "ChairmanTest",
            "session_duration_minutes": 60
        }
        create_resp = requests.post(f"{BASE_URL}/api/sessions", json=create_payload, timeout=TIMEOUT)
        assert create_resp.status_code == 201, f"Session creation failed: {create_resp.status_code}, {create_resp.text}"
        create_data = create_resp.json()
        session_id = create_data.get("session_id")
        chairman_token = create_data.get("chairman_token")
        ws_url = create_data.get("ws_url")
        assert session_id and chairman_token and ws_url, "Missing session_id, chairman_token or ws_url in creation response"

        # Step 2: Open WebSocket connection to listen for events
        # ws_url example from PRD: /ws/{session_id}?token={chairman_token}
        ws_full_url = ws_url if ws_url.startswith("ws://") or ws_url.startswith("wss://") else f"ws://localhost:8000{ws_url}"
        ws = websocket.WebSocketApp(ws_full_url,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # Wait briefly for WS connection to establish
        time.sleep(2)

        # Step 3: Patch the session to pause it (PATCH /api/sessions/{session_id})
        patch_headers = {
            "Authorization": f"Bearer {chairman_token}",
            "Content-Type": "application/json"
        }
        patch_payload = {"paused": True}
        patch_resp = requests.patch(f"{BASE_URL}/api/sessions/{session_id}", headers=patch_headers, json=patch_payload, timeout=TIMEOUT)
        assert patch_resp.status_code == 200, f"Patch session failed: {patch_resp.status_code}, {patch_resp.text}"
        patch_data = patch_resp.json()

        # Validate response includes updated_fields and current_state keys
        assert isinstance(patch_data, dict), "Response is not a JSON object"
        assert "updated_fields" in patch_data, "Response missing 'updated_fields'"
        assert "paused" in patch_data["updated_fields"] and patch_data["updated_fields"]["paused"] is True, "'paused' not correctly reflected in updated_fields"
        assert "current_state" in patch_data, "Response missing 'current_state'"
        assert patch_data["current_state"].get("paused") is True, "'paused' state not updated in current_state"

        # Step 4: Wait to receive session_paused event on the WS
        timeout = time.time() + 10  # wait max 10 seconds for event
        while time.time() < timeout:
            if any(event.get("type") == "session_paused" for event in ws_events):
                break
            time.sleep(0.1)
        else:
            assert False, "Did not receive 'session_paused' event on WebSocket"

    finally:
        # Cleanup: delete the created session
        if session_id and chairman_token:
            try:
                del_headers = {"Authorization": f"Bearer {chairman_token}"}
                requests.delete(f"{BASE_URL}/api/sessions/{session_id}", headers=del_headers, timeout=TIMEOUT)
            except Exception:
                pass
        if 'ws' in locals():
            try:
                ws.close()
            except Exception:
                pass

test_patch_api_sessions_sessionid_update_session_settings()