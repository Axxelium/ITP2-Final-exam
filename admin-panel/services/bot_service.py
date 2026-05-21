import logging
import requests
from config import Config

logger = logging.getLogger(__name__)


class BotService:

    def _send(self, text: str):
        """Отправляет сообщение через Telegram Bot API синхронно."""
        try:
            url  = f'https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage'
            resp = requests.post(url, json={
                'chat_id': Config.CHAT_ID,
                'text':    text,
                'parse_mode': 'HTML',
            }, timeout=5)

            if not resp.ok:
                logger.error('Telegram API error: %s %s',
                             resp.status_code, resp.text)
        except requests.exceptions.ConnectionError:
            logger.error('Telegram: no connection')
        except requests.exceptions.Timeout:
            logger.error('Telegram: request timed out')
        except Exception as e:
            logger.error('Telegram: unexpected error: %s', e)

    def notify_new_user(self, username: str):
        """Уведомление при регистрации нового пользователя."""
        text = (
            '👤 <b>New employee registered</b>\n'
            f'Username: <code>{username}</code>'
        )
        self._send(text)

    def notify_admin_action(self, action: str, detail: str):
        """Уведомление при ключевом действии администратора."""
        labels = {
            'delete_user': '🗑 Employee deleted',
            'edit_user':   '✏️ Employee updated',
        }
        label = labels.get(action, f'⚙️ Action: {action}')
        text  = f'<b>{label}</b>\n<code>{detail}</code>'
        self._send(text)