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
| Hostile | `HOSTILE` | Actively antagonistic or unfriendly disposition |
| Hurt | `HURT` | Emotional pain from perceived wrongdoing |
| Angry | `ANGRY` | Strong displeasure or annoyance |
| Selfish | `SELFISH` | Prioritizing self-interest above others |
| Hateful | `HATEFUL` | Intense dislike or ill will |
| Critical | `CRITICAL` | Tendency to find fault or judge harshly |

### Sad/Sadness Category
Emotions related to loss, disappointment, and low energy states.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Guilty | `GUILTY` | Feeling responsible for wrongdoing |
| Ashamed | `ASHAMED` | Embarrassment about actions or self |
| Depressed | `DEPRESSED` | Persistent low mood and hopelessness |
| Lonely | `LONELY` | Feeling isolated or disconnected |
| Bored | `BORED` | Lack of interest or engagement |
| Apathetic | `APATHETIC` | Absence of emotion or motivation |

### Fear/Scared Category
Emotions related to threat perception and anxiety.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Rejected | `REJECTED` | Feeling dismissed or unwanted |
| Confused | `CONFUSED` | Uncertainty or lack of clarity |
| Submissive | `SUBMISSIVE` | Yielding to authority or pressure |
| Insecure | `INSECURE` | Self-doubt and lack of confidence |
| Anxious | `ANXIOUS` | Worry and unease about outcomes |
| Helpless | `HELPLESS` | Feeling powerless to change situation |

### Joy/Happiness Category
Emotions related to positive energy and enthusiasm.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Excited | `EXCITED` | Eager anticipation and high energy |
| Sensual | `SENSUAL` | Appreciation of physical pleasures |
| Energetic | `ENERGETIC` | Vitality and active engagement |
| Cheerful | `CHEERFUL` | Lighthearted and optimistic mood |
| Creative | `CREATIVE` | Inspired and imaginative state |
| Hopeful | `HOPEFUL` | Positive expectation for the future |

### Powerful/Confident Category
Emotions related to self-assurance and status.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Proud | `PROUD` | Satisfaction with achievements |
| Respected | `RESPECTED` | Feeling valued by others |
| Appreciated | `APPRECIATED` | Recognized for contributions |
| Important | `IMPORTANT` | Sense of personal significance |
| Faithful | `FAITHFUL` | Loyalty and commitment |
| Satisfied | `SATISFIED` | Contentment with current state |

### Peaceful/Calm Category
Emotions related to tranquility and connection.

| Emotion | Constant | Description |
|---------|----------|-------------|
| Content | `CONTENT` | Ease and acceptance |
| Thoughtful | `THOUGHTFUL` | Reflective and considerate state |
| Intimate | `INTIMATE` | Deep personal connection |
| Loving | `LOVING` | Affection and care for others |
| Trusting | `TRUSTING` | Confidence in others' reliability |
| Nurturing | `NURTURING` | Desire to care for and support |

## Emotion Constants Reference

The following shows the exact constant usage as defined in the Personaut PDK:

```python
from personaut.emotions.emotion import (
    # Anger/Mad
    HOSTILE, HURT, ANGRY, SELFISH, HATEFUL, CRITICAL,
    # Sad/Sadness
    GUILTY, ASHAMED, DEPRESSED, LONELY, BORED, APATHETIC,
    # Fear/Scared
    REJECTED, CONFUSED, SUBMISSIVE, INSECURE, ANXIOUS, HELPLESS,
    # Joy/Happiness
    EXCITED, SENSUAL, ENERGETIC, CHEERFUL, CREATIVE, HOPEFUL,
    # Powerful/Confident
    PROUD, RESPECTED, APPRECIATED, IMPORTANT, FAITHFUL, SATISFIED,
    # Peaceful/Calm
    CONTENT, THOUGHTFUL, INTIMATE, LOVING, TRUSTING, NURTURING,
    # Complete list
    ALL_EMOTIONS,
)

# Each constant is just a lowercase string:
print(HOSTILE)   # "hostile"
print(ANXIOUS)   # "anxious"
print(len(ALL_EMOTIONS))  # 36
```

## EmotionalState Class

The `EmotionalState` class manages all 36 emotions as a unified state object. By default, an `EmotionalState` contains all emotions defined in the current version of Personaut PDK.

> **Reference**: From the Personaut API specification:
> - Emotional States are made up by default of all of the emotions defined
> - You can add or remove emotions through an input list of emotions
> - If you do not put any emotion into the emotional state it defaults to all in the version of personaut

### Creating an EmotionalState

```python
from personaut.emotions.state import EmotionalState

# Create with default values (ALL 36 emotions included at baseline)
# This is the standard way to create an emotional state
emotional_state = EmotionalState()

# Create with only specific emotions (subset tracking)
# Only these emotions will be tracked; all others are excluded
emotional_state = EmotionalState(
    emotions=['angry', 'anxious', 'hopeful']
)

# Create with a non-zero baseline
emotional_state = EmotionalState(baseline=0.2)
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
from personaut.emotions.state import EmotionalState

emotional_state = EmotionalState()

# Change a single emotion to a specific value (0 to 1)
emotional_state.change_emotion('angry', 0.1)

# More examples:
emotional_state.change_emotion('hostile', 0.5)
emotional_state.change_emotion('loving', 0.8)
emotional_state.change_emotion('anxious', 0.3)
```

### Modifying Entire State

Use `change_state()` to modify multiple emotions at once. This method accepts a dictionary of emotion values and an optional `fill` parameter:

```python
from personaut.emotions.state import EmotionalState

emotional_state = EmotionalState()

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
from personaut.emotions.categories import EmotionCategory

# Get all emotions as a dictionary
all_emotions = emotional_state.to_dict()

# Get emotions by category
anger_emotions = emotional_state.get_category_emotions(EmotionCategory.ANGER)

# Get dominant emotion (highest value)
dominant = emotional_state.get_dominant()
# Returns: ('anxious', 0.7)

# Get top N emotions
top_emotions = emotional_state.get_top(n=3)
# Returns: [('anxious', 0.7), ('insecure', 0.6), ('helpless', 0.4)]

# Check if any emotion exceeds threshold
is_distressed = emotional_state.any_above(0.5, category=EmotionCategory.FEAR)
# Returns: True (anxious=0.7, insecure=0.6 both exceed 0.5)
```

### Complete API Reference

| Method | Description |
|--------|-------------|
| `EmotionalState()` | Create state with all 36 emotions at baseline |
| `EmotionalState(emotions=[...])` | Create state with only specified emotions |
| `EmotionalState(baseline=0.2)` | Create state with non-zero baseline |
| `change_emotion(emotion, value)` | Set a single emotion to exact value (0-1) |
| `change_state(dict, fill=None)` | Set multiple emotions; optionally fill others |
| `to_dict()` | Get all emotions as dictionary |
| `get_category_emotions(category)` | Get emotions for a specific category |
| `get_category_average(category)` | Get average intensity for a category |
| `get_dominant()` | Get emotion with highest value |
| `get_top(n)` | Get top N emotions by value |
| `any_above(threshold, category=None)` | Check if any emotion exceeds threshold |
| `get_valence()` | Calculate emotional valence (-1 to 1) |
| `get_arousal()` | Calculate emotional arousal (0 to 1) |
| `decay(turns_elapsed, rate)` | Decay emotions toward mood baseline |
| `apply_delta(deltas, intensity_scale)` | Shift emotions by delta amounts |
| `apply_trait_modulated_change(updates, traits)` | Apply trait-influenced changes |
| `apply_antagonism(strength)` | Suppress contradictory emotion pairs |
| `copy()` | Create a copy of the emotional state |

> **Note**: State calculation modes (`state_mode`, `state_window`, Markov chain transitions) and
> methods like `get_transition_probabilities()` and `transition()` are planned features
> not yet available in v0.3.0. Emotional dynamics are currently modeled through the
> `decay()`, `apply_delta()`, `apply_trait_modulated_change()`, and `apply_antagonism()`
> methods on `EmotionalState`.

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
from personaut import create_individual

individual = create_individual(name="Alex")

# Set initial nervous disposition
individual.emotional_state.change_state({
    'anxious': 0.6,
    'insecure': 0.5,
    'hopeful': 0.3,
    'content': 0.2
})

# Set apprehension trait to reinforce this
individual.set_trait('apprehension', 0.8)
```

### Simulating Emotional Response

```python
# After a positive interaction
def handle_positive_feedback(individual):
    state = individual.emotional_state
    
    # Use apply_delta to shift emotions
    state.apply_delta({
        'anxious': -0.2,
        'insecure': -0.1,
        'appreciated': 0.3,
        'hopeful': 0.2,
        'content': 0.15,
    })
```

### Checking Emotional Thresholds

```python
from personaut.emotions.categories import EmotionCategory

def should_trigger_mask(individual, mask):
    """Check if emotional state should trigger a mask."""
    state = individual.emotional_state
    
    # Check if any fear emotion exceeds threshold
    if state.any_above(0.7, category=EmotionCategory.FEAR):
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
