import logging

logger = logging.getLogger(__name__)


class BotService:
    def notify_new_user(self, username: str):
        pass

    def notify_admin_action(self, action: str, detail: str):
        pass