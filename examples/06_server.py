#!/usr/bin/env python3
"""Example 06: Live Interaction Server

This example demonstrates how to start the Personaut REST API server,
create personas via HTTP, and interact with them.

The server provides:
  - Dashboard UI at http://127.0.0.1:5000
  - REST API at http://127.0.0.1:8000/api
  - Interactive docs at http://127.0.0.1:8000/api/docs  (Swagger UI)
  - ReDoc at http://127.0.0.1:8000/api/redoc
  - Health check at http://127.0.0.1:8000/api/health

Usage:
    python 06_server.py
"""

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

# Load .env file if present (for API keys)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"📄 Loaded environment from {env_path}")
except ImportError:
    pass

from personaut.server import LiveInteractionServer


# ─── HTTP Helpers (using stdlib only) ──────────────────────────────────────────

API = "http://127.0.0.1:8000"


def api_get(path: str) -> dict:
    """GET request to the API."""
    req = urllib.request.Request(f"{API}{path}")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def api_post(path: str, data: dict) -> dict:
    """POST request to the API."""
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{API}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def api_patch(path: str, data: dict) -> dict:
    """PATCH request to the API."""
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{API}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def api_delete(path: str) -> int:
    """DELETE request to the API. Returns status code."""
    req = urllib.request.Request(f"{API}{path}", method="DELETE")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status


def wait_for_server(timeout: float = 10.0) -> bool:
    """Wait until the server responds to health checks."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            api_get("/api/health")
            return True
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("Example 06: Live Interaction Server")
    print("=" * 60)

    # 1. Create and start the server
    print("\n1. Starting server...")
    server = LiveInteractionServer()
    server.start(api_port=8000, ui_port=5000, blocking=False)

    if not wait_for_server():
        print("   ❌ Server failed to start")
        return

    print("   ✅ Server running!")
    print("   🖥️  Dashboard: http://127.0.0.1:5000")
    print("   📖 Swagger UI: http://127.0.0.1:8000/api/docs")

    try:
        # 2. Health check
        print("\n2. Health Check:")
        health = api_get("/api/health")
        print(f"   Status: {health['status']}")
        print(f"   Version: {health['version']}")

        # 3. Create individuals via REST API
        print("\n3. Creating Individuals via API:")

        sarah = api_post("/api/individuals", {
            "name": "Sarah",
            "description": "A friendly barista who loves coffee and art",
            "individual_type": "simulated",
            "initial_emotions": {"cheerful": 0.8, "hopeful": 0.5},
            "initial_traits": {"warmth": 0.9, "liveliness": 0.8},
            "metadata": {"occupation": "barista"},
        })
        print(f"   Created: {sarah['name']} (ID: {sarah['id']})")

        mike = api_post("/api/individuals", {
            "name": "Mike",
            "description": "An analytical software architect",
            "individual_type": "simulated",
            "initial_emotions": {"content": 0.5},
            "initial_traits": {"reasoning": 0.9, "dominance": 0.7},
            "metadata": {"occupation": "architect"},
        })
        print(f"   Created: {mike['name']} (ID: {mike['id']})")

        eve = api_post("/api/individuals", {
            "name": "Eve",
            "description": "A curious researcher",
            "individual_type": "simulated",
            "initial_emotions": {"creative": 0.8, "excited": 0.6},
            "initial_traits": {"reasoning": 0.85, "openness_to_change": 0.9},
            "metadata": {"occupation": "researcher"},
        })
        print(f"   Created: {eve['name']} (ID: {eve['id']})")

        # 4. List all individuals
        print("\n4. List All Individuals:")
        listing = api_get("/api/individuals")
        print(f"   Total: {listing['total']}")
        for ind in listing["individuals"]:
            emotions = ind.get("emotional_state") or {}
            traits = ind.get("trait_profile") or {}
            print(f"   • {ind['name']}: emotions={emotions}, traits={traits}")

        # 5. Get individual detail
        print("\n5. Get Individual Detail:")
        detail = api_get(f"/api/individuals/{sarah['id']}")
        print(f"   Name: {detail['name']}")
        print(f"   Description: {detail.get('description')}")
        print(f"   Emotions: {detail.get('emotional_state')}")
        print(f"   Traits: {detail.get('trait_profile')}")

        # 6. Update an individual
        print("\n6. Update Individual:")
        updated = api_patch(f"/api/individuals/{sarah['id']}", {
            "description": "A friendly barista who just won a latte art competition!",
            "metadata": {"occupation": "barista", "award": "Latte Art Champion 2026"},
        })
        print(f"   Updated: {updated['name']}")
        print(f"   New description: {updated.get('description')}")

        # 7. Create a situation
        print("\n7. Create Situation:")
        situation = api_post("/api/situations", {
            "name": "Coffee Shop Conversation",
            "description": "A relaxed chat at a downtown coffee shop",
            "modality": "in_person",
            "location": "Downtown Cafe",
            "context": {"atmosphere": "relaxed", "time_of_day": "morning"},
        })
        print(f"   Created: {situation.get('name', 'situation')} (ID: {situation['id']})")

        # 8. Delete an individual
        print("\n8. Delete Individual:")
        status_code = api_delete(f"/api/individuals/{eve['id']}")
        print(f"   Deleted Eve (status: {status_code})")
        listing2 = api_get("/api/individuals")
        print(f"   Remaining individuals: {listing2['total']}")
        for ind in listing2["individuals"]:
            print(f"   • {ind['name']}")

    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"\n   ⚠️ API error ({e.code}): {body[:300]}")
    except Exception as e:
        print(f"\n   ⚠️ Error: {e}")

    # 9. Keep the server running
    print("\n" + "=" * 60)
    print("✅ Demo complete! Server is still running.")
    print("=" * 60)
    print()
    print("Open in your browser:")
    print("  🖥️  http://127.0.0.1:5000          - Dashboard UI")
    print("  📖 http://127.0.0.1:8000/api/docs   - Swagger API docs")
    print()
    print("API Endpoints:")
    print("  GET    /api/health             - Health check")
    print("  GET    /api/individuals         - List all individuals")
    print("  POST   /api/individuals         - Create individual")
    print("  GET    /api/individuals/{id}    - Get individual")
    print("  PATCH  /api/individuals/{id}    - Update individual")
    print("  DELETE /api/individuals/{id}    - Delete individual")
    print("  GET    /api/situations           - List situations")
    print("  POST   /api/situations           - Create situation")
    print("  POST   /api/sessions             - Create chat session")
    print("  POST   /api/sessions/{id}/messages - Send message")
    print()
    print("Press Ctrl+C to stop the server.\n")

    try:
        while server.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.stop()
        print("Server stopped. Goodbye!")


if __name__ == "__main__":
    main()
