"""Unit tests for the simulation business-logic engine.

These tests exercise the engine functions directly (no Flask app context),
validating PDK hydration, emotion radar, emotional dynamics, random persona
generation, prompt builders, outcome evaluation, and correlation analysis.
"""

from __future__ import annotations

import pytest

from personaut.individuals import create_individual
from personaut.server.ui.views import simulation_engine as engine
from personaut.situations import create_situation


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset LLM singleton between tests."""
    engine._llm_instance = None
    engine._llm_checked = False
    yield


@pytest.fixture()
def alice():
    """A PDK Individual for conversation tests."""
    return create_individual(
        name="Alice",
        traits={
            "warmth": 0.8,
            "dominance": 0.3,
            "emotional_stability": 0.7,
            "liveliness": 0.6,
            "sensitivity": 0.5,
        },
        emotional_state={"cheerful": 0.6, "content": 0.5},
        metadata={"occupation": "teacher"},
    )


@pytest.fixture()
def bob():
    """A second PDK Individual."""
    return create_individual(
        name="Bob",
        traits={
            "warmth": 0.4,
            "dominance": 0.7,
            "emotional_stability": 0.5,
            "liveliness": 0.5,
            "sensitivity": 0.4,
        },
        emotional_state={"content": 0.6, "anxious": 0.2},
        metadata={"occupation": "engineer"},
    )


@pytest.fixture()
def classroom():
    """A PDK Situation."""
    return create_situation(
        modality="in_person",
        description="A discussion in a college classroom",
        location="Room 301",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Hydration helpers
# ═══════════════════════════════════════════════════════════════════════════


class TestSimHydrateIndividual:
    def test_basic_hydration(self) -> None:
        data = {
            "id": "ind_sim_001",
            "name": "Sim Test",
            "trait_profile": {"warmth": 0.7},
            "emotional_state": {"cheerful": 0.4},
            "metadata": {"occupation": "tester"},
        }
        individual = engine.hydrate_individual(data)
        assert individual.name == "Sim Test"

    def test_empty_profile(self) -> None:
        data = {
            "id": "ind_empty",
            "name": "Empty",
            "trait_profile": {},
            "emotional_state": {},
            "metadata": {},
        }
        individual = engine.hydrate_individual(data)
        assert individual.name == "Empty"


class TestSimHydrateSituation:
    def test_basic(self) -> None:
        data = {
            "id": "sit_001",
            "description": "A quiet library",
            "modality": "in_person",
            "location": "Main Hall",
            "context": {"noise_level": "quiet"},
        }
        situation = engine.hydrate_situation(data)
        assert situation.description == "A quiet library"


# ═══════════════════════════════════════════════════════════════════════════
# Emotion radar
# ═══════════════════════════════════════════════════════════════════════════


class TestSimEmotionRadar:
    def test_empty(self) -> None:
        radar = engine.compute_emotion_radar({})
        assert all(v == 0.0 for v in radar.values())

    def test_single_emotion(self) -> None:
        radar = engine.compute_emotion_radar({"angry": 0.9})
        anger_label = [k for k in radar if k.lower() == "anger"][0]
        assert radar[anger_label] == 0.9

    def test_get_emotion_radar_data(self, alice) -> None:
        data = engine.get_emotion_radar_data(alice)
        # simulation_engine's version returns categories/values/emotions
        assert "categories" in data
        assert "values" in data
        assert "emotions" in data
        assert len(data["categories"]) == 6
        assert len(data["values"]) == 6


# ═══════════════════════════════════════════════════════════════════════════
# Emotional dynamics
# ═══════════════════════════════════════════════════════════════════════════


class TestAnalyzeSimulationEmotions:
    def test_no_llm_returns_dict(self, alice, bob) -> None:
        result = engine.analyze_simulation_emotions(
            alice,
            [bob],
            "I'm so happy to see you!",
            [],
        )
        # Without LLM — heuristic analysis
        assert isinstance(result, dict)

    def test_greetings_boost_cheerful(self, alice, bob) -> None:
        result = engine.analyze_simulation_emotions(
            alice,
            [bob],
            "Hello, welcome!",
            [],
        )
        if result:
            # Heuristic should pick up positive sentiment
            assert any(k in result for k in ["cheerful", "friendly", "content"])


class TestUpdateSpeakerEmotions:
    def test_updates_emotional_state(self, alice) -> None:
        engine.update_speaker_emotions(alice, {"cheerful": 0.9})
        updated = alice.get_emotional_state().to_dict()
        # Emotion should change (may not be exact due to blending)
        assert updated.get("cheerful", 0) > 0


# ═══════════════════════════════════════════════════════════════════════════
# Random persona generation
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateRandomIndividual:
    def test_generates_named_individual(self) -> None:
        individual = engine.generate_random_individual(0)
        assert individual.name is not None
        assert len(individual.name) > 0

    def test_generates_with_traits(self) -> None:
        """Generated persona should have a trait profile."""
        individual = engine.generate_random_individual(0)
        traits = individual.traits.to_dict() if individual.traits else {}
        assert len(traits) > 0

    def test_different_indices_produce_variation(self) -> None:
        """Multiple random individuals should show diversity."""
        individuals = [engine.generate_random_individual(i) for i in range(5)]
        names = {ind.name for ind in individuals}
        # At least some should differ (random generation)
        assert len(names) >= 2

    def test_vary_by_traits(self) -> None:
        individual = engine.generate_random_individual(
            0,
            vary_by="traits",
            fixed_emotions={"content": 0.5},
        )
        traits = individual.traits.to_dict() if individual.traits else {}
        assert len(traits) > 0

    def test_vary_by_emotions(self) -> None:
        individual = engine.generate_random_individual(
            0,
            vary_by="emotions",
            fixed_traits={"warmth": 0.5},
        )
        es = individual.get_emotional_state()
        assert es is not None

    def test_fixed_traits_applied(self) -> None:
        fixed = {"warmth": 0.42, "dominance": 0.42}
        individual = engine.generate_random_individual(
            0,
            vary_by="emotions",
            fixed_traits=fixed,
        )
        profile = individual.traits.to_dict() if individual.traits else {}
        if profile:
            assert profile.get("warmth") == pytest.approx(0.42, abs=0.01)

    def test_has_metadata(self) -> None:
        individual = engine.generate_random_individual(0)
        assert individual.metadata is not None
        assert "occupation" in individual.metadata
        assert "speaking_style" in individual.metadata


class TestGenerateRandomSituation:
    def test_returns_situation_and_params(self) -> None:
        situation, params = engine.generate_random_situation()
        assert situation is not None
        assert isinstance(params, dict)
        assert "modality" in params
        assert "location" in params


# ═══════════════════════════════════════════════════════════════════════════
# Prompt builders
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildConversationPrompt:
    def test_returns_string(self, alice, bob, classroom) -> None:
        prompt = engine.build_conversation_prompt(
            [alice, bob],
            classroom,
            0,
            alice,
            [],
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_includes_speaker_name(self, alice, bob, classroom) -> None:
        prompt = engine.build_conversation_prompt(
            [alice, bob],
            classroom,
            0,
            alice,
            [],
        )
        assert "Alice" in prompt

    def test_includes_history(self, alice, bob, classroom) -> None:
        history = [
            {"speaker": "Alice", "content": "Hello!"},
            {"speaker": "Bob", "content": "Hi there!"},
        ]
        prompt = engine.build_conversation_prompt(
            [alice, bob],
            classroom,
            2,
            alice,
            history,
        )
        assert "Hello!" in prompt
        assert "Hi there!" in prompt


class TestBuildSurveyPrompt:
    def test_returns_string(self, alice) -> None:
        question = {"text": "How do you feel today?", "type": "open_ended"}
        prompt = engine.build_survey_prompt(alice, question, None)
        assert isinstance(prompt, str)
        assert "How do you feel" in prompt

    def test_includes_individual_name(self, alice) -> None:
        question = {"text": "Rate your mood", "type": "likert_5"}
        prompt = engine.build_survey_prompt(alice, question, None)
        assert "Alice" in prompt

    def test_with_image_context(self, alice) -> None:
        question = {"text": "What do you see?", "type": "open_ended"}
        prompt = engine.build_survey_prompt(
            alice,
            question,
            None,
            has_image=True,
            image_description="A sunset over mountains",
        )
        assert "sunset" in prompt or "image" in prompt.lower()


# ═══════════════════════════════════════════════════════════════════════════
# LLM response (no LLM → None)
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateLLMResponse:
    def test_returns_none_without_llm(self) -> None:
        result = engine.generate_llm_response("Hello")
        assert result is None

    def test_returns_none_multimodal_without_llm(self) -> None:
        result = engine.generate_llm_response_multimodal("Hello")
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# Outcome evaluation
# ═══════════════════════════════════════════════════════════════════════════


class TestEvaluateOutcome:
    def test_returns_expected_keys(self, alice) -> None:
        history = [
            {"speaker": "Agent", "content": "Would you like to try our new product?"},
            {"speaker": "Alice", "content": "Sure, I'd love to!"},
        ]
        result = engine.evaluate_outcome(
            "Customer agrees to try product",
            history,
            "Alice",
            alice,
        )
        # The engine returns 'achieved' (not 'success') and 'confidence'
        assert "achieved" in result
        assert "confidence" in result
        assert isinstance(result["achieved"], bool)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_no_llm_returns_not_achieved(self, alice) -> None:
        """Without LLM, outcome evaluation falls back to not-achieved."""
        history = [
            {"speaker": "Agent", "content": "Can I sign you up?"},
            {"speaker": "Alice", "content": "Yes, absolutely! Sign me up!"},
        ]
        result = engine.evaluate_outcome(
            "Customer signs up",
            history,
            "Alice",
            alice,
        )
        # Without LLM: achieved=False, confidence=0.0
        assert result["achieved"] is False
        assert "reasoning" in result

    def test_empty_conversation(self, alice) -> None:
        result = engine.evaluate_outcome(
            "Customer buys something",
            [],
            "Alice",
            alice,
        )
        assert isinstance(result, dict)
        assert "achieved" in result


# ═══════════════════════════════════════════════════════════════════════════
# Correlation analysis
# ═══════════════════════════════════════════════════════════════════════════


class TestTraitCorrelations:
    def test_empty_trials(self) -> None:
        result = engine.compute_trait_correlations([])
        assert isinstance(result, dict)

    def test_with_trials(self) -> None:
        trials = [
            {
                "customer_traits": {"warmth": 0.8, "dominance": 0.3},
                "outcome": {"achieved": True, "confidence": 0.9},
            },
            {
                "customer_traits": {"warmth": 0.2, "dominance": 0.9},
                "outcome": {"achieved": False, "confidence": 0.3},
            },
            {
                "customer_traits": {"warmth": 0.7, "dominance": 0.4},
                "outcome": {"achieved": True, "confidence": 0.8},
            },
        ]
        result = engine.compute_trait_correlations(trials)
        assert isinstance(result, dict)


class TestEmotionCorrelations:
    def test_empty_trials(self) -> None:
        result = engine.compute_emotion_correlations([])
        assert isinstance(result, dict)

    def test_with_trials(self) -> None:
        trials = [
            {
                "customer_emotions": {"cheerful": 0.8, "anxious": 0.1},
                "outcome": {"achieved": True, "confidence": 0.9},
            },
            {
                "customer_emotions": {"cheerful": 0.2, "anxious": 0.8},
                "outcome": {"achieved": False, "confidence": 0.3},
            },
        ]
        result = engine.compute_emotion_correlations(trials)
        assert isinstance(result, dict)


class TestSituationCorrelations:
    def test_empty_trials(self) -> None:
        result = engine.compute_situation_correlations([])
        assert isinstance(result, dict)

    def test_with_trials(self) -> None:
        trials = [
            {
                "situation_params": {"modality": "in_person", "location": "Office"},
                "outcome": {"achieved": True, "confidence": 0.9},
            },
            {
                "situation_params": {"modality": "phone_call", "location": "Home"},
                "outcome": {"achieved": False, "confidence": 0.3},
            },
        ]
        result = engine.compute_situation_correlations(trials)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════
# Survey fallback
# ═══════════════════════════════════════════════════════════════════════════


class TestSurveyFallback:
    def test_returns_string(self, alice) -> None:
        question = {"text": "How do you feel?", "type": "open_ended"}
        result = engine.survey_fallback(alice, question)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_likert_returns_number(self, alice) -> None:
        question = {"text": "Rate 1-5", "type": "likert_5"}
        result = engine.survey_fallback(alice, question)
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════════════════════
# Module constants
# ═══════════════════════════════════════════════════════════════════════════


class TestModuleConstants:
    def test_emotion_categories_defined(self) -> None:
        categories = engine.EMOTION_CATEGORIES
        assert len(categories) == 6
        for _name, emotions in categories.items():
            assert isinstance(emotions, list)
            assert len(emotions) > 0

    def test_category_colors_defined(self) -> None:
        colors = engine.CATEGORY_COLORS
        assert len(colors) == 6
        for _name, color in colors.items():
            assert color.startswith("#")
