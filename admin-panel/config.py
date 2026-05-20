class Config:
    SECRET_KEY = 'change-this-in-production'
    DB_PATH    = 'data'
    BOT_TOKEN  = 'your-bot-token'
    CHAT_ID    = 'your-chat-id'
    DEBUG      = True

    USERS_JSON       = f'{DB_PATH}/users.json'
    RECORDS_JSON     = f'{DB_PATH}/records.json'
    DEPARTMENTS_JSON = f'{DB_PATH}/departments.json'