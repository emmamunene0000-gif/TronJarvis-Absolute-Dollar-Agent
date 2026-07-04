"""
Telegram Bot — The Body
Signal feed, execution control, live status — all reading real Governor
and Memory state. No hardcoded "PAPER TRADING" placeholders (§18: no paper
mode, anywhere).
"""
import logging
from typing import Any, Callable, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

log = logging.getLogger("tradersmind.telegram")

STYLE_LABELS = {"vanilla": "VANILLA", "multiplier": "MULTIPLIER", "rise_fall": "RISE/FALL"}


class TradersMindBot:
    """Telegram interface for TradersMind. Receives signals, shows cards,
    handles tap-to-execute. Reads live Governor/Memory state — it doesn't
    hold its own copy of the truth."""

    def __init__(self, token: str, chat_id: str, governor, memory, demo_trades_required: int = 100):
        self.token = token
        self.chat_id = chat_id
        self.governor = governor
        self.memory = memory
        self.demo_trades_required = demo_trades_required
        self.app: Optional[Application] = None
        # episode_id -> raw signal dict, kept only long enough to render buttons
        self.pending_signals: dict[int, dict[str, Any]] = {}
        self.on_execute_callback: Optional[Callable] = None
        self.on_why_callback: Optional[Callable] = None
        self.on_history_callback: Optional[Callable] = None

    def set_callbacks(self, on_execute, on_why, on_history):
        self.on_execute_callback = on_execute
        self.on_why_callback = on_why
        self.on_history_callback = on_history

    async def start(self):
        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("risk", self.cmd_risk))
        self.app.add_handler(CommandHandler("history", self.cmd_history))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        log.info("Telegram polling started")

    async def stop(self):
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

    # --- Commands (real state, not placeholders) ---

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "TradersMind activated.\n"
            "TRON detects. I classify, narrate, size, and (if you tap) execute.\n\n"
            "Commands: /status /risk /history"
        )

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        status = self.governor.get_status()
        await update.message.reply_text(
            f"SESSION STATUS\n"
            f"Daily P&L: ${status['daily_pnl']:.2f}\n"
            f"Trades today: {status['daily_trades']}\n"
            f"Win rate: {status['win_rate']}%\n"
            f"Risk state: {status['state']}\n"
            f"Heat: {status['heat_level']}"
        )

    async def cmd_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        p = self.governor.profile
        status = self.governor.get_status()
        demo_trades = await self.memory.count_completed_trades(env="demo")
        await update.message.reply_text(
            f"RISK GOVERNOR\n"
            f"Sizing band: ${p.min_stake:.2f}–${p.max_dynamic_stake:.2f} "
            f"(hard ceiling ${p.max_stake:.2f})\n"
            f"Daily loss limit: ${p.daily_loss_limit:.2f}\n"
            f"Max consecutive losses: {p.max_consecutive_losses}\n"
            f"Cooldown: {p.cooldown_minutes} min after 2 losses\n"
            f"Auto-execute gate: confidence>={p.min_confidence_for_auto}% "
            f"and sync={p.min_sync_layers_for_auto}/4\n\n"
            f"Cooldown active: {status['cooldown_active']}\n"
            f"State: {status['state']}\n\n"
            f"Live-mode gate: {demo_trades}/{self.demo_trades_required} "
            f"completed demo trades"
        )

    async def cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        trades = await self.memory.get_recent_trades(limit=10)
        if not trades:
            await update.message.reply_text("No executed trades yet.")
            return
        lines = ["LAST TRADES"]
        for t in trades:
            lines.append(
                f"{t['signal_type']} {t['bias']} | stake ${t['stake']:.2f} | "
                f"{t['result_status']} | env={t['env']}"
            )
        await update.message.reply_text("\n".join(lines))

    # --- Signal cards ---

    def _keyboard(self, episode_id: int, styles: list[str], stake: float) -> InlineKeyboardMarkup:
        rows = [[InlineKeyboardButton(
            f"⚡ {STYLE_LABELS.get(s, s.upper())} ${stake:.2f}",
            callback_data=f"t|{episode_id}|{s}|{stake}"
        )] for s in styles]
        rows.append([
            InlineKeyboardButton("\U0001f9e0 WHY?", callback_data=f"w|{episode_id}"),
            InlineKeyboardButton("✕", callback_data=f"d|{episode_id}"),
        ])
        return InlineKeyboardMarkup(rows)

    async def send_signal_card(self, signal: dict, narrative: str, episode_id: int,
                               tap_styles: list[str], stake: float):
        """EXECUTE-tier signal, tap-eligible. Buttons only appear here —
        CONTEXT signals never get an execute button (doctrine §2.1/§7)."""
        self.pending_signals[episode_id] = signal
        conf = signal.get("confidence", 0)
        sync = signal.get("fractal", {}).get("sync_layers", 0)
        quality = signal.get("fractal", {}).get("quality", "MIXED")
        setup = signal.get("setup", {})

        text = (
            f"{signal.get('signal', 'SIGNAL')} | {signal.get('bias', '')}\n"
            f"{signal.get('symbol', '')} @ {signal.get('spot', 0)} | tf {signal.get('tf', '')}\n"
            f"Confidence {conf}% | Fractal {sync}/4 ({quality})\n"
            f"Strike {setup.get('strike', '—')} | Expiry {setup.get('expiry_min', '—')}m | "
            f"RR 1:{setup.get('rr', '—')}\n\n"
            f"{narrative}"
        )
        if not self.app:
            return
        await self.app.bot.send_message(
            chat_id=self.chat_id, text=text,
            reply_markup=self._keyboard(episode_id, tap_styles or ["vanilla"], stake)
        )

    async def send_context_card(self, signal: dict, narrative: str):
        """CONTEXT-tier signal — informational only, no buttons, no execute path."""
        if not self.app:
            return
        text = (
            f"[CONTEXT] {signal.get('signal', 'SIGNAL')} | {signal.get('symbol', '')}\n"
            f"{narrative}\nNo action required."
        )
        await self.app.bot.send_message(chat_id=self.chat_id, text=text)

    async def send_execution_alert(self, ticket: dict, signal_type: str, stake: float):
        env_tag = "DEMO" if ticket.get("env") == "demo" else "LIVE"
        await self.app.bot.send_message(
            chat_id=self.chat_id,
            text=(
                f"EXECUTED — {env_tag}\n"
                f"{signal_type}\n"
                f"Contract: #{ticket.get('contract_id', 'N/A')}\n"
                f"Stake: ${stake:.2f}  Buy price: {ticket.get('buy_price')}\n"
            )
        )

    async def send_risk_alert(self, alert_type: str, message: str):
        if not self.app:
            return
        await self.app.bot.send_message(
            chat_id=self.chat_id, text=f"RISK ALERT: {alert_type}\n{message}"
        )

    # --- Callback handling ---

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        parts = query.data.split("|")
        kind = parts[0]

        if kind == "d":
            await query.edit_message_reply_markup(reply_markup=None)
            return

        if kind == "w":
            episode_id = int(parts[1])
            signal = self.pending_signals.get(episode_id)
            if signal and self.on_why_callback:
                explanation = await self.on_why_callback(episode_id, signal)
                await query.message.reply_text(explanation)
            return

        if kind == "t":
            episode_id, style, stake = int(parts[1]), parts[2], float(parts[3])
            await query.edit_message_reply_markup(reply_markup=None)
            if self.on_execute_callback:
                result = await self.on_execute_callback(episode_id, style, stake)
                await query.message.reply_text(f"Tap execute: {result}")
            self.pending_signals.pop(episode_id, None)
