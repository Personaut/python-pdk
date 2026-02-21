# Simulation Guide

This document describes the simulation system in the Personaut PDK. Simulations enable authentic persona-driven interactions including conversations, surveys, outcome analysis, and real-time interactions.

## Overview

The simulation system orchestrates interactions between individuals based on their emotional states, personality traits, memories, relationships, and situational context. Each simulation type serves different research and development needs.

**Simulation Types:**
- **CONVERSATION**: Dialogue between two or more individuals
- **SURVEY**: Questionnaire responses from an individual
- **OUTCOME_SUMMARY**: Analysis of whether a target outcome is achieved
- **LIVE_CONVERSATION**: Real-time interactive simulation

**Output Styles:**
- **SCRIPT**: Screenplay-like dialogue format
- **QUESTIONNAIRE**: Structured Q&A format
- **JSON**: Machine-readable structured output
- **TXT**: Human-readable text output

## Creating Situations

Every simulation requires a situation that defines the context for the interaction.

### Basic Situation

```python
import personaut
from datetime import datetime

situation = personaut.create_situation(
    modality=personaut.types.modality.IN_PERSON,
    description='Meeting at a coffee shop to discuss a project',
    time=datetime.now(),
    location='Miami, FL'
)
```

### Modality Types

The modality defines how individuals are interacting:

```python
# In-person interaction
in_person = personaut.types.modality.IN_PERSON
# - Full non-verbal cues available
# - Physical environment affects mood
# - Real-time responses expected

# Text message conversation
text_message = personaut.types.modality.TEXT_MESSAGE
# - No visual cues
# - Asynchronous responses possible
# - Written communication style

# Video call
video_call = personaut.types.modality.VIDEO_CALL
# - Limited non-verbal cues
# - Technology-mediated
# - Potential for connection issues

# Phone call
phone_call = personaut.types.modality.PHONE_CALL
# - Voice-only communication
# - Real-time but audio-only
# - Tone of voice important

# Email
email = personaut.types.modality.EMAIL
# - Formal written communication
# - Asynchronous
# - Document-style responses
```

### Situation Context

```python
# Detailed situation with additional context
situation = personaut.create_situation(
    modality=personaut.types.modality.TEXT_MESSAGE,
    description='Receiving a text message from an old friend',
    time=datetime.now(),
    location=None,  # Location not relevant for text
    context={
        'relationship_history': 'Haven\'t spoken in 2 years',
        'last_interaction': 'Left on good terms',
        'reason_for_contact': 'Reconnecting'
    }
)
```

### Rich Situational Context with Facts

For more detailed environment modeling, use the Facts system to create structured situational context:

```python
from personaut.facts import create_coffee_shop_context

# Create rich situational context
context = create_coffee_shop_context(
    city="Miami, FL",
    venue_name="Sunrise Cafe",
    capacity_percent=85,
    queue_length=7,
    noise_level="moderate",
    atmosphere="bustling",
    time_of_day="morning",
)

# Use in simulation
situation = personaut.create_situation(
    modality=personaut.types.modality.IN_PERSON,
    description=context.description,
    location=context.get_value("city"),
    context=context.to_dict(),  # Full situational context
)
```

Or extract context from natural language descriptions:

```python
from personaut.facts import FactExtractor, LLMFactExtractor

# Regex-based extraction (fast)
extractor = FactExtractor()
context = extractor.extract(
    "We met at a busy coffee shop in downtown Miami around 3pm. "
    "About 80% capacity with a line of 5 people waiting."
)

# LLM-based extraction (richer)
llm_extractor = LLMFactExtractor(llm_client=your_client)
context = await llm_extractor.extract(
    "Grabbed coffee at the corner spot. Super packed today, great vibe with jazz playing."
)

# Use extracted context in simulation
situation = personaut.create_situation(
    modality=personaut.types.modality.IN_PERSON,
    description="Coffee shop meeting",
    location=context.get_value("city"),
    context=context.to_dict(),
)
```

See [FACTS.md](FACTS.md) for complete documentation on the Facts system.

## Conversation Simulations


Simulate dialogues between two or more individuals.

### Basic Conversation

```python
import personaut

# Create individuals
user_a = personaut.create_individual(name="Sarah")
user_b = personaut.create_individual(name="Mike")

# Set up emotional states
user_a.emotional_state.change_state({'anxious': 0.4, 'hopeful': 0.6})
user_b.emotional_state.change_state({'proud': 0.7, 'cheerful': 0.5})

# Create situation
situation = personaut.create_situation(
    modality=personaut.types.modality.IN_PERSON,
    description='First meeting at a networking event',
    location='Conference Center'
)

# Create simulation
simulation = personaut.create_simulation(
    situation=situation,
    individuals=[user_a, user_b],
    type=personaut.simulations.types.CONVERSATION,
    style=personaut.simulations.styles.SCRIPT,
    output='txt'
)

# Run simulation
simulation.run(
    num=10,      # Generate 10 conversation variations
    dir='./'     # Output directory
)
```

### Script Output Format

The SCRIPT style produces screenplay-like output:

```
=== Conversation Simulation ===
Situation: First meeting at a networking event
Location: Conference Center
Participants: Sarah, Mike

---

SARAH: (nervously adjusts her name tag) Hi, I don't think we've met. I'm Sarah.

MIKE: (extends hand confidently) Mike. Great to meet you. What brings you to the conference?

SARAH: (relaxing slightly) I'm actually presenting tomorrow on user research methods. A bit nervous about it, honestly.

MIKE: (encouraging smile) That's impressive! I'd love to hear more about your work. What's the main focus?

...
```

### Multi-Party Conversations

```python
# Three-way conversation
user_a = personaut.create_individual(name="Sarah")
user_b = personaut.create_individual(name="Mike")
user_c = personaut.create_individual(name="Alex")

simulation = personaut.create_simulation(
    situation=team_meeting_situation,
    individuals=[user_a, user_b, user_c],
    type=personaut.simulations.types.CONVERSATION,
    style=personaut.simulations.styles.SCRIPT,
    output='txt',
    turn_order='dynamic'  # AI determines who speaks next
)
```

### Non-Tracked Individuals

For background characters or service roles that don't need full personality tracking:

```python
# Create a non-tracked individual (simpler, less state)
barista = personaut.create_nontracked_individual(role='barista')

# Use in simulation
simulation = personaut.create_simulation(
    situation=coffee_shop_situation,
    individuals=[user_a, barista],
    type=personaut.simulations.types.CONVERSATION,
    style=personaut.simulations.styles.SCRIPT,
    output='txt'
)
```

## Survey Simulations

Simulate how an individual would respond to questionnaires or surveys.

### Basic Survey

```python
import personaut

user_a = personaut.create_individual(name="Respondent")
user_a.emotional_state.change_state({
    'content': 0.6,
    'satisfied': 0.5
})

# Define survey questions
survey_questions = [
    {
        'id': 'q1',
        'text': 'How satisfied are you with your current work-life balance?',
        'type': 'likert_5'
    },
    {
        'id': 'q2', 
        'text': 'What changes would improve your daily routine?',
        'type': 'open_ended'
    }
]

situation = personaut.create_situation(
    modality=personaut.types.modality.SURVEY,
    description='Annual employee satisfaction survey'
)

simulation = personaut.create_simulation(
    situation=situation,
    individuals=[user_a],
    type=personaut.simulations.types.SURVEY,
    style=personaut.simulations.styles.QUESTIONNAIRE,
    output='json',
    questions=survey_questions
)

simulation.run(num=10, dir='./')
```

### Survey Output Format (JSON)

```json
{
  "simulation_id": "survey_001",
  "respondent": {
    "name": "Respondent",
    "emotional_state": {
      "content": 0.6,
      "satisfied": 0.5
    }
  },
  "responses": [
    {
      "question_id": "q1",
      "question": "How satisfied are you with your current work-life balance?",
      "response": 4,
      "response_label": "Satisfied",
      "reasoning": "Current contentment and satisfaction levels suggest positive overall outlook"
    },
    {
      "question_id": "q2",
      "question": "What changes would improve your daily routine?",
      "response": "I think having more flexibility in my schedule would help. Being able to start earlier and finish earlier would let me enjoy more evening time with family.",
      "emotional_influence": "Content state leads to constructive, measured suggestions rather than complaints"
    }
  ]
}
```

### Emotional Variation in Surveys

Run the same survey with different emotional states to see response patterns:

```python
# Anxious respondent
anxious_state = personaut.emotions.EmotionalState()
anxious_state.change_state({'anxious': 0.7, 'insecure': 0.5})

# Confident respondent
confident_state = personaut.emotions.EmotionalState()
confident_state.change_state({'proud': 0.8, 'satisfied': 0.6})

for state, label in [(anxious_state, 'anxious'), (confident_state, 'proud')]:
    respondent = personaut.create_individual(name=f"Respondent_{label}")
    respondent.emotional_state = state
    
    simulation = personaut.create_simulation(
        situation=survey_situation,
        individuals=[respondent],
        type=personaut.simulations.types.SURVEY,
        style=personaut.simulations.styles.QUESTIONNAIRE,
        output='json'
    )
    
    simulation.run(num=5, dir=f'./{label}_responses/')
```

## Outcome Simulations

Analyze likelihood of achieving specific outcomes and understand what influences results.

### Basic Outcome Analysis

```python
import personaut

# Define the customer
customer = personaut.create_individual(name="Customer")

# Define the sales rep
sales_rep = personaut.create_individual(name="Sales Rep")
sales_rep.set_trait("warmth", 0.8)

# Create situation
situation = personaut.create_situation(
    modality=personaut.types.modality.IN_PERSON,
    description='Coffee shop upselling interaction',
    location='Denver, CO'
)

# Create outcome simulation
simulation = personaut.create_simulation(
    situation=situation,
    individuals=[customer, sales_rep],
    type=personaut.simulations.types.OUTCOME_SUMMARY,
    output='txt',
    target_outcome='Yes to upselling drink size',
    randomize=[customer.emotional_state]  # Vary customer emotions
)

simulation.run(num=10, dir='.')
```

### Outcome Output Format

```
=== Outcome Summary ===
Target Outcome: Yes to upselling drink size
Total Simulations: 10

Results:
- Outcome Achieved: 6/10 (60%)
- Outcome Not Achieved: 4/10 (40%)

Emotional State Analysis:
- When customer anxiety > 0.5: 2/4 achieved (50%)
- When customer content > 0.5: 4/6 achieved (67%)

Key Factors:
1. Sales rep warmth (0.8) consistently positive influence
2. Customer anxiety correlated with declined upsells
3. Friendly initial greeting increased success rate

Recommendations:
- Reduce perceived pressure in upsell approach
- Match energy to customer's emotional state
- Lead with value proposition before asking
```

### Randomization Options

```python
# Randomize emotional state
simulation = personaut.create_simulation(
    ...
    randomize=[customer.emotional_state]
)
```

> **Planned Feature (not yet implemented):** Fine-grained randomization options
> (`randomize_emotions`, `randomize_range`, `randomize_traits`) are not yet available.
> Currently, randomization is managed through the `randomize` parameter which accepts
> emotional state objects.

## Live Conversation Simulations

Create interactive, real-time simulations where you can message a simulated individual using any modality. The simulator renders a UI that matches the communication channel (text messages, email, in-person, etc.).

### Basic Live Chat

```python
import personaut

# Create the AI individual you'll chat with
ai_friend = personaut.create_individual(name="Sarah")
ai_friend.emotional_state.change_state({
    'cheerful': 0.7,
    'creative': 0.6,
    'trusting': 0.5
})

# Add personality traits
ai_friend.set_trait("warmth", 0.8)
ai_friend.set_trait("liveliness", 0.6)

# Create human participant (you)
human = personaut.create_human(name='Anthony')

# Define the situation with modality
situation = personaut.create_situation(
    modality=personaut.types.modality.TEXT_MESSAGE,
    description='Catching up with an old college friend'
)

# Create live simulation
simulation = personaut.create_simulation(
    situation=situation,
    individuals=[ai_friend, human],
    type=personaut.simulations.types.LIVE_CONVERSATION,
    output='json'
)

# Start the interactive simulator
simulation.start_simulator()
```

### Modality-Specific UI Rendering

The simulator renders different UIs based on the modality type, creating an authentic experience for each communication channel.

#### Text Message Modality

```python
situation = personaut.create_situation(
    modality=personaut.types.modality.TEXT_MESSAGE,
    description='Texting with a friend'
)

simulation.start_simulator()
# Renders: iMessage-style chat bubbles
# - Blue bubbles for your messages (right-aligned)
# - Gray bubbles for AI messages (left-aligned)
# - Typing indicators when AI is responding
# - Delivered/Read receipts
# - Timestamp groupings
```

**Text Message UI Features:**
- Chat bubble interface
- Typing indicators ("Sarah is typing...")
- Message timestamps
- Emoji support
- Read receipts simulation
- Casual, short response style

#### Email Modality

```python
situation = personaut.create_situation(
    modality=personaut.types.modality.EMAIL,
    description='Professional correspondence about a project',
    context={
        'subject': 'Re: Q4 Project Timeline',
        'thread_id': 'project-timeline-001'
    }
)

simulation.start_simulator()
# Renders: Email client interface
# - Email thread view with quoted replies
# - Subject line and headers
# - Formal formatting with greetings/signatures
# - Reply/Forward actions
```

**Email UI Features:**
- Email thread with quoted text
- Subject line display
- To/From/CC headers
- Formal greeting and signature
- Longer, structured responses
- Reply and Forward buttons

#### In-Person Modality

```python
situation = personaut.create_situation(
    modality=personaut.types.modality.IN_PERSON,
    description='Meeting at a coffee shop',
    location='Downtown Cafe'
)

simulation.start_simulator()
# Renders: Narrative dialogue interface
# - Describes physical actions and expressions
# - Environmental descriptions
# - Non-verbal cues (body language, tone)
# - Scene-setting details
```

**In-Person UI Features:**
- Screenplay-style dialogue
- Physical action descriptions: `*Sarah leans forward with interest*`
- Environmental awareness: `*The barista calls out an order nearby*`
- Facial expressions and body language
- Option to describe your own actions

#### Phone Call Modality

```python
situation = personaut.create_situation(
    modality=personaut.types.modality.PHONE_CALL,
    description='Catching up on the phone'
)

simulation.start_simulator()
# Renders: Voice call interface
# - Transcript-style dialogue
# - Tone/inflection descriptions
# - Pauses and interruptions modeled
# - Call duration timer
```

**Phone Call UI Features:**
- Audio-only cues (tone, pauses, sighs)
- No visual descriptions
- Natural interruptions and overlaps
- Call timer display
- Mute/End call buttons

#### Video Call Modality

```python
situation = personaut.create_situation(
    modality=personaut.types.modality.VIDEO_CALL,
    description='Video catch-up call',
    context={
        'platform': 'Zoom',
        'background': 'Home office'
    }
)

simulation.start_simulator()
# Renders: Video call interface
# - Visual descriptions (expressions, gestures)
# - Background/environment mentions
# - Screen share simulation option
# - Connection quality notes
```

**Video Call UI Features:**
- Facial expression descriptions
- Visible body language (upper body)
- Background environment context
- Technology issues simulation (lag, freezing)
- Mute/Camera toggle buttons

### Real-Time Emotional State Tracking

The live simulator tracks and displays emotional state changes during the conversation:

```python
simulation.start_simulator(
    show_emotions=True,  # Display emotion panel
    emotion_display='chart'  # Options: 'chart', 'bars', 'text', 'hidden'
)
```

**Emotion Display Options:**

```python
# Chart view - line graph showing emotion changes over time
emotion_display='chart'

# Bar view - horizontal bars showing current levels
emotion_display='bars'

# Text view - descriptive text of current state
emotion_display='text'
# Output: "Sarah is feeling creative and engaged, with slight anxiety"

# Hidden - no display (for cleaner testing)
emotion_display='hidden'
```

### Trigger and Mask Visualization

```python
simulation.start_simulator(
    show_triggers=True,  # Alert when triggers activate
    show_masks=True      # Show when masks are applied
)

# When a trigger activates:
# 🔔 Trigger Activated: "High anxiety response"
# → Applying mask: "stoic"

# Mask indicator shows current active mask
# 🎭 Active Mask: Professional
```

### Starting the Simulator

```python
# Basic start
simulation.start_simulator()

# Full configuration
simulation.start_simulator(
    # Server configuration
    host='0.0.0.0',
    port=5000,
    debug=False,
    
    # UI options
    theme='dark',              # 'light', 'dark', 'system'
    show_emotions=True,        # Show emotion panel
    show_triggers=True,        # Show trigger notifications
    show_masks=True,           # Show mask indicators
    show_memories=True,        # Show retrieved memories
    
    # Behavior options
    typing_delay=True,         # Simulate typing time
    typing_speed='normal',     # 'slow', 'normal', 'fast', 'instant'
    auto_save=True,            # Save conversation history
    
    # Webhook notifications
    webhook_url='http://localhost:8080/updates',
    notify_on=[
        'message_sent',
        'message_received', 
        'emotional_state_change',
        'trigger_activated',
        'mask_applied'
    ]
)
```

### API Endpoints

The flask application exposes REST endpoints for programmatic interaction:

```python
# POST /message - Send a message
# Request: { "content": "Hey, how are you?", "action": "waves hello" }
# Response: { 
#   "response": "Hi! I'm doing well, thanks for asking! *smiles warmly*",
#   "emotional_state": { "cheerful": 0.8, "creative": 0.5 },
#   "triggers_activated": [],
#   "active_mask": null
# }

# GET /history - Get conversation history
# Response: { "messages": [...], "duration": "5m 32s" }

# GET /state - Get current state
# Response: {
#   "emotional_state": {...},
#   "active_mask": "professional",
#   "active_triggers": [...],
#   "retrieved_memories": [...]
# }

# POST /reset - Reset conversation
# Response: { "status": "reset", "initial_state": {...} }

# GET /emotions - Get emotion history over time
# Response: { "timeline": [...], "current": {...} }

# POST /action - Send an action without dialogue
# Request: { "action": "sits down across from Sarah" }
# Response: { "response": "*looks up and smiles* Oh, there you are!" }
```

### Programmatic Control

Use the simulator programmatically for testing:

```python
# Instead of web UI, use programmatic interface
chat = simulation.create_chat_session()

# Send messages
response = chat.send("Hey Sarah, long time no see!")
print(response.content)  # "Oh wow, Anthony! It's been ages!"
print(response.emotional_state)  # {'excited': 0.7, 'cheerful': 0.6, ...}

# Send actions (for in-person/video modalities)
response = chat.send_action("gives Sarah a friendly hug")
print(response.content)  # "*hugs back warmly* I've missed you!"

# Check state
state = chat.get_state()
print(state.active_mask)  # None
print(state.dominant_emotion)  # 'excited'

# Simulate time passage
chat.advance_time(hours=1)

# Resume conversation
response = chat.send("So what have you been up to?")
```

### Human Participant

```python
# Create a human participant (not AI-simulated)
human = personaut.create_human(name='Anthony')

# Humans don't have simulated emotional states or traits
# Their messages come from actual user input in live simulations

# Optionally provide context about the human
human = personaut.create_human(
    name='Anthony',
    context={
        'relationship': 'old college friend',
        'last_contact': '2 years ago',
        'shared_history': 'Roommates freshman year'
    }
)
```

### Multiple AI Participants

Create group chats with multiple AI individuals:

```python
sarah = personaut.create_individual(name="Sarah")
mike = personaut.create_individual(name="Mike")
human = personaut.create_human(name='Anthony')

# Group text message
situation = personaut.create_situation(
    modality=personaut.types.modality.TEXT_MESSAGE,
    description='Group chat planning a reunion',
    context={'group_name': 'College Crew 🎓'}
)

simulation = personaut.create_simulation(
    situation=situation,
    individuals=[sarah, mike, human],
    type=personaut.simulations.types.LIVE_CONVERSATION,
    output='json',
    turn_order='realistic'  # AI decides who responds naturally
)

simulation.start_simulator()
```

### Saving and Loading Sessions

```python
# Save session for later
simulation.start_simulator(
    session_file='./sessions/sarah_chat.json',
    auto_save=True
)

# Load previous session
simulation.load_session('./sessions/sarah_chat.json')
simulation.start_simulator()  # Continues from saved point
```

### Example: Customer Support Chat

```python
import personaut

# Create support agent persona
support_agent = personaut.create_individual(name="Alex")
support_agent.emotional_state.change_state({
    'cheerful': 0.8,
    'content': 0.7,
    'satisfied': 0.9
})
support_agent.set_trait("warmth", 0.7)
support_agent.set_trait("emotional_stability", 0.8)

# Add professional mask that activates by default
professional_mask = personaut.masks.create_mask(
    name='professional',
    active_by_default=True,
    emotional_modifications={'angry': -0.8, 'hostile': -0.6}
)
support_agent.add_mask(professional_mask)

# Add trigger for escalation
from personaut.triggers import TriggerRule
escalation_trigger = personaut.triggers.create_emotional_trigger(
    description='Customer becoming very angry',
    rules=[TriggerRule(emotion='angry', threshold=0.9, operator='>')],
    response=personaut.masks.STOIC_MASK,
)

# Customer simulatio
customer = personaut.create_human(name='Customer')

situation = personaut.create_situation(
    modality=personaut.types.modality.TEXT_MESSAGE,
    description='Customer support chat about a billing issue',
    context={
        'platform': 'Website live chat',
        'issue_type': 'billing',
        'account_status': 'active'
    }
)

simulation = personaut.create_simulation(
    situation=situation,
    individuals=[support_agent, customer],
    type=personaut.simulations.types.LIVE_CONVERSATION,
    output='json'
)

simulation.start_simulator(
    theme='light',
    show_emotions=True,
    show_triggers=True
)
```

## Relationships in Simulations

Relationships affect how individuals interact in simulations.

### Creating Relationships

```python
import personaut
from personaut.memory import create_shared_memory

user_a = personaut.create_individual(name="Sarah")
user_b = personaut.create_individual(name="Mike")

# Create relationship with trust levels (uses individual IDs, not objects)
relationship = personaut.create_relationship(
    individual_ids=[user_a.id, user_b.id],
    trust={user_a.id: 0.8, user_b.id: 0.5},  # Sarah trusts Mike more than vice versa
)

# Add shared memory
shared_mem = create_shared_memory(
    description='Roommates in college for 2 years',
    individual_ids=[user_a.id, user_b.id],
)
```

### Relationship Effects

```python
# Trust affects:
# - Disclosure of private memories
# - Emotional openness in conversation
# - Response to requests

# High trust (0.8+): Individual may share private memories
# Medium trust (0.4-0.7): Cautious but open communication
# Low trust (0.0-0.3): Guarded responses, withholds information

simulation = personaut.create_simulation(
    situation=situation,
    individuals=[user_a, user_b],
    type=personaut.simulations.types.CONVERSATION,
    relationships=[relationship]  # Include relationship context
)
```

## Memory in Simulations

Memories influence how individuals respond in simulations.

### Memory Types

```python
from personaut.memory import (
    create_individual_memory,
    create_shared_memory,
    create_private_memory,
    search_memories,
)

# Individual memory - personal perception
individual_memory = create_individual_memory(
    individual_id=user_a.id,
    description='Got promoted last month, feeling accomplished',
)

# Shared memory - multi-perspective
shared_memory = create_shared_memory(
    description='Roommates in college for 2 years',
    individual_ids=[user_a.id, user_b.id],
)

# Private memory - trust-gated
private_memory = create_private_memory(
    individual_id=user_a.id,
    description='Deep dark secret that affects trust',
    trust_threshold=0.8,  # Only shared with high-trust relationships
)
```

### Memory Retrieval

During simulations, relevant memories are retrieved via vector search:

```python
# Memories similar to current situation are automatically retrieved
# and included in prompt generation

# Manual memory search
relevant_memories = search_memories(
    individual_id=user_a.id,
    query="feeling anxious about new situations",
    limit=5,
)
```

## Triggers in Simulations

Triggers can activate during simulations based on emotional or situational conditions.

### Emotional Triggers

```python
import personaut
from personaut.triggers import TriggerRule

# Create emotional trigger
trigger = personaut.triggers.create_emotional_trigger(
    description='Unknown or unfamiliar situations',
    rules=[TriggerRule(emotion='anxious', threshold=0.8, operator='>')],
    response=personaut.masks.STOIC_MASK,  # Apply stoic mask
)

user_a.add_trigger(trigger)

# When anxiety exceeds 0.8 during simulation, stoic mask activates
```

### Situational Triggers

```python
# Create situational trigger
trigger = personaut.triggers.create_situational_trigger(
    description='Dark enclosed spaces',
    keywords=['dark', 'enclosed', 'cramped'],
    rules=[TriggerRule(emotion='anxious', threshold=0.4, operator='>')],
    response=personaut.masks.GUARDED_MASK,
)
```

## Masks in Simulations

Masks are contextual personas that modify behavior.

```python
import personaut

# Professional mask - activated in work settings
professional_mask = personaut.masks.create_mask(
    name='professional',
    emotional_modifications={
        'angry': -0.5,      # Suppress anger
        'content': 0.2,     # Boost contentment
        'hostile': -0.3,    # Reduce hostility
    },
    trigger_situations=['office', 'meeting', 'professional']
)

user_a.add_mask(professional_mask)

# When in office situation, professional mask auto-activates
# Emotions are modified according to mask rules
```

## Running Simulations

### Basic Run

```python
simulation.run(
    num=10,      # Number of simulation variations
    dir='./'     # Output directory
)
```

### Advanced Run Options

```python
simulation.run(
    num=10,
    dir='./output/',
    options={
        'include_actions': True,   # Include physical actions/gestures
        'update_emotions': True,   # Update emotional state each turn
        'create_memories': True,   # Create memories from conversation
    }
)
```

> **Planned Features (not yet implemented):** Future releases will add
> `parallel`, `max_workers`, `track_emotions`, `track_memories`,
> `save_prompts`, `filename_prefix`, `include_metadata`, `on_turn`,
> and `on_complete` parameters to `simulation.run()`.


### Output Files

```
./output/
├── conversation_001.txt       # First simulation variation
├── conversation_002.txt       # Second variation
├── ...
├── conversation_010.txt       # Tenth variation
├── metadata.json              # Simulation configuration and stats
├── emotion_tracking.json      # Emotion changes per turn (if tracked)
└── prompts/                   # Generated prompts (if saved)
    ├── turn_001_sarah.txt
    ├── turn_001_mike.txt
    └── ...
```

## Simulation Types Reference

| Type | Purpose | Participants | Output |
|------|---------|--------------|--------|
| `CONVERSATION` | Dialogue simulation | 2+ individuals | Script, JSON, TXT |
| `SURVEY` | Questionnaire responses | 1 individual | JSON, TXT |
| `OUTCOME_SUMMARY` | Target outcome analysis | 2+ individuals | Stats report |
| `LIVE_CONVERSATION` | Real-time interaction | 1 AI + 1 human | Interactive app |

## Simulation Styles Reference

| Style | Format | Best For |
|-------|--------|----------|
| `SCRIPT` | Screenplay format with stage directions | Reviewing dialogue flow |
| `QUESTIONNAIRE` | Q&A format with responses | Survey analysis |
| `NARRATIVE` | Story-like prose | Reading experience |
| `JSON` | Structured data | Machine processing |
| `TXT` | Plain text | Simple logging |

## Best Practices

### Emotional Realism
- Set initial emotional states that match the situation
- Allow emotions to evolve naturally during conversation
- Avoid extreme emotional values unless intentional

### Relationship Dynamics
- Define trust levels that reflect relationship history
- Include shared memories for established relationships
- Consider asymmetric trust (A trusts B more than B trusts A)

### Outcome Analysis
- Run sufficient variations (10+) for statistical validity
- Randomize relevant variables to identify key factors
- Document target outcomes clearly

### Live Simulations
- Test in development before deployment
- Handle network errors gracefully
- Log all interactions for review

## Examples

### Customer Service Simulation

```python
import personaut

# Frustrated customer
customer = personaut.create_individual(name="Customer")
customer.emotional_state.change_state({
    'angry': 0.6,
    'hostile': 0.7,
    'hopeful': 0.3
})

# Patient service rep
service_rep = personaut.create_individual(name="Support Agent")
service_rep.set_trait("warmth", 0.8)
service_rep.set_trait("emotional_stability", 0.7)

situation = personaut.create_situation(
    modality=personaut.types.modality.PHONE_CALL,
    description='Customer calling about a billing error',
    context={'issue': 'Double charged for subscription'}
)

simulation = personaut.create_simulation(
    situation=situation,
    individuals=[customer, service_rep],
    type=personaut.simulations.types.CONVERSATION,
    style=personaut.simulations.styles.SCRIPT,
    output='txt'
)

simulation.run(num=5, dir='./customer_service/')
```

### Population Survey

```python
import personaut

# Create diverse respondent pool
respondents = []
personality_profiles = [
    {'warmth': 0.8, 'apprehension': 0.3},  # Confident extrovert
    {'warmth': 0.3, 'apprehension': 0.7},  # Anxious introvert
    {'dominance': 0.8, 'vigilance': 0.6},  # Skeptical leader
    {'sensitivity': 0.8, 'liveliness': 0.7} # Enthusiastic creative
]

for i, profile in enumerate(personality_profiles):
    respondent = personaut.create_individual(name=f"Respondent_{i+1}")
    for trait_name, value in profile.items():
        trait = getattr(personaut.traits, trait_name.upper())
        respondent.set_trait(trait_name, value)
    respondents.append(respondent)

# Run survey for each respondent
for respondent in respondents:
    simulation = personaut.create_simulation(
        situation=survey_situation,
        individuals=[respondent],
        type=personaut.simulations.types.SURVEY,
        style=personaut.simulations.styles.QUESTIONNAIRE,
        output='json'
    )
    simulation.run(num=1, dir='./survey_results/')
```

### A/B Testing with Outcome Analysis

```python
import personaut

# Test two sales approaches
approaches = [
    {'description': 'Friendly greeting, immediate product pitch', 'name': 'direct'},
    {'description': 'Build rapport first, then suggest product', 'name': 'rapport'}
]

for approach in approaches:
    situation = personaut.create_situation(
        modality=personaut.types.modality.IN_PERSON,
        description=approach['description'],
        location='Retail Store'
    )
    
    simulation = personaut.create_simulation(
        situation=situation,
        individuals=[customer, sales_rep],
        type=personaut.simulations.types.OUTCOME_SUMMARY,
        target_outcome='Customer makes a purchase',
        randomize=[customer.emotional_state]
    )
    
    simulation.run(num=20, dir=f'./ab_test/{approach["name"]}/')
```

## Related Documentation

- [EMOTIONS.md](./EMOTIONS.md) - Emotional state system
- [TRAITS.md](./TRAITS.md) - Personality trait system
- [PROMPTS.md](./PROMPTS.md) - Prompt generation for simulations
- [../PERSONAS.md](../PERSONAS.md) - Main agent guidelines
