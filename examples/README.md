# Personaut PDK Examples

This folder contains working examples demonstrating every feature of the Personaut PDK.

## Running Examples

All examples can be run with hatch:

```bash
cd /path/to/python-pdk
python3 -m hatch run python examples/01_basic_individual.py
python3 -m hatch run python examples/02_emotions.py
# etc.
```

Or run all offline examples at once:

```bash
python3 -m hatch run python examples/run_all_examples.py
```

## Examples Overview

| #  | File                          | Feature                 | Description                                            |
|----|-------------------------------|-------------------------|--------------------------------------------------------|
| 01 | `01_basic_individual.py`      | Individuals             | Creating and configuring personas                      |
| 02 | `02_emotions.py`              | Emotions                | 36-emotion system and emotional states                 |
| 03 | `03_traits.py`                | Traits                  | 17-trait personality system (16PF model)               |
| 04 | `04_persona_prompts.py`       | Persona Prompts         | How traits/emotions influence LLM prompts              |
| 05 | `05_llm_generation.py`        | **LLM Generation** 🔑  | Live persona-driven text generation                    |
| 06 | `06_server.py`                | **Server** 🔑           | REST API server with CRUD operations                   |
| 07 | `07_situations.py`            | Situations              | Modalities, context, and environment settings          |
| 08 | `08_masks_and_triggers.py`    | Masks & Triggers        | Contextual personas and conditional activators         |
| 09 | `09_memory.py`                | Memory                  | Trust-gated memories with vector search                |
| 10 | `10_relationships.py`         | Relationships           | Asymmetric trust and relationship networks             |
| 11 | `11_facts.py`                 | Facts & Extraction      | Situational facts, context presets, and text extraction |
| 12 | `12_states.py`                | States & Markov         | State calculators and probabilistic transitions        |
| 13 | `13_storage.py`               | Storage                 | FileStorage and SQLiteStorage backends                 |
| 14 | `14_simulations.py`           | Simulations             | Conversations, surveys, outcomes, and live chat        |

> 🔑 = Requires API keys or starts a server

## Architecture Overview

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Persona Data    │    │  System Prompt   │    │  LLM Response    │
│                  │    │                  │    │                  │
│  - Traits  (03)  │───▶│  Constructed     │───▶│  In-character    │
│  - Emotions (02) │    │  automatically   │    │  response that   │
│  - Masks   (08)  │    │  from persona    │    │  matches the     │
│  - Memory  (09)  │    │  (04, 05)        │    │  persona         │
│  - Facts   (11)  │    │                  │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         │                                              │
         ▼                                              ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Context         │    │  Dynamics        │    │  Persistence     │
│                  │    │                  │    │                  │
│  - Situations(07)│    │  - Triggers (08) │    │  - FileStorage   │
│  - Relations(10) │    │  - Markov   (12) │    │  - SQLite   (13) │
│  - Trust   (10)  │    │  - States   (12) │    │  - Server   (06) │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                 │
                     ┌───────────┴───────────┐
                     │  Simulations (14)     │
                     │                       │
                     │  - Conversation       │
                     │  - Survey             │
                     │  - Outcome Analysis   │
                     │  - Live Chat          │
                     └───────────────────────┘
```

## Server Example (06)

Example 06 starts a FastAPI server, creates personas via REST API,
demonstrates CRUD operations, then keeps the server running so you can
explore the interactive Swagger UI:

```bash
python3 -m hatch run python examples/06_server.py
# → Server runs the demo, then stays alive
# → Open http://127.0.0.1:8000/api/docs for Swagger UI
# → Press Ctrl+C to stop
```

## API Key Setup

Example 05 requires an LLM API key:

```bash
# For Gemini
export GOOGLE_API_KEY=your_key

# For AWS Bedrock
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=yyy
```

## Quick Start

```python
import personaut

# Create a persona with personality traits
becca = personaut.create_individual(
    name="Becca",
    traits={"warmth": 0.9, "liveliness": 0.8},
    emotional_state={"cheerful": 0.7},
    metadata={"occupation": "barista"},
)

# Traits and emotions are used to construct prompts
# that make LLM responses match the character
```

## Learning Path

We recommend going through the examples in order:

1. **Foundations** (01-03) — Individual creation, emotions, traits
2. **Prompt Pipeline** (04-05) — How persona data becomes LLM prompts
3. **Context Layer** (07, 10) — Situations, relationships, trust
4. **Behavior System** (08, 11) — Masks, triggers, facts
5. **State Dynamics** (09, 12) — Memory, state calculation, Markov transitions
6. **Infrastructure** (06, 13) — Server API, storage backends
7. **Simulations** (14) — Conversations, surveys, outcomes, live chat
