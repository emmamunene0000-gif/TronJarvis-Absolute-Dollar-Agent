"""
Signal Router — Classification (CLAUDE.md §7) + Routing Matrix (§8).

TradersMind never invents a signal (doctrine §2.1). This module is the only
place that decides what a TRON signal is allowed to do:
  EXECUTE  -> may place a trade if its route-style is enabled
  CONTEXT  -> narrated/logged only, never an independent trade
  NOISE    -> logged only, never spoken (unused today — the 18-signal
              whitelist in tron/models.py maps entirely onto EXECUTE/CONTEXT,
              kept here for a signal type TRON might add later)

Two locked-spec resolutions applied here, both settled against jarvis's
already-shipped classifier which disagreed with this spec:
  - SNIPER_CALL/PUT classified CONTEXT (dormant unless show_zones), not
    EXECUTE as jarvis had it.
  - BULL_BOS/BEAR_BOS classified CONTEXT ("confidence modifier only"), not
    NOISE as jarvis had it.
"""
from dataclasses import dataclass
from typing import Optional

TIER_EXECUTE = "EXECUTE"
TIER_CONTEXT = "CONTEXT"
TIER_NOISE = "NOISE"

EXECUTE_SIGNALS = {
    "CALL_ENTRY", "PUT_ENTRY",
    "CALL_CONTINUATION", "PUT_CONTINUATION",
    "H4_FLIP_CALL", "H4_FLIP_PUT",
    "MTF_FLIP_CALL", "MTF_FLIP_PUT",
    "TRAIL_FLIP_CALL", "TRAIL_FLIP_PUT",
}

CONTEXT_SIGNALS = {
    "SNIPER_CALL", "SNIPER_PUT",
    "CALL_ZONE_BREAK", "PUT_ZONE_BREAK",
    "BULL_REGIME_SHIFT", "BEAR_REGIME_SHIFT",
    "BULL_BOS", "BEAR_BOS",
}

# Same-bar suppression priority for overlapping flip tiers (§7 notes).
# Lower number = higher priority = fires; a lower-priority flip on the same
# symbol+bar is downgraded to context-only, never executed.
FLIP_PRIORITY = {
    "H4_FLIP_CALL": 1, "H4_FLIP_PUT": 1,
    "MTF_FLIP_CALL": 2, "MTF_FLIP_PUT": 2,
    "TRAIL_FLIP_CALL": 3, "TRAIL_FLIP_PUT": 3,
}

# §8 Routing Matrix — which styles a given EXECUTE signal best-fits.
STYLE_FIT = {
    "CALL_ENTRY": {"vanilla", "multiplier"},
    "PUT_ENTRY": {"vanilla", "multiplier"},
    "CALL_CONTINUATION": {"rise_fall"},
    "PUT_CONTINUATION": {"rise_fall"},
    "H4_FLIP_CALL": {"vanilla", "multiplier"},
    "H4_FLIP_PUT": {"vanilla", "multiplier"},
    "MTF_FLIP_CALL": {"vanilla", "multiplier"},
    "MTF_FLIP_PUT": {"vanilla", "multiplier"},
    "TRAIL_FLIP_CALL": {"rise_fall", "vanilla", "multiplier"},
    "TRAIL_FLIP_PUT": {"rise_fall", "vanilla", "multiplier"},
}

# Locked per operator: CALL_ENTRY/PUT_ENTRY may also be tap-executed to
# Rise/Fall as a manual override, even though it isn't in the auto-route
# fit set above (open decision #3 in §8).
TAP_ONLY_EXTRA_STYLES = {
    "CALL_ENTRY": {"rise_fall"},
    "PUT_ENTRY": {"rise_fall"},
}


def classify(signal_type: str) -> str:
    if signal_type in EXECUTE_SIGNALS:
        return TIER_EXECUTE
    if signal_type in CONTEXT_SIGNALS:
        return TIER_CONTEXT
    return TIER_NOISE


@dataclass
class RouteDecision:
    auto_style: Optional[str]   # style to auto-execute with, or None if no enabled style fits
    tap_styles: list            # every style the operator may still tap-execute to


def route(signal_type: str, enabled_styles: set[str],
          style_priority: list[str]) -> RouteDecision:
    """
    Resolve which contract style an EXECUTE-tier signal auto-routes to.

    Locked per operator (open decision #1 in §8): when a signal fits more
    than one enabled style, `style_priority` is a fixed ranked list
    (config/settings.yaml -> router.style_priority) — first enabled match
    wins. Generalizes the "fixed operator default" answer for the
    Vanilla-vs-Multiplier tie into one ranked list covering all three
    styles, since TRAIL_FLIP_* fits all three simultaneously.
    """
    best_fit = STYLE_FIT.get(signal_type, set())
    candidates = best_fit & enabled_styles

    auto_style = None
    for style in style_priority:
        if style in candidates:
            auto_style = style
            break

    tap_styles = set(best_fit) | TAP_ONLY_EXTRA_STYLES.get(signal_type, set())
    tap_styles &= enabled_styles or tap_styles  # if nothing enabled, still show every fit for manual choice

    return RouteDecision(auto_style=auto_style, tap_styles=sorted(tap_styles))


def suppressed_by_higher_priority_flip(signal_type: str,
                                        same_bar_signals: list[str]) -> bool:
    """
    §7: MTF_FLIP is suppressed if H4_FLIP fired the same bar; TRAIL_FLIP is
    suppressed if H4_FLIP or MTF_FLIP fired the same bar. `same_bar_signals`
    is every other signal type already logged for this symbol+time bucket.
    """
    my_priority = FLIP_PRIORITY.get(signal_type)
    if my_priority is None:
        return False
    for other in same_bar_signals:
        other_priority = FLIP_PRIORITY.get(other)
        if other_priority is not None and other_priority < my_priority:
            return True
    return False
