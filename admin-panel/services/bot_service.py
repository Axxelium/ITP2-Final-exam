import logging
import threading
import requests
from config import Config

logger = logging.getLogger(__name__)


class BotService:

    def _api(self, method: str, **kwargs) -> dict | None:
        """Вызов любого метода Telegram Bot API."""
        try:
            url  = f'https://api.telegram.org/bot{Config.BOT_TOKEN}/{method}'
            resp = requests.post(url, json=kwargs, timeout=5)
            if resp.ok:
                return resp.json()
            logger.error('Telegram API error [%s]: %s %s',
                         method, resp.status_code, resp.text)
        except requests.exceptions.ConnectionError:
            logger.error('Telegram: no connection')
        except requests.exceptions.Timeout:
            logger.error('Telegram: request timed out')
        except Exception as e:
            logger.error('Telegram: unexpected error: %s', e)
        return None

    # ── Отправка одному ───────────────────────────────────────────

    def _send(self, chat_id: int, text: str):
        self._api('sendMessage', chat_id=chat_id,
                  text=text, parse_mode='HTML')

    # ── Рассылка всем подписчикам ─────────────────────────────────

    def _broadcast(self, text: str):
        from services.db_service import DatabaseService
        db = DatabaseService(Config.USERS_JSON,
                             Config.DEPARTMENTS_JSON,
                             Config.SUBSCRIBERS_JSON)
        subscribers = db.get_all_subscribers()
        if not subscribers:
            logger.info('Telegram: no subscribers yet')
            return
        for chat_id in subscribers:
            self._send(chat_id, text)

    # ── Публичные методы ──────────────────────────────────────────

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
        text  = f'<b>{label}</b>\n<code>{detail}</code>'
        self._broadcast(text)

    # ── Polling — обработка /start и /stop ────────────────────────

    def start_polling(self):
        """Запускает polling в отдельном фоновом потоке."""
        thread = threading.Thread(target=self._poll_loop,
                                  daemon=True, name='tg-polling')
        thread.start()
        logger.info('Telegram polling started')

    def _poll_loop(self):
        from services.db_service import DatabaseService
        db = DatabaseService(Config.USERS_JSON,
                             Config.DEPARTMENTS_JSON,
                             Config.SUBSCRIBERS_JSON)
        offset = None

        while True:
            try:
                params = {'timeout': 30, 'allowed_updates': ['message']}
                if offset:
                    params['offset'] = offset

                result = self._api('getUpdates', **params)
                if not result or not result.get('ok'):
                    continue

                for update in result.get('result', []):
                    offset = update['update_id'] + 1
                    self._handle_update(update, db)

            except Exception as e:
                logger.error('Polling error: %s', e)

    def _handle_update(self, update: dict, db):
        try:
            msg     = update.get('message', {})
            text    = msg.get('text', '')
            chat_id = msg.get('chat', {}).get('id')
            name    = msg.get('chat', {}).get('first_name', 'there')

            if not chat_id:
                return

            if text == '/start':
                is_new = db.add_subscriber(chat_id)
                if is_new:
                    self._send(chat_id,
                               f'👋 Hello, <b>{name}</b>!\n'
                               'You are now subscribed to EMS notifications.\n'
                               'Send /stop to unsubscribe.')
                    logger.info('New subscriber: %s', chat_id)
                else:
                    self._send(chat_id,
                               '✅ You are already subscribed.')

            elif text == '/stop':
                removed = db.remove_subscriber(chat_id)
                if removed:
                    self._send(chat_id,
                               '🔕 You have unsubscribed from notifications.')
                else:
                    self._send(chat_id,
                               'You were not subscribed.')

        except Exception as e:
            logger.error('Handle update error: %s', e)