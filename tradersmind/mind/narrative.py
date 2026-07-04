"""
Logic Trace Engine — Template-Based Narrative Generator
Zero LLM. Zero hallucination. Deterministic storytelling.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
import yaml
import os

@dataclass
class NarrativeResult:
    headline: str
    story: str
    confidence_breakdown: str
    recommendation: str
    risk_note: str

class LogicTrace:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.templates = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                cfg = yaml.safe_load(f)
                self.templates = cfg.get("narrative", {}).get("templates", {})

    def generate(self, signal: Dict[str, Any], 
                 similar_stats: Optional[Dict[str, Any]] = None) -> NarrativeResult:
        """
        Convert TRON JSON into a human-readable narrative.
        """
        sig_type = signal.get("signal", "UNKNOWN")
        bias = signal.get("bias", "CALL")
        conf = signal.get("confidence", 0)
        sync = signal.get("fractal", {}).get("sync_layers", 0)
        quality = signal.get("fractal", {}).get("quality", "MIXED")
        strike = signal.get("setup", {}).get("strike", 0)
        strike_mode = signal.get("setup", {}).get("strike_mode", "ATM")
        expiry = signal.get("setup", {}).get("expiry_min", 0)
        rr = signal.get("setup", {}).get("rr", 0)
        iv = signal.get("setup", {}).get("iv_proxy", 0)
        delta = signal.get("setup", {}).get("delta", 0.5)
        regime_str = signal.get("setup", {}).get("regime_strength", 0)

        # Historical context injection
        win_rate_note = ""
        if similar_stats and similar_stats.get("total", 0) > 0:
            wr = similar_stats["win_rate"]
            streak = similar_stats.get("streak", 0)
            win_rate_note = f" Similar setups won {wr}% historically."
            if streak <= -2:
                win_rate_note += f" CAUTION: Current streak is {streak} losses."
            elif streak >= 3:
                win_rate_note += f" HOT: Current streak is +{streak} wins."

        # Template selection
        template_key = sig_type.lower()
        template = self.templates.get(template_key, 
            "{bias} signal detected. Confidence {confidence}%. Sync {sync_layers}/4.")

        headline = template.format(
            bias=bias,
            sync_layers=sync,
            confidence=conf,
            strike=strike,
            strike_mode=strike_mode,
            expiry=expiry,
            win_rate=similar_stats["win_rate"] if similar_stats else 0
        )

        # Build the story
        story_parts = [
            f"Signal: {sig_type}",
            f"Market: {signal.get('symbol', 'UNKNOWN')} @ {signal.get('spot', 0)}",
            f"Fractal Alignment: {sync}/4 layers ({quality})",
            f"Structure: {signal.get('core', {}).get('structure', 'NEUT')}",
            f"VWAP Regime: {signal.get('core', {}).get('vwap', 'NEUT')}",
            f"Fib Trend: {signal.get('core', {}).get('fib', 'NEUT')}",
            f"Volume Position: {signal.get('core', {}).get('vp', '—')}",
            f"RSI: {signal.get('core', {}).get('rsi', 50)}",
            f"Spatial Quality: {signal.get('core', {}).get('spatial', 'OPEN_SPACE')}",
        ]
        story = " | ".join(story_parts)

        # Confidence breakdown
        conf_parts = []
        if signal.get("fractal", {}).get("h4") == bias:
            conf_parts.append("H4 aligned")
        if signal.get("fractal", {}).get("h1") == bias:
            conf_parts.append("H1 aligned")
        if signal.get("fractal", {}).get("m15") == bias:
            conf_parts.append("M15 aligned")
        if signal.get("core", {}).get("vwap") == bias:
            conf_parts.append("VWAP confirms")
        if signal.get("core", {}).get("fib") == bias:
            conf_parts.append("Fib confirms")

        conf_breakdown = f"Confidence {conf}% because: {', '.join(conf_parts)}." if conf_parts else f"Confidence {conf}%."

        # Recommendation
        if conf >= 85 and sync >= 3 and quality in ["ALIGNED", "SOVEREIGN"]:
            recommendation = "HIGH CONVICTION — Risk Governor approves max stake."
        elif conf >= 60 and sync >= 2:
            recommendation = "MODERATE CONVICTION — Standard stake approved."
        else:
            recommendation = "LOW CONVICTION — Reduce stake or wait for better alignment."

        # Risk note
        risk_parts = [f"RR {rr}:1", f"IV Proxy {iv:.1f}%", f"Delta {delta:.2f}"]
        if regime_str > 50:
            risk_parts.append(f"Strong regime ({regime_str}%)")
        risk_note = " | ".join(risk_parts)

        return NarrativeResult(
            headline=headline + win_rate_note,
            story=story,
            confidence_breakdown=conf_breakdown,
            recommendation=recommendation,
            risk_note=risk_note
        )

    def explain_rejection(self, reason: str) -> str:
        """Explain why a signal was rejected or held."""
        explanations = {
            "LOW_CONFIDENCE": "Confidence below threshold. TRON sees the setup but not enough layers align. Patience.",
            "HEAT_LIMIT": "Risk Governor paused trading. Heat threshold exceeded. Cooldown active.",
            "DAILY_LIMIT": "Daily loss limit reached. Trading halted for protection. Manual override required.",
            "STREAK_LIMIT": "Consecutive loss streak detected. System in protective mode.",
            "SPATIAL_FAIL": "Price not near key level. Open-space entry rejected by spatial filter.",
        }
        return explanations.get(reason, f"Signal held: {reason}")
