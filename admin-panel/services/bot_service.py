import logging
import threading

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import Config

logger = logging.getLogger(__name__)


class BotService:

    def __init__(self):
        self._app = None

    def _build_app(self) -> Application:
        return Application.builder().token(Config.BOT_TOKEN).build()

    # ── Рассылка всем подписчикам ─────────────────────────────────

    def _get_db(self):
        from services.db_service import DatabaseService
        return DatabaseService(
            Config.USERS_JSON,
            Config.DEPARTMENTS_JSON,
            Config.RECORDS_JSON,
        )

    def _broadcast(self, text: str):
        import asyncio
        db          = self._get_db()
        subscribers = db.get_all_subscribers()
        if not subscribers:
            logger.info('Telegram: no subscribers')
            return

        async def _send_all():
            app = Application.builder().token(Config.BOT_TOKEN).build()
            async with app:
                for chat_id in subscribers:
                    try:
                        await app.bot.send_message(
                            chat_id   = chat_id,
                            text      = text,
                            parse_mode = 'HTML',
                        )
                    except Exception as e:
                        logger.error('Telegram send error to %s: %s', chat_id, e)

        try:
            asyncio.run(_send_all())
        except Exception as e:
            logger.error('Telegram broadcast error: %s', e)

    # ── Публичные методы уведомлений ──────────────────────────────

    def notify_new_user(self, username: str):
        text = (
            '👤 <b>New employee registered</b>\n'
            f'Username: <code>{username}</code>'
        )
        self._broadcast(text)

    def notify_admin_action(self, action: str, detail: str):
        labels = {
            'delete_user': '🗑 Employee deleted',
            'edit_user':   '✏️ Employee updated',
        }
        label = labels.get(action, f'⚙️ Action: {action}')
        self._broadcast(f'<b>{label}</b>\n<code>{detail}</code>')

    # ── Polling — обработчики команд ──────────────────────────────

    def start_polling(self):
        thread = threading.Thread(
            target  = self._run_polling,
            daemon  = True,
            name    = 'tg-polling',
        )
        thread.start()
        logger.info('Telegram polling started')

    def _run_polling(self):
        import asyncio
        asyncio.run(self._polling_main())

    async def _polling_main(self):
        app = self._build_app()

        app.add_handler(CommandHandler('start',  self._handle_start))
        app.add_handler(CommandHandler('stop',   self._handle_stop))
        app.add_handler(CommandHandler('link',   self._handle_link))
        app.add_handler(CommandHandler('me',     self._handle_me))
        app.add_handler(CommandHandler('help',   self._handle_help))

        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            # держим polling живым пока поток не убит
            import asyncio as _asyncio
            while True:
                await _asyncio.sleep(3600)

    # ── Команды бота ─────────────────────────────────────────────

    async def _handle_start(self, update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
        db      = self._get_db()
        chat_id = update.effective_chat.id
        name    = update.effective_user.first_name or 'there'
        is_new  = db.add_subscriber(chat_id)

        if is_new:
            text = (
                f'👋 Hello, <b>{name}</b>!\n'
                'You are now subscribed to EMS notifications.\n\n'
                'To link your Telegram to your EMS account:\n'
                '<code>/link your_username your_password</code>\n\n'
                'Send /stop to unsubscribe, /help for all commands.'
            )
        else:
            text = '✅ You are already subscribed. Send /help for commands.'

        await update.message.reply_text(text, parse_mode='HTML')

    async def _handle_stop(self, update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
        db      = self._get_db()
        chat_id = update.effective_chat.id
        removed = db.remove_subscriber(chat_id)

        if removed:
            await update.message.reply_text('🔕 You have unsubscribed.')
        else:
            await update.message.reply_text('You were not subscribed.')

    async def _handle_link(self, update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 2:
            await update.message.reply_text(
                'Usage: /link username password\n'
                'Example: /link admin admin123',
            )
            return

        username = context.args[0]
        password = context.args[1]
        chat_id  = update.effective_chat.id

        db   = self._get_db()
        user = db.get_user_by_username(username)

        if not user or not user.check_password(password):
            await update.message.reply_text(
                '❌ Invalid username or password.'
            )
            return

        # Проверяем — не привязан ли этот telegram к другому аккаунту
        all_users = db.get_all_users()
        for u in all_users:
            if u.telegram_id == chat_id and u.id != user.id:
                await update.message.reply_text(
                    '⚠️ This Telegram account is already linked to another user.'
                )
                return

        user.telegram_id = chat_id
        db.update_user(user)

        # Подписываем автоматически если ещё не подписан
        db.add_subscriber(chat_id)

        await update.message.reply_text(
            f'✅ Successfully linked to EMS account <b>{username}</b>!\n'
            'You will now receive personal notifications.',
            parse_mode='HTML',
        )

    async def _handle_me(self, update: Update,
                         context: ContextTypes.DEFAULT_TYPE):
        """Показывает к какому аккаунту привязан этот Telegram."""
        chat_id   = update.effective_chat.id
        db        = self._get_db()
        all_users = db.get_all_users()
        linked    = next((u for u in all_users
                          if u.telegram_id == chat_id), None)

        if linked:
            await update.message.reply_text(
                f'🔗 Linked to EMS account: <b>{linked.username}</b>\n'
                f'Role: {linked.role}\n'
                f'Department: {linked.department or "—"}',
                parse_mode='HTML',
            )
        else:
            await update.message.reply_text(
                '🔓 Not linked to any EMS account.\n'
                'Use /link <username> <password> to connect.'
            )

    async def _handle_help(self, update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
        text = (
            '<b>EMS Bot commands</b>\n\n'
            '/start — Subscribe to notifications\n'
            '/stop — Unsubscribe\n'
            '/link &lt;username&gt; &lt;password&gt; — Link your EMS account\n'
            '/me — Show linked account info\n'
            '/help — This message'
        )
        await update.message.reply_text(text, parse_mode='HTML')