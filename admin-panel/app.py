from flask import Flask
from config import Config


def create_app():
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

    from controllers.auth  import auth_bp
    from controllers.admin import admin_bp
    from controllers.user  import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    return app


if __name__ == '__main__':
    app = create_app()

    # Запускаем Telegram polling в фоне
    from services.bot_service import BotService
    BotService().start_polling()

    app.run(debug=Config.DEBUG, use_reloader=False)