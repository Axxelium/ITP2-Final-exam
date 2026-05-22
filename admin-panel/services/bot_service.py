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

    # Рассылка всем подписчикам

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
        # Fallback: use CHAT_ID from Config if nobody subscribed via /start yet
        if not subscribers and getattr(Config, 'CHAT_ID', ''):
            subscribers = [Config.CHAT_ID]
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

    # Публичные уведомления

    def notify_new_user(self, username: str):
        text = (
            '👤 <b>New employee registered</b>\n'
            f'Username: <code>{username}</code>'
        )
        self._broadcast(text)

    def notify_admin_action(self, action: str, detail: str):
        labels = {
            'delete_user':   '🗑 Employee deleted',
            'edit_user':     '✏️ Employee updated',
            'delete_record': '🗑 Record deleted',
            'edit_record':   '✏️ Record updated',
        }
        label = labels.get(action, f'⚙️ Action: {action}')
        self._broadcast(f'<b>{label}</b>\n<code>{detail}</code>')

    # Polling — обрабатывает команды

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
            await app.updater.start_poll