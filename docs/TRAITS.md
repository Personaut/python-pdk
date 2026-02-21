# Trait System Guide

This document describes the personality trait system in the Personaut PDK. Traits are stable personality characteristics that influence how individuals respond emotionally and behaviorally across situations.

## Overview

The trait system models 17 personality traits based on established psychological frameworks. Each trait has a value between 0 and 1, where:
- `0.0` = trait is at the low extreme
- `0.5` = trait is at the moderate/neutral level
- `1.0` = trait is at the high extreme

Traits differ from emotions in that:
- **Traits** are stable over time and represent core personality
- **Emotions** are transient states that fluctuate based on situations

Traits influence:
- Emotional state transitions (via coefficients)
- Behavioral response patterns
- Prompt generation for simulations
- Default emotional baselines

## Trait Definitions

### WARMTH (Factor A)

The degree to which an individual is outgoing, kindly, and interested in others versus reserved and detached.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Outgoing, kindly, shows genuine interest in others |
| Moderate (0.4-0.6) | Balanced warmth, selectively engaging |
| Low (0.0-0.3) | Detached, critical, maintains emotional distance |

```python
import personaut

warmth = personaut.trait.WARMTH

individual = personaut.create_individual(name="Sarah")
individual.set_trait("warmth", 0.8)
```

### REASONING (Factor B)

The capacity for abstract thinking versus concrete, practical thinking.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Abstract thinking, higher mental capacity, quick to understand |
| Moderate (0.4-0.6) | Balanced reasoning abilities |
| Low (0.0-0.3) | Concrete thinking, practical orientation |

```python
reasoning = personaut.trait.REASONING
```

### EMOTIONAL_STABILITY (Factor C)

The degree of emotional resilience versus reactivity to stress and negative situations.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Stable, mature, handles stress well, composed |
| Moderate (0.4-0.6) | Generally stable with occasional reactivity |
| Low (0.0-0.3) | Reactive, emotionally sensitive, easily affected |

```python
emotional_stability = personaut.trait.EMOTIONAL_STABILITY
```

### DOMINANCE (Factor E)

The tendency to be assertive and competitive versus deferential and accommodating.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Assertive, competitive, takes charge |
| Moderate (0.4-0.6) | Balanced assertiveness, situationally adaptive |
| Low (0.0-0.3) | Deferential, humble, yielding to others |

```python
dominance = personaut.trait.DOMINANCE
```

### HUMILITY (Factor H-H)

The degree of modesty and sincerity versus arrogance and entitlement.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Modest, sincere, avoids attention |
| Moderate (0.4-0.6) | Balanced self-regard |
| Low (0.0-0.3) | Arrogant, entitled, seeks recognition |

```python
humility = personaut.trait.HUMILITY

# Example: setting humility
individual = personaut.create_individual(name="Alex")
individual.set_trait("humility", 0.8)
```

### LIVELINESS (Factor F)

The level of spontaneity and enthusiasm versus seriousness and restraint.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Spontaneous, enthusiastic, expressive |
| Moderate (0.4-0.6) | Balanced energy levels |
| Low (0.0-0.3) | Serious, restrained, measured |

```python
liveliness = personaut.trait.LIVELINESS
```

### RULE_CONSCIOUSNESS (Factor G)

The degree of conscientiousness and moral adherence versus expediency.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Conscientious, moral, follows rules strictly |
| Moderate (0.4-0.6) | Generally rule-following with flexibility |
| Low (0.0-0.3) | Expedient, flexible with rules, pragmatic |

```python
rule_consciousness = personaut.trait.RULE_CONSCIOUSNESS
```

### SOCIAL_BOLDNESS (Factor H)

The tendency to be socially venturesome versus shy and timid.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Venturesome, uninhibited, thick-skinned socially |
| Moderate (0.4-0.6) | Selectively bold in social situations |
| Low (0.0-0.3) | Shy, timid, threat-sensitive socially |

```python
social_boldness = personaut.trait.SOCIAL_BOLDNESS
```

### SENSITIVITY (Factor I)

The degree of emotional sensitivity and refinement versus utilitarian practicality.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Tender-minded, refined, emotionally sensitive |
| Moderate (0.4-0.6) | Balanced sensitivity |
| Low (0.0-0.3) | Utilitarian, tough-minded, practical |

```python
sensitivity = personaut.trait.SENSITIVITY
```

### VIGILANCE (Factor L)

The tendency to be skeptical and suspicious versus trusting and accepting.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Skeptical, suspicious, questions motives |
| Moderate (0.4-0.6) | Reasonably cautious |
| Low (0.0-0.3) | Trusting, easy-going, accepting |

```python
vigilance = personaut.trait.VIGILANCE
```

### ABSTRACTEDNESS (Factor M)

The orientation toward imagination and ideas versus practical groundedness.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Imaginative, idea-oriented, abstracted |
| Moderate (0.4-0.6) | Balanced between ideas and practicality |
| Low (0.0-0.3) | Grounded, practical, solution-oriented |

```python
abstractedness = personaut.trait.ABSTRACTEDNESS
```

### PRIVATENESS (Factor N)

The tendency to be discreet and polished versus forthright and genuine.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Polished, discreet, private about personal matters |
| Moderate (0.4-0.6) | Selectively private |
| Low (0.0-0.3) | Forthright, genuine, open about feelings |

```python
privateness = personaut.trait.PRIVATENESS
```

### APPREHENSION (Factor O)

The tendency toward worry and self-doubt versus self-assurance.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Insecure, worried, self-doubting |
| Moderate (0.4-0.6) | Occasional self-doubt |
| Low (0.0-0.3) | Self-assured, placid, confident |

```python
apprehension = personaut.trait.APPREHENSION
```

### OPENNESS_TO_CHANGE (Factor Q1)

The willingness to experiment and embrace change versus preference for tradition.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Experimenting, open to new ideas, flexible |
| Moderate (0.4-0.6) | Balanced openness |
| Low (0.0-0.3) | Traditional, conservative, prefers familiar |

```python
openness_to_change = personaut.trait.OPENNESS_TO_CHANGE
```

### SELF_RELIANCE (Factor Q2)

The preference for solitude and self-sufficiency versus group orientation.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Solitary, resourceful, self-sufficient |
| Moderate (0.4-0.6) | Balanced between independence and group needs |
| Low (0.0-0.3) | Group-oriented, seeks belonging, affiliative |

```python
self_reliance = personaut.trait.SELF_RELIANCE
```

### PERFECTIONISM (Factor Q3)

The degree of self-discipline and orderliness versus tolerance for disorder.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Self-disciplined, compulsive, perfectionistic |
| Moderate (0.4-0.6) | Generally organized |
| Low (0.0-0.3) | Tolerates disorder, flexible about standards |

```python
perfectionism = personaut.trait.PERFECTIONISM
```

### TENSION (Factor Q4)

The level of impatience and drive versus relaxation and tranquility.

| Value | Interpretation |
|-------|----------------|
| High (0.7-1.0) | Impatient, driven, high-strung |
| Moderate (0.4-0.6) | Moderate tension levels |
| Low (0.0-0.3) | Relaxed, tranquil, patient |

```python
tension = personaut.trait.TENSION
```

## Trait Constants Reference

All 17 traits as defined in the Personaut PDK:

```python
import personaut

# Higher warmth means outgoing/kindly and less means detached and more critical
warmth = personaut.trait.WARMTH

# Higher reasoning means abstract/higher capacity and less means concrete
reasoning = personaut.trait.REASONING

# Higher emotional_stability means stable/mature and less means reactive
emotional_stability = personaut.trait.EMOTIONAL_STABILITY

# Higher dominance means assertive/competitive and less means deferential/humble
dominance = personaut.trait.DOMINANCE

# Higher humility means modest/sincere and less means arrogant/entitled
humility = personaut.trait.HUMILITY

# Higher liveliness means spontaneous/enthusiastic and less means serious/restrained
liveliness = personaut.trait.LIVELINESS

# Higher rule_consciousness means conscientious/moral and less means expedient
rule_consciousness = personaut.trait.RULE_CONSCIOUSNESS

# Higher social_boldness means venturesome/uninhibited and less means shy/timid
social_boldness = personaut.trait.SOCIAL_BOLDNESS

# Higher sensitivity means tender-minded/refined and less means utilitarian/tough
sensitivity = personaut.trait.SENSITIVITY

# Higher vigilance means skeptical/suspicious and less means trusting/easy-going
vigilance = personaut.trait.VIGILANCE

# Higher abstractedness means imaginative/idea-oriented and less means grounded/practical
abstractedness = personaut.trait.ABSTRACTEDNESS

# Higher privateness means polished/discreet and less means forthright/genuine
privateness = personaut.trait.PRIVATENESS

# Higher apprehension means insecure/worried and less means self-assured/placid
apprehension = personaut.trait.APPREHENSION

# Higher openness_to_change means experimenting and less means traditional/conservative
openness_to_change = personaut.trait.OPENNESS_TO_CHANGE

# Higher self_reliance means solitary/resourceful and less means group-oriented
self_reliance = personaut.trait.SELF_RELIANCE

# Higher perfectionism means self-disciplined and less means tolerates disorder
perfectionism = personaut.trait.PERFECTIONISM

# Higher tension means impatient/driven and less means relaxed/tranquil
tension = personaut.trait.TENSION
```

## Creating Traits

### Basic Trait Setting

```python
import personaut

# Set a trait value directly
individual = personaut.create_individual(name="Sarah")
individual.set_trait("warmth", 0.8)
```

### Setting Multiple Traits

```python
# Set multiple traits on creation
individual = personaut.create_individual(
    name="Sarah",
    traits={"warmth": 0.8, "humility": 0.7}
)

# Or set them individually
individual.set_trait("humility", 0.8)
```

### Custom Traits

> **Planned Feature (not yet implemented):** `personaut.traits.create_custom_trait()`
> will allow defining new trait types with custom emotion coefficients.

## Trait-Emotion Coefficients

Each trait has default coefficients that influence how emotional states change. These coefficients determine:
- Which emotions are affected by the trait
- The direction of influence (increase/decrease)
- The magnitude of the effect

### Coefficient System

```python
# Coefficient formula for emotion change:
# actual_change = base_change * (1 + trait_value * coefficient)

# Example: WARMTH with coefficient 0.3 for LOVING
# If base_change for LOVING is 0.2 and warmth=0.8:
# actual_change = 0.2 * (1 + 0.8 * 0.3) = 0.2 * 1.24 = 0.248
```

### Default Coefficient Mappings

The following table shows how each trait affects emotional transitions based on its value:

#### WARMTH (A)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Speeds up movement toward LOVING and TRUSTING; buffers against HOSTILE |
| **Low** | Increases likelihood of CRITICAL and LONELY; slows down NURTURING |

```python
# Default coefficients for WARMTH
warmth_coefficients = {
    'loving': 0.4,      # High warmth accelerates loving
    'trusting': 0.3,    # High warmth accelerates trusting
    'hostile': -0.5,    # High warmth buffers hostile
    'nurturing': 0.3,   # High warmth accelerates nurturing
    'critical': -0.3,   # High warmth reduces critical
    'lonely': -0.2      # High warmth reduces lonely
}
```

#### REASONING (B)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Accelerates CONFUSED → THOUGHTFUL transitions; buffers against HELPLESS |
| **Low** | Increases susceptibility to CONFUSED or ANXIOUS when logic is required |

```python
reasoning_coefficients = {
    'thoughtful': 0.4,
    'confused': -0.4,
    'helpless': -0.3,
    'anxious': -0.2
}
```

#### EMOTIONAL_STABILITY (C)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Strong buffer for all "Sad" and "Fear" categories; stabilizes CONTENT |
| **Low** | Rapid spikes in ANXIOUS, DEPRESSED, and HURT; values shift 0 to 1 quickly |

```python
emotional_stability_coefficients = {
    # Fear category buffers
    'anxious': -0.5,
    'insecure': -0.4,
    'helpless': -0.4,
    'rejected': -0.3,
    'confused': -0.3,
    'submissive': -0.2,
    # Sad category buffers
    'depressed': -0.5,
    'guilty': -0.3,
    'ashamed': -0.3,
    'lonely': -0.3,
    'hurt': -0.4,
    # Positive stabilization
    'content': 0.4
}
```

#### DOMINANCE (E)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Correlates with PROUD and IMPORTANT; moves toward ANGRY if challenged |
| **Low** | High affinity for SUBMISSIVE; moves toward APPRECIATED when guided |

```python
dominance_coefficients = {
    'proud': 0.4,
    'important': 0.3,
    'angry': 0.2,       # When challenged
    'submissive': -0.5,
    'appreciated': -0.2  # When guided (low dominance)
}
```

#### HUMILITY (H-H)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Increases FAITHFUL and SATISFIED; acts as a massive buffer against SELFISH |
| **Low** | Faster movement toward SELFISH and IMPORTANT (ego-driven) |

```python
humility_coefficients = {
    'faithful': 0.3,
    'satisfied': 0.2,
    'selfish': -0.6,    # Massive buffer
    'important': -0.3
}
```

#### LIVELINESS (F)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Naturally high baseline for EXCITED and ENERGETIC; low tolerance for BORED |
| **Low** | High baseline for THOUGHTFUL; slow to move toward CHEERFUL |

```python
liveliness_coefficients = {
    'excited': 0.5,
    'energetic': 0.4,
    'bored': -0.5,
    'cheerful': 0.3,
    'thoughtful': -0.2  # Low liveliness increases thoughtful
}
```

#### RULE_CONSCIOUSNESS (G)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Increases GUILTY if rules are broken; high affinity for RESPECTED |
| **Low** | Buffer against GUILTY; more likely to move toward SELFISH or CREATIVE |

```python
rule_consciousness_coefficients = {
    'guilty': 0.4,      # When rules broken
    'respected': 0.3,
    'selfish': -0.3,
    'creative': -0.2    # Low rule consciousness increases creative
}
```

#### SOCIAL_BOLDNESS (H)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Fast movement toward EXCITED; extreme buffer against REJECTED/INSECURE |
| **Low** | High sensitivity to REJECTED; rapid movement toward ANXIOUS in groups |

```python
social_boldness_coefficients = {
    'excited': 0.4,
    'rejected': -0.6,   # Extreme buffer
    'insecure': -0.5,   # Extreme buffer
    'anxious': -0.4
}
```

#### SENSITIVITY (I)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Fast movement toward HURT or INTIMATE; high capacity for NURTURING |
| **Low** | Buffer against HURT; remains CRITICAL or APATHETIC under pressure |

```python
sensitivity_coefficients = {
    'hurt': 0.4,
    'intimate': 0.4,
    'nurturing': 0.3,
    'critical': -0.3,
    'apathetic': -0.2
}
```

#### VIGILANCE (L)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Rapid movement toward HOSTILE and CRITICAL; blocks TRUSTING from rising |
| **Low** | Default state moves toward TRUSTING and SATISFIED; low HATEFUL |

```python
vigilance_coefficients = {
    'hostile': 0.4,
    'critical': 0.3,
    'trusting': -0.5,   # Blocks trusting
    'satisfied': -0.2,
    'hateful': 0.2
}
```

#### ABSTRACTEDNESS (M)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | High baseline for CREATIVE and THOUGHTFUL; prone to BORED if grounded |
| **Low** | High affinity for SATISFIED through practical tasks; low CONFUSED |

```python
abstractedness_coefficients = {
    'creative': 0.4,
    'thoughtful': 0.3,
    'bored': 0.2,       # When grounded in reality
    'satisfied': -0.2,
    'confused': -0.3
}
```

#### PRIVATENESS (N)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Hard cap on INTIMATE and TRUSTING; emotions like HURT stay hidden/internal |
| **Low** | Rapid movement toward INTIMATE; values for LOVING are transparent |

```python
privateness_coefficients = {
    'intimate': -0.5,   # Hard cap
    'trusting': -0.4,   # Hard cap
    'hurt': -0.2,       # Stays hidden
    'loving': -0.3
}
```

#### APPREHENSION (O)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Default pull toward GUILTY, ASHAMED, and INSECURE; hard to move to PROUD |
| **Low** | High baseline for PROUD (self-assured); extreme buffer against ANXIOUS |

```python
apprehension_coefficients = {
    'guilty': 0.4,
    'ashamed': 0.4,
    'insecure': 0.4,
    'proud': -0.4,
    'anxious': 0.3
}
```

#### OPENNESS_TO_CHANGE (Q1)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Fast movement toward HOPEFUL and CREATIVE; low BORED |
| **Low** | Increases CONFUSED or ANXIOUS when environment shifts |

```python
openness_to_change_coefficients = {
    'hopeful': 0.4,
    'creative': 0.3,
    'bored': -0.3,
    'confused': -0.2,
    'anxious': -0.2
}
```

#### SELF_RELIANCE (Q2)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Buffer against LONELY and REJECTED; naturally moves to THOUGHTFUL |
| **Low** | Rapid rise in LONELY or HELPLESS when left alone; needs APPRECIATED |

```python
self_reliance_coefficients = {
    'lonely': -0.5,
    'rejected': -0.3,
    'thoughtful': 0.3,
    'helpless': -0.3,
    'appreciated': -0.2  # Low self-reliance needs this
}
```

#### PERFECTIONISM (Q3)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | High affinity for SATISFIED (when orderly) or CRITICAL (when messy) |
| **Low** | High tolerance for BORED; buffer against GUILTY regarding disorder |

```python
perfectionism_coefficients = {
    'satisfied': 0.3,   # When orderly
    'critical': 0.3,    # When messy
    'bored': -0.2,
    'guilty': -0.2
}
```

#### TENSION (Q4)

| Trait Level | Emotion Effects |
|-------------|-----------------|
| **High** | Rapid movement toward ANGRY and ANXIOUS; hard to reach CONTENT |
| **Low** | Naturally high CONTENT and RELAXED; slow to move toward EXCITED |

```python
tension_coefficients = {
    'angry': 0.4,
    'anxious': 0.4,
    'content': -0.5,    # Hard to reach
    'excited': 0.2      # Low tension slows excited
}
```

## Trait Profiles

Create complete personality profiles by combining multiple traits:

### Example Profiles

```python
import personaut

def create_extrovert_profile(individual: Individual) -> None:
    """Create an extroverted personality profile."""
    traits = [
        (personaut.traits.WARMTH, 0.8),
        (personaut.traits.LIVELINESS, 0.7),
        (personaut.traits.SOCIAL_BOLDNESS, 0.8),
        (personaut.traits.SELF_RELIANCE, 0.3),
        (personaut.traits.PRIVATENESS, 0.2)
    ]
    for trait, value in traits:
        individual.set_trait(trait.lower(), value)

def create_introvert_profile(individual: Individual) -> None:
    """Create an introverted personality profile."""
    traits = [
        (personaut.traits.WARMTH, 0.4),
        (personaut.traits.LIVELINESS, 0.3),
        (personaut.traits.SOCIAL_BOLDNESS, 0.2),
        (personaut.traits.SELF_RELIANCE, 0.8),
        (personaut.traits.PRIVATENESS, 0.7),
        (personaut.traits.ABSTRACTEDNESS, 0.7)
    ]
    for trait, value in traits:
        individual.set_trait(trait.lower(), value)

def create_anxious_profile(individual: Individual) -> None:
    """Create an anxiety-prone personality profile."""
    traits = [
        (personaut.traits.EMOTIONAL_STABILITY, 0.2),
        (personaut.traits.APPREHENSION, 0.8),
        (personaut.traits.TENSION, 0.7),
        (personaut.traits.VIGILANCE, 0.6),
        (personaut.traits.SOCIAL_BOLDNESS, 0.2)
    ]
    for trait, value in traits:
        individual.set_trait(trait.lower(), value)

def create_leader_profile(individual: Individual) -> None:
    """Create a leadership-oriented personality profile."""
    traits = [
        (personaut.traits.DOMINANCE, 0.8),
        (personaut.traits.EMOTIONAL_STABILITY, 0.7),
        (personaut.traits.SOCIAL_BOLDNESS, 0.7),
        (personaut.traits.RULE_CONSCIOUSNESS, 0.6),
        (personaut.traits.SELF_RELIANCE, 0.6),
        (personaut.traits.TENSION, 0.5)
    ]
    for trait, value in traits:
        individual.set_trait(trait.lower(), value)
```

### Using Profiles

```python
sarah = personaut.create_individual(name="Sarah")
create_introvert_profile(sarah)

# Sarah now has a complete introvert personality
# Her emotional state transitions will be influenced accordingly
```

## Trait API Reference

| Method | Description |
|--------|-------------|
| `individual.set_trait(name, value)` | Set a trait value (0.0-1.0) |
| `individual.get_trait(name)` | Get an individual's trait value |
| `individual.traits` | The TraitProfile object for an individual |
| `individual.traits.to_dict()` | Get all traits as a dict |
| `individual.traits.get_high_traits(threshold=0.7)` | Get traits above threshold |
| `individual.traits.get_low_traits(threshold=0.3)` | Get traits below threshold |
| `personaut.traits.get_coefficient(trait, emotion)` | Get influence coefficient |
| `personaut.traits.get_traits_affecting_emotion(emotion)` | Get all traits affecting an emotion |
| `personaut.traits.is_valid_trait(name)` | Check if a trait name is valid |
## Best Practices

### Trait Balance
- Avoid extreme values (0.0 or 1.0) unless intentional
- Consider trait interactions (high vigilance + low warmth creates very distrustful persona)
- Use profiles for consistent personality archetypes

### Custom Traits
- Define clear high/low descriptions
- Map emotion coefficients carefully
- Test coefficient magnitudes for balanced effects

### Simulation Accuracy
- Match trait profiles to target demographics
- Validate trait-emotion interactions for realism
- Document any custom coefficient adjustments

## Related Documentation

- [EMOTIONS.md](./EMOTIONS.md) - Emotion system and how traits affect it
- [PROMPTS.md](./PROMPTS.md) - How traits influence prompt generation
- [SIMULATIONS.md](./SIMULATIONS.md) - Trait effects in simulations
- [../PERSONAS.md](../PERSONAS.md) - Main agent guidelines
