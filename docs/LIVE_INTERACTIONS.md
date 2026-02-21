# Live Interactions Guide

This document describes the live interaction system in the Personaut PDK. Live interactions provide a FastAPI backend for managing persona state and a Flask-based web UI for interactive conversations with modality-specific interfaces.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Flask Web UI                                │
│                   (Modality-Specific Interfaces)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ Text Chat   │ │ Email       │ │ In-Person   │ │ Video Call  │   │
│  │ Interface   │ │ Interface   │ │ Interface   │ │ Interface   │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │               Management Dashboard                           │   │
│  │  - Relationship Editor  - Situation Config  - Modality      │   │
│  │  - Emotional State View - Memory Browser  - Trigger Panel   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │ /individuals │ │ /situations  │ │ /simulations │                │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤                │
│  │ /emotions    │ │ /modalities  │ │ /messages    │                │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤                │
│  │ /traits      │ │ /relationships│ │ /sessions   │                │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤                │
│  │ /memories    │ │ /triggers    │ │ /websocket   │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Personaut PDK Core                              │
│  Individuals │ Emotions │ Traits │ Memory │ Simulations            │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Starting the Server

```python
import personaut
from personaut.server import LiveInteractionServer

# Create the server
server = LiveInteractionServer()

# Create an individual to interact with
sarah = personaut.create_individual(name="Sarah")
sarah.emotional_state.change_state({
    'cheerful': 0.7,
    'creative': 0.6
})
sarah.add_trait(personaut.traits.create_trait(
    trait=personaut.traits.WARMTH, value=0.8
))

# Add to server
server.add_individual(sarah)

# Start server (FastAPI backend + Flask UI)
server.start(
    api_port=8000,      # FastAPI backend
    ui_port=5000,       # Flask UI
    debug=True
)

# Access:
# - UI: http://localhost:5000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Using Docker

```bash
# Run with Docker Compose
docker-compose up

# Or build and run manually
docker build -t personaut-live .
docker run -p 8000:8000 -p 5000:5000 personaut-live
```

## FastAPI Backend

The FastAPI backend provides a RESTful API for managing all aspects of live interactions.

### Individual Management

```python
# API endpoints for individuals

# GET /api/individuals - List all individuals
# Response: [
#   {"id": "sarah_001", "name": "Sarah", "type": "simulated"},
#   {"id": "anthony_001", "name": "Anthony", "type": "human"}
# ]

# POST /api/individuals - Create individual
# Request: {
#   "name": "Mike",
#   "traits": [{"trait": "WARMTH", "value": 0.6}],
#   "emotional_state": {"cheerful": 0.5}
# }
# Response: {"id": "mike_002", "name": "Mike", ...}

# GET /api/individuals/{id} - Get individual details
# Response: {
#   "id": "sarah_001",
#   "name": "Sarah",
#   "emotional_state": {...},
#   "traits": [...],
#   "memories": [...],
#   "active_mask": null
# }

# PATCH /api/individuals/{id} - Update individual
# Request: {"emotional_state": {"anxious": 0.3}}

# DELETE /api/individuals/{id} - Remove individual
```

### Emotional State Endpoints

```python
# GET /api/individuals/{id}/emotions
# Response: {
#   "current": {"cheerful": 0.7, "creative": 0.6, ...},
#   "dominant": "cheerful",
#   "category": "peaceful",
#   "history": [...]
# }

# PATCH /api/individuals/{id}/emotions
# Request: {"anxious": 0.4, "hopeful": 0.6}
# Response: {"updated": true, "new_state": {...}}

# POST /api/individuals/{id}/emotions/reset
# Request: {"fill": 0.0}  # Reset all to value
# Response: {"reset": true}

# GET /api/individuals/{id}/emotions/history
# Query: ?limit=100&since=2024-01-01T00:00:00
# Response: {"timeline": [...]}
```

### Trait Management

```python
# GET /api/individuals/{id}/traits
# Response: [
#   {"trait": "WARMTH", "value": 0.8, "response": "naturally friendly"},
#   {"trait": "LIVELINESS", "value": 0.6}
# ]

# POST /api/individuals/{id}/traits
# Request: {"trait": "DOMINANCE", "value": 0.5}

# PATCH /api/individuals/{id}/traits/{trait_name}
# Request: {"value": 0.7}

# DELETE /api/individuals/{id}/traits/{trait_name}
```

### Situation Management

```python
# GET /api/situations - List all situations
# Response: [
#   {"id": "sit_001", "description": "Coffee shop meeting", "modality": "IN_PERSON"},
#   {"id": "sit_002", "description": "Text conversation", "modality": "TEXT_MESSAGE"}
# ]

# POST /api/situations - Create situation
# Request: {
#   "modality": "TEXT_MESSAGE",
#   "description": "Catching up with an old friend",
#   "location": null,
#   "time": "2024-01-15T14:00:00",
#   "context": {
#     "relationship_history": "College roommates",
#     "last_contact": "2 years ago"
#   }
# }
# Response: {"id": "sit_003", ...}

# GET /api/situations/{id} - Get situation details
# PATCH /api/situations/{id} - Update situation
# DELETE /api/situations/{id} - Remove situation
```

### Modality Configuration

```python
# GET /api/modalities - List available modalities
# Response: [
#   {
#     "id": "TEXT_MESSAGE",
#     "name": "Text Message",
#     "description": "SMS/iMessage style conversation",
#     "ui_template": "chat_bubbles",
#     "features": ["typing_indicator", "read_receipts", "emoji"]
#   },
#   {
#     "id": "EMAIL",
#     "name": "Email",
#     "description": "Professional email correspondence",
#     "ui_template": "email_thread",
#     "features": ["subject_line", "formal_greeting", "signature"]
#   },
#   ...
# ]

# GET /api/modalities/{id}/config
# Response: {
#   "id": "TEXT_MESSAGE",
#   "settings": {
#     "typing_delay": true,
#     "typing_speed": "normal",
#     "show_timestamps": true,
#     "show_read_receipts": true,
#     "emoji_support": true,
#     "max_message_length": 500
#   }
# }

# PATCH /api/modalities/{id}/config
# Request: {"typing_speed": "fast", "show_read_receipts": false}
```

### Relationship Management

```python
# GET /api/relationships - List all relationships
# Response: [
#   {
#     "id": "rel_001",
#     "individuals": ["sarah_001", "mike_002"],
#     "trust": {"sarah_001": 0.8, "mike_002": 0.5},
#     "shared_memories": [...]
#   }
# ]

# POST /api/relationships - Create relationship
# Request: {
#   "individuals": ["sarah_001", "mike_002"],
#   "trust": {"sarah_001": 0.8, "mike_002": 0.5},
#   "history": "Met at work 3 years ago, became close friends"
# }

# GET /api/relationships/{id} - Get relationship details
# Response: {
#   "id": "rel_001",
#   "individuals": [...],
#   "trust": {...},
#   "shared_memories": [...],
#   "interaction_count": 47,
#   "last_interaction": "2024-01-14T18:30:00"
# }

# PATCH /api/relationships/{id} - Update relationship
# Request: {"trust": {"sarah_001": 0.9}}

# PATCH /api/relationships/{id}/trust
# Request: {
#   "individual_id": "sarah_001",
#   "change": 0.1,
#   "reason": "Successfully kept a secret"
# }

# POST /api/relationships/{id}/memories
# Request: {
#   "description": "Celebrated Sarah's promotion together",
#   "emotional_impact": {"cheerful": 0.3, "appreciated": 0.2}
# }
```

### Memory Endpoints

```python
# GET /api/individuals/{id}/memories
# Query: ?type=individual&limit=20
# Response: {
#   "memories": [
#     {
#       "id": "mem_001",
#       "type": "individual",
#       "description": "Got promoted last month",
#       "created_at": "2024-01-01T10:00:00",
#       "emotional_state": {...}
#     }
#   ]
# }

# POST /api/individuals/{id}/memories
# Request: {
#   "type": "individual",
#   "description": "Had a difficult conversation with boss",
#   "emotional_state": {"anxious": 0.6, "hurt": 0.3}
# }

# POST /api/individuals/{id}/memories/search
# Request: {
#   "query": "feeling nervous about presentations",
#   "limit": 5
# }
# Response: {
#   "results": [
#     {"memory": {...}, "similarity": 0.87},
#     {"memory": {...}, "similarity": 0.72}
#   ]
# }

# DELETE /api/individuals/{id}/memories/{memory_id}
```

### Trigger Management

```python
# GET /api/individuals/{id}/triggers
# Response: [
#   {
#     "id": "trig_001",
#     "type": "emotional",
#     "description": "High fear response",
#     "rules": [{"emotion": "fear", "threshold": 0.8, "operator": ">"}],
#     "response": {"type": "mask", "mask": "stoic"},
#     "active": true
#   }
# ]

# POST /api/individuals/{id}/triggers
# Request: {
#   "type": "emotional",
#   "description": "Anxiety spike",
#   "rules": [{"emotion": "anxious", "threshold": 0.7, "operator": ">"}],
#   "response": {"type": "emotional_modification", "changes": {"content": 0.3}}
# }

# PATCH /api/individuals/{id}/triggers/{trigger_id}
# Request: {"active": false}  # Disable trigger

# DELETE /api/individuals/{id}/triggers/{trigger_id}
```

### Simulation Sessions

```python
# POST /api/sessions - Create new session
# Request: {
#   "situation_id": "sit_001",
#   "individuals": ["sarah_001", "human_anthony"],
#   "modality": "TEXT_MESSAGE"
# }
# Response: {
#   "session_id": "sess_001",
#   "status": "active",
#   "websocket_url": "ws://localhost:8000/ws/sess_001"
# }

# GET /api/sessions/{id} - Get session state
# Response: {
#   "session_id": "sess_001",
#   "status": "active",
#   "situation": {...},
#   "individuals": [...],
#   "message_count": 12,
#   "duration": "5m 32s",
#   "emotional_changes": [...]
# }

# GET /api/sessions/{id}/messages
# Query: ?limit=50&before=msg_045
# Response: {"messages": [...]}

# POST /api/sessions/{id}/messages
# Request: {
#   "from": "human_anthony",
#   "content": "Hey Sarah, how are you?",
#   "action": null
# }
# Response: {
#   "message_id": "msg_046",
#   "response": {
#     "from": "sarah_001",
#     "content": "Hey! I'm doing great, thanks for asking!",
#     "emotional_state": {...},
#     "triggers_fired": []
#   }
# }

# POST /api/sessions/{id}/actions
# Request: {
#   "from": "human_anthony",
#   "action": "waves hello"
# }

# DELETE /api/sessions/{id} - End session
# POST /api/sessions/{id}/save - Save session to file
# POST /api/sessions/{id}/load - Load session from file
```

### WebSocket Real-Time Updates

```python
# Connect to WebSocket for real-time updates
# ws://localhost:8000/ws/{session_id}

# Incoming message types:
{
    "type": "message",
    "data": {
        "from": "sarah_001",
        "content": "That sounds fun!",
        "timestamp": "2024-01-15T14:05:32"
    }
}

{
    "type": "emotional_state_change",
    "data": {
        "individual_id": "sarah_001",
        "previous": {"excited": 0.5},
        "current": {"excited": 0.7},
        "trigger": null
    }
}

{
    "type": "trigger_activated",
    "data": {
        "individual_id": "sarah_001",
        "trigger_id": "trig_001",
        "description": "High excitement response",
        "response_applied": {"type": "mask", "mask": "enthusiastic"}
    }
}

{
    "type": "mask_applied",
    "data": {
        "individual_id": "sarah_001",
        "mask": "professional",
        "reason": "Work context detected"
    }
}

{
    "type": "typing",
    "data": {
        "individual_id": "sarah_001",
        "is_typing": true
    }
}
```

## Flask Web UI

The Flask UI provides a user-friendly interface for managing and interacting with personas.

### Main Dashboard

Access at `http://localhost:5000`

```
┌─────────────────────────────────────────────────────────────────┐
│  🎭 Personaut Live Interactions                    [Settings] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  📋 Individuals │  │  🌍 Situations  │  │  💬 Sessions   │  │
│  │                 │  │                 │  │                │  │
│  │  Sarah    ●     │  │  Coffee Shop    │  │  Active: 2     │  │
│  │  Mike     ●     │  │  Text Chat      │  │  Saved: 5      │  │
│  │  + Add New      │  │  + Add New      │  │  + New Session │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Quick Start: Select individuals and situation to begin  │  │
│  │                                                          │  │
│  │  Individual: [Sarah          ▼]                          │  │
│  │  Situation:  [Text Message   ▼]  [Configure...]          │  │
│  │                                                          │  │
│  │              [Start Conversation]                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Individual Editor

```
┌─────────────────────────────────────────────────────────────────┐
│  👤 Edit Individual: Sarah                      [Save] [Delete] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Name: [Sarah                    ]                              │
│                                                                 │
│  ── Emotional State ──────────────────────────────────────────  │
│                                                                 │
│  😊 cheerful    [████████░░] 0.7    [Reset]                    │
│  🤔 creative    [██████░░░░] 0.6                               │
│  🤝 trusting    [█████░░░░░] 0.5                               │
│  😰 anxious     [██░░░░░░░░] 0.2                               │
│                                                                 │
│  [Show All Emotions ▼]           [Randomize] [Reset All]       │
│                                                                 │
│  ── Personality Traits ───────────────────────────────────────  │
│                                                                 │
│  WARMTH         [████████░░] 0.8    High: outgoing, kindly     │
│  LIVELINESS     [██████░░░░] 0.6    Moderate: balanced energy  │
│  DOMINANCE      [████░░░░░░] 0.4    Moderate: situational      │
│                                                                 │
│  [+ Add Trait]                                                 │
│                                                                 │
│  ── Triggers & Masks ─────────────────────────────────────────  │
│                                                                 │
│  Triggers:                                                      │
│  ☑ High fear → Apply stoic mask                                │
│  ☐ Low trust → Increase vigilance                              │
│  [+ Add Trigger]                                               │
│                                                                 │
│  Masks:                                                        │
│  • Professional (inactive)                                      │
│  • Casual (inactive)                                           │
│  [+ Add Mask]                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Situation Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│  🌍 Configure Situation                         [Save] [Delete] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Description: [Catching up with an old college friend    ]     │
│                                                                 │
│  ── Modality ──────────────────────────────────────────────────│
│                                                                 │
│  ○ 💬 Text Message     ○ 📧 Email         ○ 🧑‍🤝‍🧑 In-Person     │
│  ○ 📞 Phone Call       ○ 📹 Video Call                         │
│                                                                 │
│  ── Modality Settings ─────────────────────────────────────────│
│                                                                 │
│  ☑ Show typing indicator                                       │
│  ☑ Show read receipts                                          │
│  ☑ Enable emoji                                                │
│  Typing speed: [Normal ▼]                                      │
│  Response style: [Casual ▼]                                    │
│                                                                 │
│  ── Location & Time ───────────────────────────────────────────│
│                                                                 │
│  Location: [Miami, FL            ] (optional)                  │
│  Time:     [2024-01-15 14:00     ]                            │
│                                                                 │
│  ── Context ───────────────────────────────────────────────────│
│                                                                 │
│  Key                          Value                             │
│  [relationship_history  ] → [College roommates for 2 years  ] │
│  [last_contact          ] → [Haven't spoken in 2 years       ] │
│  [reason_for_contact    ] → [Reconnecting                    ] │
│  [+ Add Context Field]                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Relationship Editor

```
┌─────────────────────────────────────────────────────────────────┐
│  🤝 Edit Relationship                           [Save] [Delete] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Between: [Sarah ▼] and [Mike ▼]                               │
│                                                                 │
│  ── Trust Levels ──────────────────────────────────────────────│
│                                                                 │
│  Sarah → Mike: [████████░░] 0.8  (trusting, comfortable)       │
│  Mike → Sarah: [█████░░░░░] 0.5  (neutral, building trust)     │
│                                                                 │
│  ── Relationship History ──────────────────────────────────────│
│                                                                 │
│  [                                                        ]    │
│  [ Met at work 3 years ago. Started as colleagues,        ]    │
│  [ became close friends after working on a project        ]    │
│  [ together. Sarah helped Mike through a difficult time.  ]    │
│  [                                                        ]    │
│                                                                 │
│  ── Shared Memories ───────────────────────────────────────────│
│                                                                 │
│  📝 "Worked late nights on the Q3 project"                     │
│     Emotional impact: +0.2 trust, +0.1 appreciation            │
│                                                                 │
│  📝 "Celebrated Sarah's promotion at the usual bar"            │
│     Emotional impact: +0.3 cheerful, +0.1 appreciated          │
│                                                                 │
│  [+ Add Shared Memory]                                         │
│                                                                 │
│  ── Interaction Statistics ────────────────────────────────────│
│                                                                 │
│  Total interactions: 47                                        │
│  Last interaction: 2 days ago                                  │
│  Average trust change: +0.02 per interaction                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Modality Interface: Text Message

```
┌─────────────────────────────────────────────────────────────────┐
│  💬 Text with Sarah                    [📊 Emotions] [⚙ Config]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                         Today 2:00 PM                           │
│                                                                 │
│                                    ┌──────────────────────────┐│
│                                    │ Hey Sarah! Long time     ││
│                                    │ no see 👋                 ││
│                                    └──────────────────────────┘│
│                                                     Delivered ✓│
│                                                                 │
│  ┌──────────────────────────┐                                  │
│  │ OMG hi!! 😊 I was just   │                                  │
│  │ thinking about you!      │                                  │
│  │ How have you been?       │                                  │
│  └──────────────────────────┘                                  │
│                                                                 │
│                                    ┌──────────────────────────┐│
│                                    │ I've been good! Super    ││
│                                    │ busy with work but good. ││
│                                    │ We should catch up!      ││
│                                    └──────────────────────────┘│
│                                                          Read ✓│
│                                                                 │
│  ┌──────────────────────────┐                                  │
│  │ Sarah is typing...       │                                  │
│  └──────────────────────────┘                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [Type a message...                              ] [Send] [📎]  │
└─────────────────────────────────────────────────────────────────┘

┌─ 📊 Emotional State Panel ──────────────────────────────────────┐
│  Sarah's Current State:                                         │
│  😊 excited    ████████░░ 0.8  ↑ +0.2                          │
│  🤝 trusting   ████████░░ 0.8                                   │
│  💭 intimate   ██████░░░░ 0.6  NEW                             │
│                                                                 │
│  [View History] [Show All]                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Modality Interface: In-Person

```
┌─────────────────────────────────────────────────────────────────┐
│  🧑‍🤝‍🧑 In-Person: Coffee Shop           [📊 Emotions] [⚙ Config]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 📍 Downtown Cafe - Afternoon                              │  │
│  │ The cafe is moderately busy. Soft jazz plays in the      │  │
│  │ background. The smell of fresh coffee fills the air.     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  SARAH: *looks up from her phone and breaks into a wide        │
│  smile* Oh my god, you're here! *stands up and gives you       │
│  a warm hug*                                                   │
│                                                                 │
│  > I wave and walk over to the table                           │
│                                                                 │
│  SARAH: It's so good to see you! Sit, sit! *gestures to        │
│  the chair across from her* I already ordered your usual -     │
│  hope that's still what you like?                              │
│                                                                 │
│  *She seems genuinely happy, her eyes bright with excitement.  │
│  There's a slight nervousness in how she fidgets with her      │
│  coffee cup.*                                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ What do you do/say?                                             │
│ [                                                          ]   │
│                                                                 │
│ [💬 Say something] [🎭 Describe action] [Both]       [Send]   │
└─────────────────────────────────────────────────────────────────┘
```

### Modality Interface: Email

```
┌─────────────────────────────────────────────────────────────────┐
│  📧 Email Thread                      [📊 Emotions] [⚙ Config] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Subject: Re: Long time no talk!                               │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  From: sarah@email.com                                         │
│  To: anthony@email.com                                         │
│  Date: January 15, 2024 at 2:15 PM                            │
│                                                                 │
│  Hi Anthony!                                                   │
│                                                                 │
│  What a wonderful surprise to hear from you! I can't believe   │
│  it's been two years already. Time really does fly.            │
│                                                                 │
│  I've been keeping busy with work - got promoted to Senior     │
│  Manager last year, which has been exciting but definitely     │
│  keeps me on my toes. Outside of work, I've picked up hiking   │
│  (finally!) and have been exploring trails around the area.    │
│                                                                 │
│  I would absolutely love to catch up! Are you still in Miami?  │
│  I'm planning to be in town next month for a conference.       │
│  Maybe we could grab coffee?                                   │
│                                                                 │
│  Looking forward to hearing from you!                          │
│                                                                 │
│  Best,                                                         │
│  Sarah                                                         │
│                                                                 │
│  ─────── Original Message ───────                              │
│  > From: anthony@email.com                                     │
│  > Hey Sarah! It's been way too long...                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ [Reply] [Reply All] [Forward]                                  │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ To: sarah@email.com                                         ││
│ │ Subject: Re: Long time no talk!                             ││
│ │                                                             ││
│ │ [Compose your reply...                                    ] ││
│ │                                                             ││
│ └─────────────────────────────────────────────────────────────┘│
│                                              [Send] [Save Draft]│
└─────────────────────────────────────────────────────────────────┘
```

## Configuration

### Server Configuration

```python
from personaut.server import LiveInteractionServer

server = LiveInteractionServer(
    # API Configuration
    api_host='0.0.0.0',
    api_port=8000,
    api_workers=4,
    
    # UI Configuration
    ui_host='0.0.0.0',
    ui_port=5000,
    ui_theme='dark',      # 'light', 'dark', 'system'
    
    # Database
    database_url='sqlite:///./personaut.db',
    # Or: 'postgresql://user:pass@host/db'
    
    # Model Provider
    model_provider='gemini',  # 'gemini', 'bedrock', 'openai'
    model_config={
        'api_key': 'your-api-key',
        'model': 'gemini-pro'
    },
    
    # Embedding Provider (for memory search)
    embedding_provider='gemini',
    
    # Session Management
    session_timeout=3600,     # 1 hour
    auto_save_sessions=True,
    session_storage='./sessions/',
    
    # WebSocket
    websocket_ping_interval=30,
    
    # Logging
    log_level='INFO',
    log_file='./logs/personaut.log'
)
```

### Environment Variables

```bash
# .env file
PERSONAUT_API_HOST=0.0.0.0
PERSONAUT_API_PORT=8000
PERSONAUT_UI_PORT=5000

# Model Provider
PERSONAUT_MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your-gemini-api-key
# Or for Bedrock:
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION=us-east-1

# Database
DATABASE_URL=sqlite:///./personaut.db

# Session
SESSION_SECRET_KEY=your-secret-key
SESSION_TIMEOUT=3600
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    command: uvicorn personaut.server.api:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db/personaut
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    depends_on:
      - db
    volumes:
      - ./sessions:/app/sessions

  ui:
    build: .
    command: flask run --host 0.0.0.0 --port 5000
    ports:
      - "5000:5000"
    environment:
      - PERSONAUT_API_URL=http://api:8000
    depends_on:
      - api

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=personaut
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Python Client

Use the Python client for programmatic interaction:

```python
from personaut.client import LiveInteractionClient

# Connect to server
client = LiveInteractionClient(
    api_url='http://localhost:8000',
    api_key='your-api-key'  # Optional
)

# Create individual
sarah = client.individuals.create(
    name='Sarah',
    traits=[{'trait': 'WARMTH', 'value': 0.8}],
    emotional_state={'cheerful': 0.7}
)

# Create situation
situation = client.situations.create(
    modality='TEXT_MESSAGE',
    description='Catching up with an old friend'
)

# Create relationship
relationship = client.relationships.create(
    individuals=[sarah.id, 'human_user'],
    trust={sarah.id: 0.6, 'human_user': 0.7}
)

# Start session
session = client.sessions.create(
    situation_id=situation.id,
    individuals=[sarah.id, 'human_user']
)

# Send message
response = client.sessions.send_message(
    session_id=session.id,
    content="Hey Sarah!",
    from_individual='human_user'
)

print(response.content)  # "Oh hi! So good to hear from you!"
print(response.emotional_state)  # {'excited': 0.7, ...}

# Get emotional state
state = client.individuals.get_emotions(sarah.id)
print(state.dominant)  # 'excited'

# Update relationship trust
client.relationships.update_trust(
    relationship_id=relationship.id,
    individual_id=sarah.id,
    change=0.1,
    reason='Had a great conversation'
)

# Close session
client.sessions.close(session.id)
```

## Best Practices

### Setting Up Realistic Personas
- Configure multiple traits for nuanced personality
- Set initial emotional states that fit the situation
- Add relevant memories that inform responses
- Define triggers for authentic emotional reactions

### Managing Relationships
- Set asymmetric trust levels for realistic dynamics
- Add shared memories for established relationships
- Update trust based on interaction outcomes
- Use relationship history in situation context

### Choosing Modalities
- Match modality to the interaction type
- Configure modality-specific settings appropriately
- Consider how modality affects response style
- Use in-person for rich, expressive interactions

### Performance
- Use PostgreSQL for production deployments
- Enable parallel API workers for high load
- Set appropriate session timeouts
- Monitor WebSocket connections

## Related Documentation

- [SIMULATIONS.md](./SIMULATIONS.md) - Batch simulation patterns
- [EMOTIONS.md](./EMOTIONS.md) - Emotional state system
- [TRAITS.md](./TRAITS.md) - Personality trait system
- [PROMPTS.md](./PROMPTS.md) - Prompt generation
- [../PERSONAS.md](../PERSONAS.md) - Main agent guidelines
