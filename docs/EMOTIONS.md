# Emotion System Guide

This document describes the emotional state system in the Personaut PDK. Emotions are the foundation for authentic agent interactions and drive behavioral responses in simulations.

## Overview

The emotion system models 36 discrete emotions organized into 6 primary categories. Each emotion has a value between 0 and 1, where:
- `0.0` = emotion is not present
- `0.5` = moderate intensity
- `1.0` = maximum intensity

Emotional states are dynamic and change based on:
- Trait influences (coefficient-based modifications)
- Situational triggers
- Memory associations
- Relationship dynamics
- Mask activations

## Emotion Categories

### Anger/Mad Category
Emotions related to frustration, aggression, and conflict.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Hostile | `personaut.emotion.HOSTILE` | Actively antagonistic or unfriendly disposition |
| Hurt | `personaut.emotion.HURT` | Emotional pain from perceived wrongdoing |
| Angry | `personaut.emotion.ANGRY` | Strong displeasure or annoyance |
| Selfish | `personaut.emotion.SELFISH` | Prioritizing self-interest above others |
| Hateful | `personaut.emotion.HATEFUL` | Intense dislike or ill will |
| Critical | `personaut.emotion.CRITICAL` | Tendency to find fault or judge harshly |

### Sad/Sadness Category
Emotions related to loss, disappointment, and low energy states.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Guilty | `personaut.emotion.GUILTY` | Feeling responsible for wrongdoing |
| Ashamed | `personaut.emotion.ASHAMED` | Embarrassment about actions or self |
| Depressed | `personaut.emotion.DEPRESSED` | Persistent low mood and hopelessness |
| Lonely | `personaut.emotion.LONELY` | Feeling isolated or disconnected |
| Bored | `personaut.emotion.BORED` | Lack of interest or engagement |
| Apathetic | `personaut.emotion.APATHETIC` | Absence of emotion or motivation |

### Fear/Scared Category
Emotions related to threat perception and anxiety.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Rejected | `personaut.emotion.REJECTED` | Feeling dismissed or unwanted |
| Confused | `personaut.emotion.CONFUSED` | Uncertainty or lack of clarity |
| Submissive | `personaut.emotion.SUBMISSIVE` | Yielding to authority or pressure |
| Insecure | `personaut.emotion.INSECURE` | Self-doubt and lack of confidence |
| Anxious | `personaut.emotion.ANXIOUS` | Worry and unease about outcomes |
| Helpless | `personaut.emotion.HELPLESS` | Feeling powerless to change situation |

### Joy/Happiness Category
Emotions related to positive energy and enthusiasm.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Excited | `personaut.emotion.EXCITED` | Eager anticipation and high energy |
| Sensual | `personaut.emotion.SENSUAL` | Appreciation of physical pleasures |
| Energetic | `personaut.emotion.ENERGETIC` | Vitality and active engagement |
| Cheerful | `personaut.emotion.CHEERFUL` | Lighthearted and optimistic mood |
| Creative | `personaut.emotion.CREATIVE` | Inspired and imaginative state |
| Hopeful | `personaut.emotion.HOPEFUL` | Positive expectation for the future |

### Powerful/Confident Category
Emotions related to self-assurance and status.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Proud | `personaut.emotion.PROUD` | Satisfaction with achievements |
| Respected | `personaut.emotion.RESPECTED` | Feeling valued by others |
| Appreciated | `personaut.emotion.APPRECIATED` | Recognized for contributions |
| Important | `personaut.emotion.IMPORTANT` | Sense of personal significance |
| Faithful | `personaut.emotion.FAITHFUL` | Loyalty and commitment |
| Satisfied | `personaut.emotion.SATISFIED` | Contentment with current state |

### Peaceful/Calm Category
Emotions related to tranquility and connection.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Content | `personaut.emotion.CONTENT` | Ease and acceptance |
| Thoughtful | `personaut.emotion.THOUGHTFUL` | Reflective and considerate state |
| Intimate | `personaut.emotion.INTIMATE` | Deep personal connection |
| Loving | `personaut.emotion.LOVING` | Affection and care for others |
| Trusting | `personaut.emotion.TRUSTING` | Confidence in others' reliability |
| Nurturing | `personaut.emotion.NURTURING` | Desire to care for and support |

## Emotion Constants Reference

The following shows the exact constant usage as defined in the Personaut PDK:

```python
import personaut

# Anger/Mad
hostile = personaut.emotion.HOSTILE
hurt = personaut.emotion.HURT
angry = personaut.emotion.ANGRY
selfish = personaut.emotion.SELFISH
hateful = personaut.emotion.HATEFUL
critical = personaut.emotion.CRITICAL

# Sad/Sadness
guilty = personaut.emotion.GUILTY
ashamed = personaut.emotion.ASHAMED
depressed = personaut.emotion.DEPRESSED
lonely = personaut.emotion.LONELY
bored = personaut.emotion.BORED
apathetic = personaut.emotion.APATHETIC

# Fear/Scared
rejected = personaut.emotion.REJECTED
confused = personaut.emotion.CONFUSED
submissive = personaut.emotion.SUBMISSIVE
insecure = personaut.emotion.INSECURE
anxious = personaut.emotion.ANXIOUS
helpless = personaut.emotion.HELPLESS

# Joy/Happiness
excited = personaut.emotion.EXCITED
sensual = personaut.emotion.SENSUAL
energetic = personaut.emotion.ENERGETIC
cheerful = personaut.emotion.CHEERFUL
creative = personaut.emotion.CREATIVE
hopeful = personaut.emotion.HOPEFUL

# Powerful/Confident
proud = personaut.emotion.PROUD
respected = personaut.emotion.RESPECTED
appreciated = personaut.emotion.APPRECIATED
important = personaut.emotion.IMPORTANT
faithful = personaut.emotion.FAITHFUL
satisfied = personaut.emotion.SATISFIED

# Peaceful/Calm
content = personaut.emotion.CONTENT
thoughtful = personaut.emotion.THOUGHTFUL
intimate = personaut.emotion.INTIMATE
loving = personaut.emotion.LOVING
trusting = personaut.emotion.TRUSTING
nurturing = personaut.emotion.NURTURING
```

## EmotionalState Class

The `EmotionalState` class manages all 36 emotions as a unified state object. By default, an `EmotionalState` contains all emotions defined in the current version of Personaut PDK.

> **Reference**: From the Personaut API specification:
> - Emotional States are made up by default of all of the emotions defined
> - You can add or remove emotions through an input list of emotions
> - If you do not put any emotion into the emotional state it defaults to all in the version of personaut

### Creating an EmotionalState

```python
import personaut

# Create with default values (ALL 36 emotions included at baseline)
# This is the standard way to create an emotional state
emotional_state = personaut.emotion.EmotionalState()

# Create with only specific emotions (subset tracking)
# Only these emotions will be tracked; all others are excluded
emotional_state = personaut.emotion.EmotionalState(
    emotions=['ANGRY', 'ANXIOUS', 'HOPEFUL']
)

# If no emotions list is provided, ALL emotions are included by default
# This is equivalent to: EmotionalState(emotions=[...all 36 emotions...])
```

### Default Emotion Set

When created without arguments, `EmotionalState()` includes all 36 emotions:

```python
# All emotions from each category are included:
# Anger/Mad: HOSTILE, HURT, ANGRY, SELFISH, HATEFUL, CRITICAL
# Sad/Sadness: GUILTY, ASHAMED, DEPRESSED, LONELY, BORED, APATHETIC  
# Fear/Scared: REJECTED, CONFUSED, SUBMISSIVE, INSECURE, ANXIOUS, HELPLESS
# Joy/Happiness: EXCITED, SENSUAL, ENERGETIC, CHEERFUL, CREATIVE, HOPEFUL
# Powerful/Confident: PROUD, RESPECTED, APPRECIATED, IMPORTANT, FAITHFUL, SATISFIED
# Peaceful/Calm: CONTENT, THOUGHTFUL, INTIMATE, LOVING, TRUSTING, NURTURING
```

### Modifying Individual Emotions

Use `change_emotion()` to set a specific emotion to an exact value:

```python
import personaut

emotional_state = personaut.emotion.EmotionalState()

# Change a single emotion to a specific value (0 to 1)
emotional_state.change_emotion('angry', 0.1)

# Examples from the spec:
emotional_state.change_emotion('hostile', 0.5)
emotional_state.change_emotion('loving', 0.8)
emotional_state.change_emotion('anxious', 0.3)
```

### Modifying Entire State

Use `change_state()` to modify multiple emotions at once. This method accepts a dictionary of emotion values and an optional `fill` parameter:

```python
import personaut

emotional_state = personaut.emotion.EmotionalState()

# Change multiple emotions at once
# Emotions not specified retain their existing values
emotional_state.change_state({'angry': 0.1})

# Change multiple emotions AND set all others to a fill value
# The fill parameter sets ALL unspecified emotions to that value
emotional_state.change_state({'angry': 0.1}, fill=0)
# Result: angry=0.1, all other 35 emotions=0

# If fill is not provided, unspecified emotions keep their current values
emotional_state.change_state({'angry': 0.1, 'hostile': 0.2})
# Result: angry=0.1, hostile=0.2, all others unchanged

# Complex example: Set a fear-based state
emotional_state.change_state({
    'anxious': 0.7,
    'insecure': 0.6,
    'helpless': 0.4,
    'hopeful': 0.2  # Still maintain some hope
}, fill=0.1)  # Set all other emotions to low baseline
```

> **Key Behavior**: The `fill` parameter is optional. When omitted, only the specified emotions are changed and all others remain at their existing values. When provided, all unspecified emotions are set to the fill value.

### Querying State

```python
# Get all emotions as a dictionary
all_emotions = emotional_state.to_dict()

# Get emotions by category
anger_emotions = emotional_state.get_category('anger')

# Get dominant emotion (highest value)
dominant = emotional_state.get_dominant()
# Returns: ('anxious', 0.7)

# Get top N emotions
top_emotions = emotional_state.get_top(n=3)
# Returns: [('anxious', 0.7), ('insecure', 0.6), ('helpless', 0.4)]

# Check if any emotion exceeds threshold
is_distressed = emotional_state.any_above(0.5, category='fear')
# Returns: True (anxious=0.7, insecure=0.6 both exceed 0.5)
```

### Complete API Reference

| Method | Description |
|--------|-------------|
| `EmotionalState()` | Create state with all 36 emotions at baseline |
| `EmotionalState(emotions=[...])` | Create state with only specified emotions |
| `change_emotion(emotion, value)` | Set a single emotion to exact value (0-1) |
| `change_state(dict, fill=None)` | Set multiple emotions; optionally fill others |
| `to_dict()` | Get all emotions as dictionary |
| `get_category(category)` | Get emotions for a specific category |
| `get_dominant()` | Get emotion with highest value |
| `get_top(n)` | Get top N emotions by value |
| `any_above(threshold, category=None)` | Check if any emotion exceeds threshold |

## State Calculation Modes

When calculating initial emotional state from historical interactions, different modes are available:

### AVERAGE Mode (Default)
Averages emotional values from the past N interactions.

```python
from personaut.states.mode import AVERAGE

individual = personaut.create_individual(
    state_mode=AVERAGE,
    state_window=10  # Look at last 10 interactions
)
```

**Example**: If last 3 interactions had `angry` values of [0.2, 0.4, 0.6], the initial state will have `angry = 0.4`.

### MAXIMUM Mode
Uses the highest emotional state from past interactions.

```python
from personaut.states.mode import MAXIMUM

individual = personaut.create_individual(
    state_mode=MAXIMUM,
    state_window=10
)
```

**Example**: If last 3 interactions had `angry` values of [0.2, 0.4, 0.6], the initial state will have `angry = 0.6`.

### MODE Mode
Uses the most frequently occurring emotional state.

```python
from personaut.states.mode import MODE

individual = personaut.create_individual(
    state_mode=MODE,
    state_window=10
)
```

**Example**: If last 5 interactions had `angry` values of [0.2, 0.4, 0.4, 0.4, 0.6], the initial state will have `angry = 0.4` (most common).

### Custom Mode
Define your own state calculation function.

```python
from personaut.states.mode import CustomMode

def weighted_recent(history: list[EmotionalState]) -> EmotionalState:
    """Weight recent interactions more heavily."""
    weights = [0.1, 0.2, 0.3, 0.4]  # Most recent gets 0.4
    # ... implementation
    return calculated_state

individual = personaut.create_individual(
    state_mode=CustomMode(weighted_recent)
)
```

## Trait-Emotion Coefficients

Personality traits influence how quickly emotions change. Each trait has coefficients that affect specific emotions.

### Coefficient Effects

| Trait | High Value Effect | Low Value Effect |
|-------|-------------------|------------------|
| **WARMTH** | Speeds up LOVING, TRUSTING; buffers HOSTILE | Increases CRITICAL, LONELY; slows NURTURING |
| **REASONING** | Accelerates CONFUSED → THOUGHTFUL; buffers HELPLESS | Increases susceptibility to CONFUSED, ANXIOUS |
| **EMOTIONAL_STABILITY** | Strong buffer for "Sad" and "Fear"; stabilizes CONTENT | Rapid spikes in ANXIOUS, DEPRESSED, HURT |
| **DOMINANCE** | Correlates with PROUD, IMPORTANT; moves toward ANGRY if challenged | High affinity for SUBMISSIVE; moves toward APPRECIATED |
| **HUMILITY** | Increases FAITHFUL, SATISFIED; massive buffer against SELFISH | Faster movement toward SELFISH, IMPORTANT |
| **LIVELINESS** | High baseline EXCITED, ENERGETIC; low tolerance for BORED | High baseline THOUGHTFUL; slow to CHEERFUL |
| **RULE_CONSCIOUSNESS** | Increases GUILTY if rules broken; high affinity for RESPECTED | Buffer against GUILTY; moves toward SELFISH, CREATIVE |
| **SOCIAL_BOLDNESS** | Fast EXCITED; extreme buffer against REJECTED, INSECURE | High sensitivity to REJECTED; rapid ANXIOUS in groups |
| **SENSITIVITY** | Fast HURT or INTIMATE; high capacity for NURTURING | Buffer against HURT; remains CRITICAL, APATHETIC |
| **VIGILANCE** | Rapid HOSTILE, CRITICAL; blocks TRUSTING | Default moves toward TRUSTING, SATISFIED |
| **ABSTRACTEDNESS** | High baseline CREATIVE, THOUGHTFUL; prone to BORED | High affinity for SATISFIED; low CONFUSED |
| **PRIVATENESS** | Hard cap on INTIMATE, TRUSTING; emotions stay hidden | Rapid INTIMATE; transparent LOVING values |
| **APPREHENSION** | Default pull toward GUILTY, ASHAMED, INSECURE | High baseline PROUD; extreme buffer against ANXIOUS |
| **OPENNESS_TO_CHANGE** | Fast HOPEFUL, CREATIVE; low BORED | Increases CONFUSED, ANXIOUS when environment shifts |
| **SELF_RELIANCE** | Buffer against LONELY, REJECTED; moves to THOUGHTFUL | Rapid LONELY, HELPLESS when alone; needs APPRECIATED |
| **PERFECTIONISM** | High SATISFIED (when orderly) or CRITICAL (when messy) | High tolerance for BORED; buffer against GUILTY |
| **TENSION** | Rapid ANGRY, ANXIOUS; hard to reach CONTENT | Naturally high CONTENT; slow to move toward EXCITED |

### Coefficient Application

```python
# Traits automatically influence emotion transitions
individual = personaut.create_individual()
individual.add_trait(personaut.traits.create_trait(
    trait=personaut.traits.WARMTH,
    value=0.9  # High warmth
))

# When this individual experiences a situation that would normally
# increase HOSTILE by 0.5, the high WARMTH trait buffers it:
# - Actual HOSTILE increase: 0.5 * (1 - warmth_coefficient) ≈ 0.15
# - LOVING increase accelerated: automatically increases by 0.1
```

## Markov Chain Transitions

Emotional states transition based on probabilistic Markov chains influenced by:
- Current emotional state
- Trait coefficients
- Situational context
- Memory associations

```python
# Get transition probabilities from current state
probabilities = emotional_state.get_transition_probabilities(
    traits=individual.traits,
    situation=current_situation
)

# Simulate next state
next_state = emotional_state.transition(
    traits=individual.traits,
    situation=current_situation,
    stochastic=True  # Add randomness
)
```

## Best Practices

### Validation
- Always validate emotion values are between 0 and 1
- Use the provided constants instead of string literals when possible
- Handle edge cases where all emotions are at 0 or 1

### Performance
- Use batch operations (`change_state()`) instead of multiple `change_emotion()` calls
- Cache emotional state calculations when running many simulations
- Consider state_window size impact on memory calculations

### Realism
- Avoid setting emotions to exactly 0 or 1 (use 0.01 - 0.99 range)
- Ensure emotional changes are gradual unless triggered by significant events
- Consider category balance (high fear typically reduces joy)

## Examples

### Creating a Nervous Individual

```python
import personaut

individual = personaut.create_individual(name="Alex")

# Set initial nervous disposition
individual.emotional_state.change_state({
    'anxious': 0.6,
    'insecure': 0.5,
    'hopeful': 0.3,
    'content': 0.2
})

# Add trait that reinforces this
individual.add_trait(personaut.traits.create_trait(
    trait=personaut.traits.APPREHENSION,
    value=0.8
))
```

### Simulating Emotional Response

```python
# After a positive interaction
def handle_positive_feedback(individual: Individual) -> None:
    state = individual.emotional_state
    
    # Reduce negative emotions
    state.decrease_emotion('anxious', 0.2)
    state.decrease_emotion('insecure', 0.1)
    
    # Increase positive emotions
    state.increase_emotion('appreciated', 0.3)
    state.increase_emotion('hopeful', 0.2)
    state.increase_emotion('content', 0.15)
```

### Checking Emotional Thresholds

```python
def should_trigger_mask(individual: Individual, mask: Mask) -> bool:
    """Check if emotional state should trigger a mask."""
    state = individual.emotional_state
    
    # Check if any fear emotion exceeds threshold
    if state.any_above(0.7, category='fear'):
        return mask.name == 'defensive'
    
    # Check specific emotion combination
    if state.get_emotion('angry') > 0.6 and state.get_emotion('hostile') > 0.5:
        return mask.name == 'confrontational'
    
    return False
```

## Related Documentation

- [TRAITS.md](./TRAITS.md) - Personality trait system and configurations
- [SIMULATIONS.md](./SIMULATIONS.md) - How emotions affect simulations
- [../PERSONAS.md](../PERSONAS.md) - Main agent guidelines
