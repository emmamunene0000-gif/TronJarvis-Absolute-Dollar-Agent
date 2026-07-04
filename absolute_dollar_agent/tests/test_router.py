"""
Unit tests for the Signal Router — classification (§7) and routing (§8).
"""
from mind.router import (
    TIER_CONTEXT,
    TIER_EXECUTE,
    classify,
    route,
    suppressed_by_higher_priority_flip,
)


class TestClassification:
    def test_all_18_signals_classify_execute_or_context(self):
        all_signals = [
            "CALL_ENTRY", "PUT_ENTRY", "CALL_CONTINUATION", "PUT_CONTINUATION",
            "H4_FLIP_CALL", "H4_FLIP_PUT", "MTF_FLIP_CALL", "MTF_FLIP_PUT",
            "TRAIL_FLIP_CALL", "TRAIL_FLIP_PUT", "SNIPER_CALL", "SNIPER_PUT",
            "CALL_ZONE_BREAK", "PUT_ZONE_BREAK", "BULL_REGIME_SHIFT",
            "BEAR_REGIME_SHIFT", "BULL_BOS", "BEAR_BOS",
        ]
        assert len(all_signals) == 18
        for sig in all_signals:
            assert classify(sig) in (TIER_EXECUTE, TIER_CONTEXT)

    def test_sniper_is_context_per_locked_spec(self):
        # The prior flat-layout build classified this EXECUTE — §7 of this
        # spec locks it CONTEXT, dormant unless show_zones is on.
        assert classify("SNIPER_CALL") == TIER_CONTEXT
        assert classify("SNIPER_PUT") == TIER_CONTEXT

    def test_bos_is_context_per_locked_spec(self):
        # The prior flat-layout build classified this NOISE — §7 locks it
        # CONTEXT ("confidence modifier only").
        assert classify("BULL_BOS") == TIER_CONTEXT
        assert classify("BEAR_BOS") == TIER_CONTEXT

    def test_flips_and_entries_are_execute(self):
        for sig in ("CALL_ENTRY", "PUT_ENTRY", "H4_FLIP_CALL", "MTF_FLIP_PUT", "TRAIL_FLIP_CALL"):
            assert classify(sig) == TIER_EXECUTE


class TestRouting:
    def test_continuation_routes_rise_fall_only(self):
        decision = route("CALL_CONTINUATION", {"vanilla", "multiplier", "rise_fall"},
                          ["vanilla", "multiplier", "rise_fall"])
        assert decision.auto_style == "rise_fall"

    def test_dual_fit_uses_fixed_priority(self):
        decision = route("H4_FLIP_CALL", {"vanilla", "multiplier"},
                          ["vanilla", "multiplier", "rise_fall"])
        assert decision.auto_style == "vanilla"

    def test_drops_to_tap_when_best_fit_style_disabled(self):
        decision = route("CALL_CONTINUATION", {"vanilla"}, ["vanilla", "multiplier", "rise_fall"])
        assert decision.auto_style is None

    def test_entry_prefers_vanilla_but_rise_fall_stays_tap_available(self):
        # Vanilla wins the style_priority tie-break when all three are enabled...
        decision = route("CALL_ENTRY", {"vanilla", "multiplier", "rise_fall"},
                          ["vanilla", "multiplier", "rise_fall"])
        assert decision.auto_style == "vanilla"
        assert "rise_fall" in decision.tap_styles

    def test_entry_auto_routes_to_rise_fall_when_its_the_only_enabled_style(self):
        # ...but per operator decision (2026-07-04), Rise/Fall is a first-class
        # auto-route target for entries too, not tap-only — confirmed by
        # falling through to it when Vanilla/Multiplier are both disabled.
        decision = route("CALL_ENTRY", {"rise_fall"}, ["vanilla", "multiplier", "rise_fall"])
        assert decision.auto_style == "rise_fall"

    def test_zone_break_has_no_style_fit(self):
        # Locked per operator: zone breaks stay CONTEXT permanently, never routed.
        decision = route("CALL_ZONE_BREAK", {"vanilla", "multiplier", "rise_fall"},
                          ["vanilla", "multiplier", "rise_fall"])
        assert decision.auto_style is None
        assert decision.tap_styles == []


class TestSameBarSuppression:
    def test_mtf_suppressed_when_h4_fired_same_bar(self):
        assert suppressed_by_higher_priority_flip("MTF_FLIP_CALL", ["H4_FLIP_CALL"]) is True

    def test_trail_suppressed_when_mtf_fired_same_bar(self):
        assert suppressed_by_higher_priority_flip("TRAIL_FLIP_PUT", ["MTF_FLIP_PUT"]) is True

    def test_h4_never_suppressed(self):
        assert suppressed_by_higher_priority_flip("H4_FLIP_CALL", ["MTF_FLIP_CALL", "TRAIL_FLIP_CALL"]) is False

    def test_no_suppression_without_overlap(self):
        assert suppressed_by_higher_priority_flip("TRAIL_FLIP_CALL", ["CALL_ENTRY"]) is False
