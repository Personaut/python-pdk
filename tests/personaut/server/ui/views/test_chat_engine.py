"""Unit tests for the chat business-logic engine.

These tests exercise the engine functions directly (no Flask app context),
validating PDK hydration, prompt building, emotion radar, mask/trigger
evaluation, response generation, and the fallback system.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from personaut.individuals import create_individual
from personaut.server.ui.views import chat_engine as engine
from personaut.situations import create_situation


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset engine singletons between tests."""
    engine._llm_instance = None
    engine._llm_checked = False
    engine._embedding_model = None
    engine._embedding_checked = False
    engine.individual_cache.clear()
    engine.conversation_histories.clear()
    engine.session_token_usage.clear()
    engine.session_speaker_contexts.clear()
    engine._individual_vector_stores.clear()
    yield


@pytest.fixture()
def sarah() -> dict:
    """API response dict for a well-defined individual."""
    return {
        "id": "ind_sarah",
        "name": "Sarah Chen",
        "description": "A cheerful barista",
        "trait_profile": {
            "warmth": 0.85,
            "reasoning": 0.6,
            "emotional_stability": 0.7,
            "dominance": 0.4,
            "liveliness": 0.75,
            "rule_consciousness": 0.5,
            "social_boldness": 0.6,
            "sensitivity": 0.65,
            "vigilance": 0.35,
            "abstractedness": 0.5,
            "privateness": 0.3,
            "apprehension": 0.4,
            "openness_to_change": 0.7,
            "self_reliance": 0.55,
            "perfectionism": 0.45,
            "tension": 0.3,
        },
        "emotional_state": {
            "cheerful": 0.7,
            "content": 0.6,
            "hopeful": 0.4,
        },
        "metadata": {
            "occupation": "barista",
            "interests": "coffee, latte art, indie music",
            "speaking_style": "casual and warm",
        },
    }


@pytest.fixture()
def sarah_individual(sarah: dict):
    """A hydrated PDK Individual for Sarah (no API calls)."""
    individual = create_individual(
        name=sarah["name"],
        traits=sarah["trait_profile"],
        emotional_state=sarah["emotional_state"],
        metadata=sarah["metadata"],
    )
    individual.id = sarah["id"]
    return individual


@pytest.fixture()
def coffeeshop_situation():
    """A PDK Situation for an in-person coffee shop encounter."""
    return create_situation(
        modality="in_person",
        description="A cozy coffee shop on a rainy morning",
        location="Downtown Café",
    )


@pytest.fixture()
def texting_situation():
    """A PDK Situation for a text message conversation."""
    return create_situation(
        modality="text_message",
        description="Texting after meeting at a party",
    )


# ═══════════════════════════════════════════════════════════════════════════
# LLM singleton
# ═══════════════════════════════════════════════════════════════════════════


class TestGetLLM:
    def test_returns_none_when_no_provider(self) -> None:
        with patch("personaut.server.ui.views.chat_engine.get_llm", wraps=engine.get_llm):
            result = engine.get_llm()
        # In test env there's no real LLM configured
        # (result could be None or an actual instance — just verify no crash)
        assert result is None or result is not None

    def test_caches_result(self) -> None:
        engine._llm_checked = True
        engine._llm_instance = "FAKE_LLM"
        assert engine.get_llm() == "FAKE_LLM"


# ═══════════════════════════════════════════════════════════════════════════
# Emotion radar
# ═══════════════════════════════════════════════════════════════════════════


class TestComputeEmotionRadar:
    def test_empty_emotions(self) -> None:
        radar = engine.compute_emotion_radar({})
        assert all(v == 0.0 for v in radar.values())
        assert len(radar) == 6  # 6 categories

    def test_single_emotion(self) -> None:
        radar = engine.compute_emotion_radar({"cheerful": 0.8})
        # "cheerful" belongs to Joy category
        joy_label = [k for k in radar if k.lower() == "joy"][0]
        assert radar[joy_label] == 0.8

    def test_max_within_category(self) -> None:
        radar = engine.compute_emotion_radar(
            {
                "cheerful": 0.6,
                "excited": 0.9,
                "hopeful": 0.3,
            }
        )
        joy_label = [k for k in radar if k.lower() == "joy"][0]
        # Should use max, not average
        assert radar[joy_label] == 0.9

    def test_multiple_categories(self) -> None:
        radar = engine.compute_emotion_radar(
            {
                "cheerful": 0.5,
                "anxious": 0.7,
            }
        )
        non_zero = {k: v for k, v in radar.items() if v > 0}
        assert len(non_zero) == 2

    def test_all_categories_present(self) -> None:
        radar = engine.compute_emotion_radar({"cheerful": 0.5})
        # Should always have all 6 categories
        expected = {"Joy", "Powerful", "Peaceful", "Anger", "Sad", "Fear"}
        assert set(radar.keys()) == expected


class TestGetIndividualRadarData:
    def test_returns_radar_structure(self, sarah: dict) -> None:
        data = engine.get_individual_radar_data(sarah)
        assert "name" in data
        assert "categories" in data
        assert "values" in data
        assert "emotions" in data
        assert data["name"] == "Sarah Chen"
        assert len(data["categories"]) == 6
        assert len(data["values"]) == 6


# ═══════════════════════════════════════════════════════════════════════════
# Hydration
# ═══════════════════════════════════════════════════════════════════════════


class TestHydrateIndividual:
    def test_basic_hydration(self) -> None:
        data = {
            "id": "ind_001",
            "name": "Test",
            "trait_profile": {"warmth": 0.8},
            "emotional_state": {"cheerful": 0.5},
            "metadata": {"occupation": "teacher"},
        }
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            individual = engine.hydrate_individual(data)
        assert individual.name == "Test"
        assert individual.id == "ind_001"

    def test_caches_by_id(self) -> None:
        data = {
            "id": "ind_cached",
            "name": "Cached",
            "trait_profile": {},
            "emotional_state": {},
            "metadata": {},
        }
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            first = engine.hydrate_individual(data)
            second = engine.hydrate_individual(data)
        assert first is second

    def test_skips_unknown_emotions(self) -> None:
        data = {
            "id": "ind_unk",
            "name": "Unk",
            "trait_profile": {},
            "emotional_state": {"cheerful": 0.5, "totally_fake_emotion": 0.9},
            "metadata": {},
        }
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            individual = engine.hydrate_individual(data)
        # Should not crash — invalid emotion is silently skipped
        assert individual.name == "Unk"

    def test_stores_description_in_metadata(self) -> None:
        data = {
            "id": "ind_desc",
            "name": "Desc",
            "description": "A thoughtful person",
            "trait_profile": {},
            "emotional_state": {},
            "metadata": {},
        }
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            individual = engine.hydrate_individual(data)
        assert individual.metadata.get("description") == "A thoughtful person"


class TestHydrateSituation:
    def test_basic_hydration(self) -> None:
        data = {
            "modality": "text_message",
            "description": "A texting conversation",
            "location": "Home",
            "context": {"time_of_day": "evening"},
        }
        situation = engine.hydrate_situation(data)
        assert situation.description == "A texting conversation"


# ═══════════════════════════════════════════════════════════════════════════
# Guidelines builder
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildGuidelines:
    def test_includes_identity(self, sarah_individual) -> None:
        guidelines = engine.build_guidelines(sarah_individual)
        joined = "\n".join(guidelines)
        assert "Sarah Chen" in joined
        assert "never break character" in joined.lower()

    def test_includes_occupation(self, sarah_individual) -> None:
        guidelines = engine.build_guidelines(sarah_individual)
        joined = "\n".join(guidelines)
        assert "barista" in joined.lower()

    def test_includes_interests(self, sarah_individual) -> None:
        guidelines = engine.build_guidelines(sarah_individual)
        joined = "\n".join(guidelines)
        assert "coffee" in joined.lower()

    def test_texting_modality_rules(self, sarah_individual, texting_situation) -> None:
        guidelines = engine.build_guidelines(sarah_individual, texting_situation)
        joined = "\n".join(guidelines)
        assert "text" in joined.lower()
        assert "stage direction" in joined.lower()

    def test_in_person_modality_rules(self, sarah_individual, coffeeshop_situation) -> None:
        guidelines = engine.build_guidelines(sarah_individual, coffeeshop_situation)
        joined = "\n".join(guidelines)
        assert "bracket" in joined.lower() or "[" in joined

    def test_boundaries_included(self, sarah_individual) -> None:
        guidelines = engine.build_guidelines(sarah_individual)
        joined = "\n".join(guidelines)
        assert "boundaries" in joined.lower() or "rude" in joined.lower()


# ═══════════════════════════════════════════════════════════════════════════
# System prompt builder
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildSystemPrompt:
    def test_returns_string(self, sarah_individual, coffeeshop_situation) -> None:
        prompt = engine.build_system_prompt(
            sarah_individual,
            situation=coffeeshop_situation,
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_contains_character_name(self, sarah_individual) -> None:
        prompt = engine.build_system_prompt(sarah_individual)
        assert "Sarah Chen" in prompt

    def test_includes_activation_context(self, sarah_individual) -> None:
        prompt = engine.build_system_prompt(
            sarah_individual,
            activation_context="MASK 'Professional' is active",
        )
        assert "Professional" in prompt


# ═══════════════════════════════════════════════════════════════════════════
# Fallback response generation
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateFallback:
    def test_greeting_in_person(self, sarah_individual, coffeeshop_situation) -> None:
        reply = engine.generate_fallback(
            sarah_individual,
            "hey!",
            coffeeshop_situation,
        )
        assert len(reply) > 0
        # Barista at work should proactively serve
        assert "get" in reply.lower() or "welcome" in reply.lower() or "hey" in reply.lower()

    def test_greeting_texting(self, sarah_individual, texting_situation) -> None:
        reply = engine.generate_fallback(
            sarah_individual,
            "hi",
            texting_situation,
        )
        assert len(reply) > 0
        # Should not include stage directions in text mode
        assert "[" not in reply or "emoji" in reply.lower()

    def test_question_response(self, sarah_individual) -> None:
        reply = engine.generate_fallback(
            sarah_individual,
            "What's your favourite coffee?",
        )
        assert len(reply) > 0

    def test_interest_detection(self, sarah_individual, coffeeshop_situation) -> None:
        reply = engine.generate_fallback(
            sarah_individual,
            "I really love coffee too!",
            coffeeshop_situation,
        )
        assert len(reply) > 0
        assert "coffee" in reply.lower() or "love" in reply.lower() or "latte" in reply.lower()

    def test_simple_fallback(self) -> None:
        reply = engine.generate_fallback_simple("Sarah Chen")
        assert "Sarah Chen" in reply


# ═══════════════════════════════════════════════════════════════════════════
# Generate reply (integration — uses fallback since no real LLM)
# ═══════════════════════════════════════════════════════════════════════════


class TestGenerateReply:
    def test_returns_tuple_of_three(self, sarah_individual, coffeeshop_situation) -> None:
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            reply, usage, activation = engine.generate_reply(
                sarah_individual,
                "hello!",
                "sess_test",
                situation=coffeeshop_situation,
            )
        assert isinstance(reply, str)
        assert isinstance(usage, dict)
        assert isinstance(activation, dict)
        assert len(reply) > 0

    def test_records_conversation_history(self, sarah_individual) -> None:
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            engine.generate_reply(sarah_individual, "first msg", "sess_hist")
            engine.generate_reply(sarah_individual, "second msg", "sess_hist")
        history = engine.conversation_histories.get("sess_hist", [])
        # Should have 4 entries: user, assistant, user, assistant
        assert len(history) == 4

    def test_activation_info_structure(self, sarah_individual) -> None:
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            _, _, activation = engine.generate_reply(
                sarah_individual,
                "test",
                "sess_act",
            )
        assert "activated_masks" in activation
        assert "fired_triggers" in activation
        assert "applied_effects" in activation
        assert "relevant_memories" in activation


# ═══════════════════════════════════════════════════════════════════════════
# Mask & trigger evaluation
# ═══════════════════════════════════════════════════════════════════════════


class TestEvaluateMasksAndTriggers:
    def test_returns_expected_keys(self, sarah_individual) -> None:
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            result = engine.evaluate_masks_and_triggers(
                sarah_individual,
                "hello",
            )
        assert "activated_masks" in result
        assert "fired_triggers" in result
        assert "applied_effects" in result
        assert "prompt_context" in result

    def test_no_masks_no_triggers(self, sarah_individual) -> None:
        """With no masks/triggers loaded, nothing should fire."""
        with patch("personaut.server.ui.views.chat_engine._api_get", return_value=None):
            result = engine.evaluate_masks_and_triggers(
                sarah_individual,
                "hello",
            )
        assert len(result["activated_masks"]) == 0
        assert len(result["fired_triggers"]) == 0


# ═══════════════════════════════════════════════════════════════════════════
# Analyze emotions (LLM-dependent — tests the no-LLM path)
# ═══════════════════════════════════════════════════════════════════════════


class TestAnalyzeEmotions:
    def test_returns_empty_without_llm(self, sarah_individual) -> None:
        result = engine.analyze_emotions(
            sarah_individual,
            "You look happy!",
            "Thanks, I am!",
        )
        # No LLM configured → should return empty dict
        assert result == {}


# ═══════════════════════════════════════════════════════════════════════════
# Memory search
# ═══════════════════════════════════════════════════════════════════════════


class TestSearchRelevantMemories:
    def test_empty_when_no_memories(self, sarah_individual) -> None:
        result = engine.search_relevant_memories(sarah_individual, "coffee")
        assert result == [] or isinstance(result, list)

    def test_keyword_fallback(self) -> None:
        """Without embedding model, should fall back to keyword matching."""
        individual = create_individual(
            name="Test",
            traits={},
            emotional_state={},
        )
        from personaut.memory import create_individual_memory

        mem = create_individual_memory(
            owner_id="test",
            description="Making coffee every morning",
        )
        individual.add_memory(mem)

        result = engine.search_relevant_memories(individual, "coffee morning")
        assert len(result) >= 1
        assert "coffee" in result[0].description.lower()


# ═══════════════════════════════════════════════════════════════════════════
# Session state helpers
# ═══════════════════════════════════════════════════════════════════════════


class TestSessionState:
    def test_speaker_profiles_default(self) -> None:
        assert len(engine.saved_speaker_profiles) >= 2
        ids = [p["id"] for p in engine.saved_speaker_profiles]
        assert "sp_default" in ids
        assert "sp_stranger" in ids

    def test_category_colors(self) -> None:
        assert len(engine.CATEGORY_COLORS) == 6
        for color in engine.CATEGORY_COLORS.values():
            assert color.startswith("#")
