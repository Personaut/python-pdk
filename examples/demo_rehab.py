#!/usr/bin/env python3
"""Demo: Nurse convincing an opioid-addicted patient to go to rehab.

Creates two rich personas — a compassionate nurse and a resistant patient —
plus a hospital room situation, their professional relationship, and key
memories that ground the conversation in realistic context.

Usage:
    python examples/demo_rehab.py
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


# ─── HTTP Helpers ──────────────────────────────────────────────────────────────

API = "http://127.0.0.1:8000"


def api_get(path: str) -> dict:
    req = urllib.request.Request(f"{API}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def api_post(path: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{API}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def wait_for_server(timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            api_get("/api/health")
            return True
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False


# ─── Demo Data ─────────────────────────────────────────────────────────────────

def create_demo_data() -> None:
    """Create the nurse, patient, situation, relationship, and memories."""

    print("\n🏥 Creating demo personas...")
    print("=" * 60)

    # ── 1. Nurse: Maria Santos ──────────────────────────────────────────────
    nurse = api_post("/api/individuals", {
        "name": "Maria Santos",
        "description": (
            "Maria is a 38-year-old registered nurse with 14 years of experience, "
            "the last 6 specializing in addiction medicine at Riverside Community "
            "Hospital. She grew up with an uncle who struggled with alcohol addiction "
            "and eventually recovered through a 12-step program, which deeply shaped "
            "her career path. Maria is known on her unit for her calm, patient "
            "demeanor and her ability to connect with even the most resistant "
            "patients. She uses motivational interviewing techniques and believes "
            "firmly that recovery is possible for everyone. She's seen many patients "
            "relapse and knows that pushing too hard can backfire, so she balances "
            "warmth with honest, direct communication. She speaks with a slight "
            "warmth in her voice, often using the patient's first name, and isn't "
            "afraid of silence — she lets people sit with their feelings."
        ),
        "individual_type": "simulated",
        "initial_emotions": {
            "nurturing": 0.85,
            "hopeful": 0.70,
            "content": 0.50,
            "anxious": 0.25,       # worried about patient's health
            "sad": 0.20,           # empathy for patient's suffering
            "proud": 0.15,
            "creative": 0.30,
        },
        "initial_traits": {
            "warmth": 0.92,
            "reasoning": 0.78,
            "emotional_stability": 0.85,
            "dominance": 0.45,          # not domineering, but firm when needed
            "humility": 0.80,
            "liveliness": 0.55,
            "rule_consciousness": 0.75,
            "social_boldness": 0.70,
            "sensitivity": 0.88,
            "vigilance": 0.65,
            "abstractedness": 0.40,     # grounded and practical
            "privateness": 0.35,        # open and forthright
            "apprehension": 0.30,
            "openness_to_change": 0.72,
            "self_reliance": 0.60,
            "perfectionism": 0.55,
            "tension": 0.30,
        },
        "physical_features": {
            "age": 38,
            "gender": "female",
            "ethnicity": "Latina",
            "height": "5'5\"",
            "build": "medium",
            "hair": "dark brown, pulled back in a practical bun",
            "eyes": "warm brown",
            "distinguishing_features": "gentle smile lines, small cross necklace, nurse scrubs",
        },
        "metadata": {
            "occupation": "Registered Nurse, Addiction Medicine",
            "interests": "motivational interviewing, family dinners, gardening, church choir",
            "speaking_style": (
                "Calm, measured, and genuinely warm. Uses the patient's first name "
                "often. Comfortable with silence. Direct but never harsh. Occasionally "
                "shares carefully chosen personal stories to build rapport. Uses "
                "phrases like 'I hear you', 'That makes sense', and 'What would it "
                "look like if...'. Avoids clinical jargon when speaking with patients."
            ),
        },
    })
    print(f"   ✅ Created: {nurse['name']} (ID: {nurse['id']})")
    print(f"      Role: Addiction Medicine Nurse")

    # ── 2. Patient: Marcus "Marc" Williams ──────────────────────────────────
    patient = api_post("/api/individuals", {
        "name": "Marcus Williams",
        "description": (
            "Marcus (Marc) is a 29-year-old construction worker who was prescribed "
            "oxycodone after a serious back injury on a job site 3 years ago. What "
            "started as legitimate pain management spiraled into dependence, and he's "
            "been buying pills from various sources for the past 18 months after his "
            "prescription was cut off. He was admitted to the ER last night after "
            "his girlfriend Keisha found him unresponsive — his second overdose in "
            "4 months. He's physically in withdrawal (mild tremors, sweating, "
            "irritable) and emotionally volatile. Marc is intelligent, was a star "
            "athlete in high school, and comes from a tight-knit family. He loves "
            "his 4-year-old daughter Aaliyah more than anything but is terrified "
            "of losing custody. He's deeply ashamed of his addiction but covers it "
            "with defensiveness and deflection. Part of him knows he needs help, "
            "but the idea of rehab is terrifying — it means admitting he can't "
            "handle it, being away from his daughter, and facing his family's "
            "disappointment. He's been told he needs to go before, and each time "
            "he's promised to handle it himself."
        ),
        "individual_type": "simulated",
        "initial_emotions": {
            "anxious": 0.75,
            "angry": 0.60,
            "ashamed": 0.70,
            "hostile": 0.45,
            "hurt": 0.65,
            "helpless": 0.55,
            "lonely": 0.50,
            "confused": 0.40,
            "insecure": 0.65,
            "sad": 0.55,
            "hopeful": 0.10,         # barely any, but a spark deep down
            "trusting": 0.15,
            "depressed": 0.45,
        },
        "initial_traits": {
            "warmth": 0.65,              # warm underneath, but guarded right now
            "reasoning": 0.60,
            "emotional_stability": 0.25, # very reactive right now
            "dominance": 0.70,           # tries to control the conversation
            "humility": 0.30,            # pride and shame compete
            "liveliness": 0.35,
            "rule_consciousness": 0.40,
            "social_boldness": 0.55,
            "sensitivity": 0.72,         # deeply sensitive under the armor
            "vigilance": 0.80,           # very suspicious/defensive
            "abstractedness": 0.30,
            "privateness": 0.85,         # keeps things locked down
            "apprehension": 0.75,
            "openness_to_change": 0.25,  # resistant to change right now
            "self_reliance": 0.82,       # "I can handle it myself"
            "perfectionism": 0.40,
            "tension": 0.80,             # very high tension
        },
        "physical_features": {
            "age": 29,
            "gender": "male",
            "ethnicity": "African American",
            "height": "6'1\"",
            "build": "athletic but thinner than usual, signs of weight loss",
            "hair": "short fade, not recently maintained",
            "eyes": "dark brown, bloodshot and tired",
            "distinguishing_features": (
                "hospital gown, IV in left arm, faded tattoo of daughter's "
                "name 'Aaliyah' on right forearm, mild tremors in hands, "
                "dark circles under eyes"
            ),
        },
        "metadata": {
            "occupation": "Construction Worker (currently not working due to addiction)",
            "interests": "his daughter Aaliyah, basketball, hip-hop, cars, formerly working with his hands",
            "speaking_style": (
                "Defensive and guarded, often deflects with sarcasm or short answers. "
                "Uses street-casual language. Gets louder when cornered emotionally. "
                "Occasionally drops his guard and speaks softly, especially when "
                "talking about his daughter. Uses phrases like 'I'm good', 'I got this', "
                "'You don't know me', and 'Y'all always think...' when defensive. "
                "His voice cracks when he's genuinely emotional."
            ),
        },
    })
    print(f"   ✅ Created: {patient['name']} (ID: {patient['id']})")
    print(f"      Role: Patient, Opioid Use Disorder")

    # ── 3. Hospital Room Situation ──────────────────────────────────────────
    print("\n📍 Creating situation...")
    situation = api_post("/api/situations", {
        "description": (
            "Marcus Williams' hospital room at Riverside Community Hospital, the "
            "morning after his second opioid overdose. It's 9:30 AM. Marcus is "
            "sitting up in bed, hooked to an IV and vitals monitor. The room is "
            "quiet except for the steady beep of the heart monitor. Maria Santos, "
            "his assigned nurse, enters to check his vitals and talk with him "
            "about next steps. The attending physician has recommended a 30-day "
            "inpatient rehabilitation program. Maria's goal is to help Marcus "
            "understand why rehab could save his life and open the door to "
            "considering it — not to force him, but to plant the seed."
        ),
        "modality": "in_person",
        "location": "Riverside Community Hospital, Room 412",
        "context": {
            "atmosphere": "sterile but quiet, morning light through window blinds",
            "time_of_day": "morning, 9:30 AM",
            "setting_details": (
                "Standard hospital room. Heart monitor beeping steadily. IV drip. "
                "Marcus's phone on the bedside table — Keisha has called 3 times "
                "this morning. A small framed photo of his daughter is visible in "
                "his belongings bag."
            ),
            "clinical_context": (
                "Patient was found unresponsive by girlfriend, administered naloxone "
                "by paramedics. This is his second overdose in 4 months. Toxicology "
                "showed oxycodone and fentanyl. Currently in mild withdrawal. "
                "Attending physician has recommended 30-day inpatient rehab."
            ),
            "stakes": (
                "If Marcus leaves without accepting help, the medical team believes "
                "a third overdose is likely. His girlfriend Keisha told Maria she "
                "can't keep doing this. Child Protective Services has been notified "
                "due to the pattern."
            ),
        },
    })
    print(f"   ✅ Created situation: Room 412 (ID: {situation['id']})")

    # ── 4. Relationship ────────────────────────────────────────────────────
    print("\n🤝 Creating relationship...")
    relationship = api_post("/api/relationships", {
        "individual_ids": [nurse["id"], patient["id"]],
        "initial_trust": 0.30,    # low trust — Marcus doesn't trust medical staff
        "relationship_type": "nurse_patient",
        "history": (
            "Maria was assigned to Marcus when he was admitted last night. She "
            "stabilized him after the naloxone administration and has been checking "
            "on him every few hours. During a 2 AM check, Marcus was awake and "
            "they had a brief exchange — he asked for water, she brought it and "
            "asked if he was comfortable. He grunted a thanks. This morning she "
            "needs to have a more substantive conversation about his treatment plan."
        ),
    })
    print(f"   ✅ Created relationship (ID: {relationship['id']})")
    print(f"      Trust level: 0.30 (low — patient is guarded)")

    # ── 5. Memories for Maria ──────────────────────────────────────────────
    print("\n💭 Creating memories...")
    api_post(f"/api/individuals/{nurse['id']}/memories", {
        "description": (
            "My Uncle Rafael struggled with alcoholism for 15 years before he "
            "finally accepted help. I was 16 when he went to rehab. I remember "
            "thinking he'd never make it, but he's been sober for 12 years now. "
            "He told me the moment that changed everything was when someone he "
            "trusted told him 'I'm not giving up on you' — not a lecture, just "
            "that simple sentence."
        ),
        "salience": 0.90,
        "emotional_state": {"hopeful": 0.8, "nurturing": 0.7, "sad": 0.3},
        "metadata": {"tags": ["personal", "addiction", "recovery", "motivation"]},
    })
    print("   ✅ Maria: Uncle Rafael's recovery story")

    api_post(f"/api/individuals/{nurse['id']}/memories", {
        "description": (
            "Last year I lost a patient — Darnell, 31 years old — to a fentanyl "
            "overdose two weeks after he left the hospital against medical advice. "
            "I still think about whether I could have said something different. "
            "His mother thanked me at the funeral for trying. That haunts me."
        ),
        "salience": 0.95,
        "emotional_state": {"sad": 0.8, "guilty": 0.5, "hopeful": 0.2},
        "metadata": {"tags": ["loss", "patient", "overdose", "motivation"]},
    })
    print("   ✅ Maria: Loss of patient Darnell")

    api_post(f"/api/individuals/{nurse['id']}/memories", {
        "description": (
            "Marcus was brought in unconscious last night. His girlfriend Keisha "
            "was sobbing in the hallway holding his phone — the lock screen was "
            "a photo of Marcus and a little girl, maybe 3 or 4. Keisha told me "
            "'He's a good man. He's a good father. Please help him.' I promised "
            "I would try."
        ),
        "salience": 0.88,
        "emotional_state": {"sad": 0.6, "nurturing": 0.8, "hopeful": 0.4},
        "metadata": {"tags": ["marcus", "admission", "keisha", "daughter"]},
    })
    print("   ✅ Maria: Marcus's admission last night")

    # ── 6. Memories for Marcus ─────────────────────────────────────────────
    api_post(f"/api/individuals/{patient['id']}/memories", {
        "description": (
            "Aaliyah drew me a picture last week — stick figures of me and her "
            "at the park. She wrote 'I luv dady' in crayon. I keep it folded in "
            "my wallet. I was supposed to take her to the park Saturday but I "
            "was too high to drive. Keisha took her instead and told Aaliyah "
            "Daddy was sick. She asked to call me and I didn't answer."
        ),
        "salience": 0.95,
        "emotional_state": {"ashamed": 0.9, "sad": 0.8, "guilty": 0.7, "loving": 0.5},
        "metadata": {"tags": ["daughter", "aaliyah", "shame", "family"]},
    })
    print("   ✅ Marcus: Aaliyah's drawing and missed park day")

    api_post(f"/api/individuals/{patient['id']}/memories", {
        "description": (
            "My back injury was three years ago — fell from scaffolding on a "
            "construction site. Doctor gave me oxycodone and it was like magic, "
            "not just for the pain but for everything. First time in my life "
            "I felt like everything was going to be okay. When they cut my "
            "prescription I panicked. I started buying from a guy at work. "
            "Then the prices went up and someone offered me something cheaper. "
            "That's when I found out it was cut with fentanyl but by then "
            "I didn't care."
        ),
        "salience": 0.85,
        "emotional_state": {"helpless": 0.7, "ashamed": 0.6, "anxious": 0.5},
        "metadata": {"tags": ["injury", "opioids", "origin", "escalation"]},
    })
    print("   ✅ Marcus: How the addiction started")

    api_post(f"/api/individuals/{patient['id']}/memories", {
        "description": (
            "My mom came to visit me last time I was in the hospital. She was "
            "crying and she said 'I didn't raise you to be this.' That hit "
            "harder than anything. My dad hasn't spoken to me in 6 months. "
            "He told my mom I'm dead to him until I get clean. I used to be "
            "his boy — we'd watch games together every Sunday."
        ),
        "salience": 0.90,
        "emotional_state": {"rejected": 0.8, "sad": 0.7, "angry": 0.4, "lonely": 0.6},
        "metadata": {"tags": ["family", "parents", "shame", "rejection"]},
    })
    print("   ✅ Marcus: Family rejection")

    api_post(f"/api/individuals/{patient['id']}/memories", {
        "description": (
            "First overdose was 4 months ago. Woke up in an ambulance with "
            "paramedics standing over me. Keisha was screaming. I promised her "
            "I'd stop. I promised my mom. I tried for 3 weeks and then the "
            "back pain came back and the cravings were so bad I couldn't sleep "
            "or eat. I told myself just one more time."
        ),
        "salience": 0.88,
        "emotional_state": {"helpless": 0.8, "ashamed": 0.7, "anxious": 0.6},
        "metadata": {"tags": ["overdose", "relapse", "promises", "withdrawal"]},
    })
    print("   ✅ Marcus: First overdose and broken promises")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ Demo setup complete!")
    print("=" * 60)
    print()
    print(f"  👩‍⚕️ Nurse:    {nurse['name']} ({nurse['id']})")
    print(f"  🏥 Patient:  {patient['name']} ({patient['id']})")
    print(f"  📍 Room 412: {situation['id']}")
    print(f"  🤝 Relationship: {relationship['id']} (trust: 0.30)")
    print(f"  💭 Memories: 3 for Maria, 4 for Marcus")
    print()
    print("Open in your browser:")
    print("  🖥️  http://127.0.0.1:5000               — Dashboard")
    print("  💬 http://127.0.0.1:5000/chat            — Start a chat session")
    print("  🧪 http://127.0.0.1:5000/simulations    — Run simulations")
    print()
    print("Press Ctrl+C to stop the server.\n")

    return nurse, patient, situation


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("🏥 Personaut Demo: Addiction & Recovery")
    print("   Nurse convincing patient to consider rehab")
    print("=" * 60)

    # 1. Create and start the server
    print("\n▸ Starting server...")
    server = LiveInteractionServer()
    server.start(api_port=8000, ui_port=5000, blocking=False)

    if not wait_for_server():
        print("   ❌ Server failed to start")
        return

    print("   ✅ Server running!")

    try:
        create_demo_data()
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"\n   ⚠️ API error ({e.code}): {body[:500]}")
        return
    except Exception as e:
        print(f"\n   ⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        while server.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.stop()
        print("Server stopped. Goodbye!")


if __name__ == "__main__":
    main()
