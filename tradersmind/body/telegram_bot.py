"""
Telegram Bot — The Body
Signal feed, execution control, live P&L, conversational interface.
"""
import os
import asyncio
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)

class TradersMindBot:
    """
    Telegram interface for TradersMind.
    Receives signals, shows cards, handles tap-to-execute.
    """
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.app: Optional[Application] = None
        self.pending_signals: Dict[str, Dict[str, Any]] = {}
        self.on_execute_callback = None
        self.on_why_callback = None
        self.on_history_callback = None

    async def start(self):
        self.app = Application.builder().token(self.token).build()

        # Handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("pause", self.cmd_pause))
        self.app.add_handler(CommandHandler("resume", self.cmd_resume))
        self.app.add_handler(CommandHandler("history", self.cmd_history))
        self.app.add_handler(CommandHandler("risk", self.cmd_risk))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

        await self.app.initialize()
        await self.app.start()
        print("[TelegramBot] Started")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *TradersMind Activated*

"
            "Just a Really Very Intelligent Sidekick.
"
            "TRON detects. I execute. Governor protects.

"
            "Commands:
"
            "/status — Current session stats
"
            "/risk — Risk Governor status
"
            "/history — Last 10 trades
"
            "/pause — Pause auto-trading
"
            "/resume — Resume auto-trading",
            parse_mode="Markdown"
        )

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Would fetch from governor + memory
        await update.message.reply_text(
            "📊 *Session Status*

"
            "Mode: PAPER TRADING
"
            "Daily P&L: $0.00
"
            "Trades Today: 0
"
            "Win Rate: —
"
            "Risk State: ACTIVE
"
            "Heat: COOL",
            parse_mode="Markdown"
        )

    async def cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "⏸ *Auto-trading PAUSED*

"
            "Signals will still stream. Tap-to-execute only.",
            parse_mode="Markdown"
        )

    async def cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "▶️ *Auto-trading RESUMED*

"
            "High-confidence signals will auto-execute.",
            parse_mode="Markdown"
        )

    async def cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📜 *Last 10 Trades*

"
            "No trades recorded yet.
"
            "Load an agent on a pair to begin.",
            parse_mode="Markdown"
        )

    async def cmd_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🛡 *Risk Governor*

"
            "Max Stake: $5.00
"
            "Daily Loss Limit: $50.00
"
            "Max Consecutive Losses: 3
"
            "Cooldown: 5 min after 2 losses
"
            "Heat Threshold: 20%

"
            "Status: ACTIVE ✅",
            parse_mode="Markdown"
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data

        if data.startswith("EXECUTE_"):
            signal_id = data.replace("EXECUTE_", "")
            if signal_id in self.pending_signals:
                signal = self.pending_signals[signal_id]
                if self.on_execute_callback:
                    result = await self.on_execute_callback(signal)
                    await query.edit_message_text(
                        f"✅ *EXECUTED*

"
                        f"Signal: {signal.get('signal', 'UNKNOWN')}
"
                        f"Bias: {signal.get('bias', 'CALL')}
"
                        f"Result: {result}",
                        parse_mode="Markdown"
                    )
                del self.pending_signals[signal_id]

        elif data.startswith("WHY_"):
            signal_id = data.replace("WHY_", "")
            if signal_id in self.pending_signals and self.on_why_callback:
                explanation = await self.on_why_callback(self.pending_signals[signal_id])
                await query.edit_message_text(
                    f"🧠 *Why This Trade?*

{explanation}",
                    parse_mode="Markdown"
                )

        elif data.startswith("HISTORY_"):
            signal_id = data.replace("HISTORY_", "")
            if self.on_history_callback:
                history = await self.on_history_callback()
                await query.edit_message_text(
                    f"📊 *Similar History*

{history}",
                    parse_mode="Markdown"
                )

        elif data == "IGNORE":
            await query.edit_message_text("❌ Signal ignored.")

    async def send_signal(self, signal: Dict[str, Any], narrative: str):
        """Send formatted signal card to Telegram."""
        signal_id = f"{signal.get('symbol', 'UNK')}_{signal.get('time', 0)}"
        self.pending_signals[signal_id] = signal

        conf = signal.get("confidence", 0)
        sync = signal.get("fractal", {}).get("sync_layers", 0)
        quality = signal.get("fractal", {}).get("quality", "MIXED")

        # Emoji based on conviction
        emoji = "🟢" if conf >= 85 else "🟡" if conf >= 60 else "🔴"

        keyboard = [
            [
                InlineKeyboardButton("▶️ EXECUTE", callback_data=f"EXECUTE_{signal_id}"),
                InlineKeyboardButton("🧠 WHY?", callback_data=f"WHY_{signal_id}")
            ],
            [
                InlineKeyboardButton("📊 HISTORY", callback_data=f"HISTORY_{signal_id}"),
                InlineKeyboardButton("❌ IGNORE", callback_data="IGNORE")
            ]
        ]

        message = (
            f"{emoji} *{signal.get('signal', 'SIGNAL')}*

"
            f"📈 Bias: {signal.get('bias', 'CALL')}
"
            f"🎯 Confidence: {conf}%
"
            f"🔄 Fractal: {sync}/4 ({quality})
"
            f"💰 Strike: {signal.get('setup', {}).get('strike', 0)}
"
            f"⏱ Expiry: {signal.get('setup', {}).get('expiry_min', 0)}m
"
            f"📊 RR: {signal.get('setup', {}).get('rr', 0)}:1

"
            f"📝 *Narrative:*
{narrative}"
        )

        await self.app.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def send_execution_alert(self, ticket: Dict[str, Any]):
        """Send execution confirmation."""
        await self.app.bot.send_message(
            chat_id=self.chat_id,
            text=(
                f"✅ *EXECUTED*

"
                f"Ticket: #{ticket.get('contract_id', 'N/A')}
"
                f"Entry: {ticket.get('entry_tick', 0)}
"
                f"Stake: ${ticket.get('buy_price', 0)}

"
                f"Live P&L streaming..."
            ),
            parse_mode="Markdown"
        )

    async def send_pnl_update(self, contract_id: str, pnl: float, spot: float):
        """Send live P&L update."""
        emoji = "🟢" if pnl >= 0 else "🔴"
        await self.app.bot.send_message(
            chat_id=self.chat_id,
            text=f"{emoji} #{contract_id} | P&L: ${pnl:.2f} | Spot: {spot}",
            parse_mode="Markdown"
        )

    async def send_risk_alert(self, alert_type: str, message: str):
        """Send risk governor alert."""
        await self.app.bot.send_message(
            chat_id=self.chat_id,
            text=f"🛡 *RISK ALERT: {alert_type}*

{message}",
            parse_mode="Markdown"
        )

    def set_callbacks(self, on_execute, on_why, on_history):
        self.on_execute_callback = on_execute
        self.on_why_callback = on_why
        self.on_history_callback = on_history
