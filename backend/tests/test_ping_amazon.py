"""
WAR ROOM — Test Ping: Amazon Nova API + AWS Credentials
Verifies that NOVA_API_KEY is valid, Nova 2 Lite can generate text/JSON,
and AWS credentials are present for Nova Sonic voice integration.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def test_nova_api_key_exists():
    """Check that NOVA_API_KEY is set in environment."""
    api_key = os.environ.get("NOVA_API_KEY", "")
    assert api_key, "NOVA_API_KEY is not set in .env"
    assert api_key != "your-nova-api-key", "NOVA_API_KEY is still the placeholder value"
    print(f"  NOVA_API_KEY is set ({api_key[:10]}...)")


def test_nova_base_url_configured():
    """Check that NOVA_BASE_URL is set."""
    base_url = os.environ.get("NOVA_BASE_URL", "")
    assert base_url, "NOVA_BASE_URL is not set in .env"
    assert "nova.amazon.com" in base_url, (
        f"NOVA_BASE_URL does not look like an Amazon Nova endpoint: {base_url}"
    )
    print(f"  NOVA_BASE_URL = {base_url}")


def test_nova_text_generation():
    """Ping Amazon Nova API with a simple text generation request using OpenAI SDK."""
    from openai import OpenAI

    api_key = os.environ.get("NOVA_API_KEY")
    base_url = os.environ.get("NOVA_BASE_URL", "https://api.nova.amazon.com/v1")
    model = os.environ.get("NOVA_AGENT_MODEL", "nova-2-lite-v1")

    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Respond with exactly: PING_OK"}],
        max_tokens=20,
    )

    text = response.choices[0].message.content or ""
    assert text.strip(), "Amazon Nova returned no text"
    print(f"  Nova text generation works (model={model}). Response: {text.strip()[:50]}")


def test_nova_json_generation():
    """Test the scenario model (nova-2-lite-v1) with a JSON response."""
    from openai import OpenAI

    api_key = os.environ.get("NOVA_API_KEY")
    base_url = os.environ.get("NOVA_BASE_URL", "https://api.nova.amazon.com/v1")
    model = os.environ.get("NOVA_SCENARIO_MODEL", "nova-2-lite-v1")

    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": 'Return a JSON object: {"status": "ok", "model": "' + model + '"}',
        }],
        max_tokens=50,
    )

    import json
    text = response.choices[0].message.content or ""
    assert text.strip(), f"Nova {model} returned no text"
    data = json.loads(text)
    assert data.get("status") == "ok", f"Unexpected response: {data}"
    print(f"  Nova JSON generation ({model}) works. Response: {text.strip()[:60]}")


def test_aws_credentials_present():
    """Check that AWS credentials are set for Nova Sonic via LiveKit."""
    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    region = os.environ.get("AWS_REGION", "us-east-1")

    assert access_key, "AWS_ACCESS_KEY_ID is not set in .env"
    assert access_key != "your-aws-access-key-id", "AWS_ACCESS_KEY_ID is still the placeholder"
    assert secret_key, "AWS_SECRET_ACCESS_KEY is not set in .env"
    assert secret_key != "your-aws-secret-access-key", "AWS_SECRET_ACCESS_KEY is still the placeholder"
    print(f"  AWS credentials set (key={access_key[:8]}..., region={region})")


if __name__ == "__main__":
    print("\n WAR ROOM — Amazon Nova API Ping Test\n" + "=" * 50)

    tests = [
        ("API Key Present", test_nova_api_key_exists),
        ("Base URL Configured", test_nova_base_url_configured),
        ("Text Generation (Agent Model)", test_nova_text_generation),
        ("JSON Generation (Scenario Model)", test_nova_json_generation),
        ("AWS Credentials (Nova Sonic)", test_aws_credentials_present),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            print(f"\n  {name}...")
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All Amazon Nova API tests passed!")
    else:
        print("Some tests failed — check your NOVA_API_KEY, NOVA_BASE_URL, and AWS credentials")
