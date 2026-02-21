# Prompt Generation Guide

This document describes the prompt generation system in the Personaut PDK. The prompt system dynamically assembles LLM prompts based on an individual's emotional state, personality traits, memories, relationships, and situational context.

## Overview

The prompt generation system is responsible for translating an individual's complete psychological and contextual state into natural language instructions for the LLM. This enables authentic persona-driven responses in simulations.

**Key Capabilities:**
- Dynamic prompt assembly from multiple components
- Emotional state integration with intensity-aware language
- Trait-based personality descriptions
- Memory injection with relevance filtering
- Relationship context and trust-level awareness
- Situational modality adaptation
- Template customization per simulation type

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PromptManager                            │
│  Orchestrates prompt generation for simulations                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PromptBuilder                            │
│  Assembles components into final prompt                         │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│    Templates     │ │   Components     │ │    Defaults      │
│  - conversation  │ │ - emotional_state│ │  - base configs  │
│  - survey        │ │ - personality    │ │  - fallbacks     │
│  - outcome       │ │ - memory         │ │                  │
│                  │ │ - relationship   │ │                  │
│                  │ │ - situation      │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

## PromptManager

The `PromptManager` is the main entry point for generating prompts. It coordinates between templates and components to produce a complete prompt for the LLM.

### Basic Usage

```python
import personaut
from personaut.prompts import PromptManager

# Create an individual with emotional state and traits
individual = personaut.create_individual(name="Sarah")
individual.emotional_state.change_state({
    'anxious': 0.6,
    'hopeful': 0.4,
    'trusting': 0.3
})
individual.set_trait("warmth", 0.7)

# Create situation context
situation = personaut.create_situation(
    type=personaut.types.modality.IN_PERSON,
    description='Meeting a new colleague at work',
    location='Office'
)

# Generate prompt
manager = PromptManager()
prompt = manager.generate(
    individual=individual,
    situation=situation,
    template='conversation'
)

print(prompt)
```

### Output Example

```
You are roleplaying as Sarah.

## Personality
Sarah has a warm and approachable personality. She tends to be outgoing and 
kindly in her interactions, showing genuine interest in others.

## Current Emotional State
Right now, Sarah is feeling notably anxious (moderate-high intensity), with 
underlying feelings of hopefulness and a cautious approach to trusting others.

## Situation
Sarah is in an office environment for an in-person meeting with a new colleague.

## Behavioral Guidelines
- Express thoughts with some hesitation due to anxiety
- Show openness to connection despite nervousness
- Be warm but maintain appropriate professional boundaries
- May seek reassurance or validation

Respond as Sarah would in this situation.
```

## PromptBuilder

The `PromptBuilder` provides fine-grained control over prompt assembly. Use it when you need to customize how individual components are combined.

### Builder Pattern

```python
from personaut.prompts import PromptBuilder

builder = PromptBuilder()

prompt = (builder
    .with_individual(individual)
    .with_emotional_state(individual.emotional_state)
    .with_traits(individual.traits)
    .with_situation(situation)
    .with_memories(relevant_memories)
    .with_relationships(relationships)
    .using_template('conversation')
    .build()
)
```

### Custom Component Order

```python
# Control the order of sections in the prompt
prompt = (builder
    .with_individual(individual)
    .section_order([
        'situation',      # Context first
        'personality',    # Then who they are
        'emotional_state', # Current feelings
        'memories',       # Relevant past
        'guidelines'      # How to behave
    ])
    .build()
)
```

## Components

Components are reusable modules that format specific aspects of an individual's state into prompt text.

### Emotional State Component

Converts an `EmotionalState` into natural language descriptions with intensity awareness.

```python
from personaut.prompts.components import EmotionalStateComponent

component = EmotionalStateComponent()

# Generate emotional context
text = component.format(individual.emotional_state)
```

**Intensity Mapping:**

| Value Range | Intensity Label | Example Output |
|-------------|-----------------|----------------|
| 0.0 - 0.2   | minimal         | "barely noticeable anxiety" |
| 0.2 - 0.4   | mild            | "slight anxiety" |
| 0.4 - 0.6   | moderate        | "noticeable anxiety" |
| 0.6 - 0.8   | strong          | "significant anxiety" |
| 0.8 - 1.0   | intense         | "overwhelming anxiety" |

**Category-Aware Descriptions:**

```python
# When multiple emotions are elevated, grouping by category
emotional_state.change_state({
    'anxious': 0.7,
    'insecure': 0.6,
    'confused': 0.5
})

text = component.format(emotional_state)
# Output: "Sarah is experiencing a cluster of fear-based emotions: 
#          significant anxiety, noticeable insecurity, and mild confusion."
```

**Dominant Emotion Highlighting:**

```python
# Automatically emphasizes the strongest emotion
text = component.format(emotional_state, highlight_dominant=True)
# Output: "Sarah is primarily feeling anxious (strong intensity), 
#          which colors her other emotional experiences..."
```

### Personality Component

Translates personality traits into behavioral descriptions.

```python
from personaut.prompts.components import PersonalityComponent

component = PersonalityComponent()
text = component.format(individual.traits)
```

**Trait Value Interpretation:**

| Trait | High (0.7-1.0) | Low (0.0-0.3) |
|-------|----------------|---------------|
| WARMTH | "outgoing, kindly, shows genuine interest" | "reserved, maintains emotional distance" |
| DOMINANCE | "assertive, takes charge, confident" | "deferential, yielding, supportive" |
| EMOTIONAL_STABILITY | "composed, handles stress well" | "reactive, emotionally sensitive" |
| VIGILANCE | "skeptical, questions motives" | "trusting, takes things at face value" |

**Example Output:**

```python
individual.set_trait("warmth", 0.8)
individual.set_trait("vigilance", 0.7)

text = component.format(individual.traits)
# Output: "Sarah is notably warm and approachable, genuinely interested in 
#          others. However, she also maintains a healthy skepticism and tends 
#          to question others' motives before fully trusting them."
```

### Memory Component

Injects relevant memories into the prompt context.

```python
from personaut.prompts.components import MemoryComponent

component = MemoryComponent()

# Get relevant memories via vector search
relevant_memories = personaut.memory.search(
    individual=individual,
    situation=situation,
    limit=5
)

text = component.format(
    memories=relevant_memories,
    trust_level=0.8  # For private memory filtering
)
```

**Memory Types in Prompts:**

```python
# Individual memories - personal perception
individual_memory = personaut.memory.create_individual_memory(
    description='First day at current job was overwhelming but exciting'
)

# Shared memories - multiple perspectives
shared_memory = personaut.memory.create_shared_memory(
    description='Collaborated on successful project last quarter',
    relationships=[relationship_with_colleague]
)

# Private memories - trust-gated
private_memory = personaut.memory.create_private_memory(
    description='Struggled with imposter syndrome for months',
    trust_threshold=0.7
)

# Component respects trust thresholds
text = component.format(
    memories=[individual_memory, shared_memory, private_memory],
    trust_level=0.5  # Private memory excluded (threshold 0.7)
)
```

**Output Example:**

```
## Relevant Memories
- Sarah remembers her first day at this job being overwhelming but exciting. 
  This shapes her understanding of what new colleagues might experience.
- She recalls a successful collaboration last quarter, which gives her 
  confidence in building new professional relationships.
```

### Relationship Component

Adds relationship context and trust dynamics.

```python
from personaut.prompts.components import RelationshipComponent

component = RelationshipComponent()

text = component.format(
    individual=individual,
    other_individuals=[colleague],
    relationships=relationships
)
```

**Trust Level Descriptions:**

| Trust Range | Description |
|-------------|-------------|
| 0.0 - 0.2   | "deeply distrustful", "guarded" |
| 0.2 - 0.4   | "cautious", "reserved" |
| 0.4 - 0.6   | "neutral", "open to building trust" |
| 0.6 - 0.8   | "trusting", "comfortable" |
| 0.8 - 1.0   | "deeply trusting", "vulnerable with" |

**Output Example:**

```
## Relationship Context
- With the new colleague: Sarah has no prior relationship. She is open to 
  building trust but will naturally be somewhat cautious initially.
```

### Situation Component

Formats situational context including modality and environment.

```python
from personaut.prompts.components import SituationComponent

component = SituationComponent()

text = component.format(situation)
```

**Modality-Specific Formatting:**

```python
# IN_PERSON modality
situation = personaut.create_situation(
    type=personaut.types.modality.IN_PERSON,
    description='Coffee shop meeting',
    location='Downtown Cafe'
)
# Output: "Sarah is physically present at Downtown Cafe for a coffee shop meeting.
#          She can observe body language and environmental cues."

# TEXT_MESSAGE modality
situation = personaut.create_situation(
    type=personaut.types.modality.TEXT_MESSAGE,
    description='Catching up with an old friend'
)
# Output: "Sarah is communicating via text message. She has time to consider 
#          her responses and cannot see the other person's immediate reactions."
```

## Templates

Templates define the overall structure and tone of prompts for different simulation types.

### Conversation Template

For dialogue-based simulations between individuals.

```python
from personaut.prompts.templates import ConversationTemplate

template = ConversationTemplate()
prompt = template.render(
    individual=individual,
    other_participants=[other_individual],
    situation=situation,
    style='natural'  # Options: 'natural', 'formal', 'casual'
)
```

**Template Structure:**

```
[Identity Section]
You are roleplaying as {name}.

[Personality Section]
{personality_component_output}

[Emotional State Section]
{emotional_state_component_output}

[Relationship Section]
{relationship_component_output}

[Memory Section]
{memory_component_output}

[Situation Section]
{situation_component_output}

[Guidelines Section]
{behavioral_guidelines}

[Response Instruction]
Respond as {name} would in this conversation.
```

### Survey Template

For questionnaire and survey response simulations.

```python
from personaut.prompts.templates import SurveyTemplate

template = SurveyTemplate()
prompt = template.render(
    individual=individual,
    questions=survey_questions,
    response_format='likert_scale'  # Options: 'likert_scale', 'open_ended', 'multiple_choice'
)
```

**Survey-Specific Guidelines:**

```python
# The template adds survey-specific behavioral instructions
# Output includes:
# - How emotional state affects response patterns
# - How traits influence answer selection
# - Consistency guidelines for multi-question surveys
```

### Outcome Template

For outcome analysis simulations with target outcomes.

```python
from personaut.prompts.templates import OutcomeTemplate

template = OutcomeTemplate()
prompt = template.render(
    individual=individual,
    situation=situation,
    target_outcome='Customer agrees to upgrade',
    randomize_emotional_state=True
)
```

### Custom Templates

Create custom templates by extending the base class:

```python
from personaut.prompts.templates.base import BaseTemplate

class NegotiationTemplate(BaseTemplate):
    """Template for negotiation simulations."""
    
    def render(
        self,
        individual: Individual,
        opponent: Individual,
        stakes: str,
        **kwargs
    ) -> str:
        # Build the prompt using components
        prompt_parts = [
            self._render_identity(individual),
            self._render_negotiation_context(stakes),
            self._render_personality(individual.traits),
            self._render_emotional_state(individual.emotional_state),
            self._render_opponent_perception(opponent),
            self._render_negotiation_guidelines()
        ]
        return "\n\n".join(prompt_parts)
```

## Behavioral Guidelines Generation

The prompt system automatically generates behavioral guidelines based on the individual's state.

### Emotion-Driven Guidelines

```python
# High anxiety (0.7) generates guidelines like:
# - "Express thoughts with some hesitation"
# - "May seek reassurance before making decisions"
# - "Tend to overthink or second-guess responses"

# High dominance trait (0.8) + high angry emotion (0.6):
# - "Assert position firmly"
# - "May interrupt or speak over others"
# - "Show impatience with opposition"
```

### Mask-Influenced Guidelines

When a mask is active, it modifies the guidelines:

```python
# Professional mask active:
# - "Maintain composure regardless of internal state"
# - "Use formal language and measured responses"
# - "Suppress visible emotional reactions"
```

## Configuration

### Default Settings

```python
from personaut.prompts import PromptManager

manager = PromptManager(
    # Component settings
    intensity_threshold=0.3,      # Minimum emotion intensity to include
    max_memories=5,               # Maximum memories to inject
    include_private_memories=True, # Respect trust thresholds for private
    
    # Template settings
    default_template='conversation',
    include_guidelines=True,
    
    # Output settings
    max_tokens=2000,              # Approximate prompt length limit
    verbose=False                 # Include debug sections
)
```

### Per-Generation Overrides

```python
prompt = manager.generate(
    individual=individual,
    situation=situation,
    
    # Override defaults for this generation
    intensity_threshold=0.5,
    max_memories=3,
    template='survey'
)
```

## Integration with Simulations

The prompt system integrates seamlessly with the simulation engine:

```python
import personaut

# Create simulation
simulation = personaut.create_simulation(
    situation=situation,
    individuals=[user_a, user_b],
    type=personaut.simulations.types.CONVERSATION,
    style=personaut.simulations.styles.SCRIPT
)

# PromptManager is used internally
# Each turn generates a new prompt reflecting:
# - Updated emotional states from previous turns
# - New memories formed during conversation
# - Relationship trust changes
# - Active masks and triggers

simulation.run(num=10)
```

### Prompt Updates During Simulation

```python
# After each turn, the prompt system:
# 1. Updates emotional state based on interaction
# 2. Adds new interaction to short-term memory
# 3. Re-evaluates trigger conditions
# 4. Regenerates prompt with new state

# Access the current prompt for debugging
current_prompt = simulation.get_current_prompt(individual=user_a)
```

## Best Practices

### Prompt Efficiency

- Set appropriate `intensity_threshold` to avoid cluttering prompts with minimal emotions
- Limit memory injection to most relevant memories
- Use `max_tokens` to prevent excessively long prompts

### Consistency

- Use the same template for related simulations
- Keep component order consistent across runs
- Document custom templates thoroughly

### Testing Prompts

```python
# Preview prompts before running simulations
prompt = manager.generate(
    individual=individual,
    situation=situation,
    preview=True  # Returns prompt without sending to model
)

# Validate prompt structure
validation = manager.validate(prompt)
if not validation.is_valid:
    print(validation.errors)
```

## Examples

### Multi-Individual Conversation

```python
import personaut
from personaut.prompts import PromptManager

# Create two individuals with different personalities
sarah = personaut.create_individual(name="Sarah")
sarah.emotional_state.change_state({'anxious': 0.4, 'hopeful': 0.6})
sarah.set_trait("warmth", 0.8)

mike = personaut.create_individual(name="Mike")  
mike.emotional_state.change_state({'proud': 0.7, 'angry': 0.5})
mike.set_trait("dominance", 0.7)

# Create shared history
relationship = personaut.relationships.create_relationship(
    individuals=[sarah, mike],
    trust={sarah: 0.6, mike: 0.5}
)

# Generate prompts for each individual
manager = PromptManager()

sarah_prompt = manager.generate(
    individual=sarah,
    other_participants=[mike],
    relationships=[relationship],
    situation=meeting_situation
)

mike_prompt = manager.generate(
    individual=mike,
    other_participants=[sarah],
    relationships=[relationship],
    situation=meeting_situation
)
```

### Survey with Emotional Variation

```python
# Run the same survey with different emotional states
base_individual = personaut.create_individual(name="Respondent")

# Anxious version
anxious_state = personaut.emotions.EmotionalState()
anxious_state.change_state({'anxious': 0.7, 'insecure': 0.5})

# Confident version  
confident_state = personaut.emotions.EmotionalState()
confident_state.change_state({'proud': 0.7, 'satisfied': 0.6})

manager = PromptManager()

for state in [anxious_state, confident_state]:
    base_individual.emotional_state = state
    prompt = manager.generate(
        individual=base_individual,
        template='survey',
        questions=survey_questions
    )
    # Run survey with this prompt...
```

## Related Documentation

- [EMOTIONS.md](./EMOTIONS.md) - Emotion system and EmotionalState class
- [TRAITS.md](./TRAITS.md) - Personality trait system
- [SIMULATIONS.md](./SIMULATIONS.md) - Simulation engine integration
- [../PERSONAS.md](../PERSONAS.md) - Main agent guidelines
