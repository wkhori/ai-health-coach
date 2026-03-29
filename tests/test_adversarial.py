"""Adversarial tests — parametrized tests that run adversarial prompts through safety.

Tests validate:
- All crisis prompts are detected (0% false negatives)
- All clinical prompts are detected by Tier 1 where applicable
- All injection prompts are flagged by the sanitizer
- Safe prompts pass (test against false positives)
- 20+ tests required
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models.enums import SafetyAction, SafetyClassificationType
from src.safety.classifier import decide_action
from src.safety.rules import tier1_classify
from src.safety.sanitizer import detect_injection_patterns, sanitize_input

# ---------------------------------------------------------------------------
# Load adversarial prompts
# ---------------------------------------------------------------------------
_PROMPTS_PATH = Path(__file__).parent / "adversarial_prompts.json"


def _load_prompts() -> dict[str, list[str]]:
    with open(_PROMPTS_PATH) as f:
        return json.load(f)


_ALL_PROMPTS = _load_prompts()


# ---------------------------------------------------------------------------
# Crisis prompts — 0% false negative required
# ---------------------------------------------------------------------------
class TestCrisisPrompts:
    """Every crisis prompt MUST be detected by Tier 1 rules."""

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["crisis"])
    def test_crisis_detected_by_tier1(self, prompt: str):
        """Crisis prompts must be caught by Tier 1 rule-based filter."""
        result = tier1_classify(prompt)
        assert result is not None, f"Crisis prompt not detected: {prompt!r}"
        assert result.classification == SafetyClassificationType.CRISIS, (
            f"Expected CRISIS, got {result.classification} for: {prompt!r}"
        )

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["crisis"])
    def test_crisis_action_is_blocked(self, prompt: str):
        """Crisis classification must result in BLOCKED action."""
        result = tier1_classify(prompt)
        assert result is not None
        action = decide_action(result)
        assert action == SafetyAction.BLOCKED, f"Expected BLOCKED, got {action} for: {prompt!r}"

    def test_crisis_zero_false_negatives(self):
        """Meta-test: verify 0% false negative rate across all crisis prompts."""
        missed = []
        for prompt in _ALL_PROMPTS["crisis"]:
            result = tier1_classify(prompt)
            if result is None or result.classification != SafetyClassificationType.CRISIS:
                missed.append(prompt)

        assert len(missed) == 0, (
            f"Crisis FN rate: {len(missed)}/{len(_ALL_PROMPTS['crisis'])}. Missed: {missed}"
        )


# ---------------------------------------------------------------------------
# Clinical prompts — test those that contain dosage/diagnostic patterns
# ---------------------------------------------------------------------------
class TestClinicalPrompts:
    """Clinical prompts with dosage patterns must be caught by Tier 1."""

    @pytest.mark.parametrize(
        "prompt",
        _ALL_PROMPTS["medication"],
    )
    def test_medication_dosage_detected(self, prompt: str):
        """Medication prompts with dosage patterns caught by Tier 1.

        All medication prompts in the bank contain numeric dosage patterns
        (e.g., '500 mg', '2 tablets') which Tier 1 rules detect.
        """
        result = tier1_classify(prompt)
        assert result is not None, f"Dosage prompt not detected by Tier 1: {prompt!r}"
        assert result.classification == SafetyClassificationType.CLINICAL

    @pytest.mark.parametrize(
        "prompt",
        _ALL_PROMPTS["medication"],
    )
    def test_medication_action_rewrite_or_block(self, prompt: str):
        """Clinical medication prompts must result in REWRITTEN or BLOCKED."""
        result = tier1_classify(prompt)
        assert result is not None
        action = decide_action(result)
        assert action in (SafetyAction.REWRITTEN, SafetyAction.BLOCKED), (
            f"Expected REWRITTEN or BLOCKED, got {action} for: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# Injection prompts — sanitizer must flag all
# ---------------------------------------------------------------------------
class TestInjectionPrompts:
    """All injection prompts must be flagged by the sanitizer."""

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["injection"])
    def test_injection_detected(self, prompt: str):
        """Every injection prompt must trigger at least one pattern match."""
        patterns = detect_injection_patterns(prompt)
        assert len(patterns) > 0, f"Injection not detected: {prompt!r}"

    def test_injection_zero_false_negatives(self):
        """Meta-test: verify 0% false negative rate across all injection prompts."""
        missed = []
        for prompt in _ALL_PROMPTS["injection"]:
            if len(detect_injection_patterns(prompt)) == 0:
                missed.append(prompt)

        assert len(missed) == 0, (
            f"Injection FN rate: {len(missed)}/{len(_ALL_PROMPTS['injection'])}. Missed: {missed}"
        )


# ---------------------------------------------------------------------------
# Safe prompts — test false positive rate
# ---------------------------------------------------------------------------
class TestSafePrompts:
    """Safe prompts must NOT be classified as crisis or clinical by Tier 1."""

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["safe_prompts"])
    def test_safe_prompt_not_crisis(self, prompt: str):
        """Safe prompts must not be classified as crisis."""
        result = tier1_classify(prompt)
        if result is not None:
            assert result.classification != SafetyClassificationType.CRISIS, (
                f"False positive CRISIS for safe prompt: {prompt!r}"
            )

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["safe_prompts"])
    def test_safe_prompt_not_clinical(self, prompt: str):
        """Safe prompts must not be classified as clinical."""
        result = tier1_classify(prompt)
        if result is not None:
            assert result.classification != SafetyClassificationType.CLINICAL, (
                f"False positive CLINICAL for safe prompt: {prompt!r}"
            )

    def test_safe_prompt_false_positive_rate_below_10pct(self):
        """Meta-test: false positive rate must be below 10%."""
        false_positives = []
        for prompt in _ALL_PROMPTS["safe_prompts"]:
            result = tier1_classify(prompt)
            if result is not None and result.classification in (
                SafetyClassificationType.CRISIS,
                SafetyClassificationType.CLINICAL,
            ):
                false_positives.append(prompt)

        fp_rate = len(false_positives) / len(_ALL_PROMPTS["safe_prompts"])
        assert fp_rate < 0.10, (
            f"FP rate {fp_rate:.1%} exceeds 10%. False positives: {false_positives}"
        )

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["safe_prompts"])
    def test_safe_prompt_no_injection(self, prompt: str):
        """Safe prompts should not trigger injection detection."""
        patterns = detect_injection_patterns(prompt)
        assert len(patterns) == 0, (
            f"False injection detection for: {prompt!r}. Patterns: {patterns}"
        )


# ---------------------------------------------------------------------------
# Edge case prompts — sanitizer robustness
# ---------------------------------------------------------------------------
class TestEdgeCasePrompts:
    """Edge case prompts should not crash the system."""

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["edge_cases"])
    def test_edge_case_sanitize_no_crash(self, prompt: str):
        """Sanitizer must handle all edge case inputs without crashing."""
        result = sanitize_input(prompt)
        assert isinstance(result, str)

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["edge_cases"])
    def test_edge_case_tier1_no_crash(self, prompt: str):
        """Tier 1 classifier must handle edge cases without crashing."""
        result = tier1_classify(prompt)
        assert result is None or hasattr(result, "classification")

    @pytest.mark.parametrize("prompt", _ALL_PROMPTS["edge_cases"])
    def test_edge_case_injection_no_crash(self, prompt: str):
        """Injection detector must handle edge cases without crashing."""
        result = detect_injection_patterns(prompt)
        assert isinstance(result, list)

    def test_zero_width_chars_stripped(self):
        """Zero-width characters from edge cases are properly stripped."""
        zwc_prompt = "\u200b\u200c\u200d\u2060\ufeff"
        result = sanitize_input(zwc_prompt)
        assert result == ""

    def test_control_chars_stripped(self):
        """Control characters from edge cases are properly stripped."""
        ctrl_prompt = "\x00\x01\x02\x03\x04"
        result = sanitize_input(ctrl_prompt)
        assert result == ""
