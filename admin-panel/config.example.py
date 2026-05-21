class Config:
    SECRET_KEY = 'change-this'
    DB_PATH    = 'data'
    BOT_TOKEN  = 'your-bot-token-here'
    DEBUG      = True

    USERS_JSON       = f'{DB_PATH}/users.json'
    RECORDS_JSON     = f'{DB_PATH}/records.json'
    DEPARTMENTS_JSON = f'{DB_PATH}/departments.json'
    SUBSCRIBERS_JSON = f'{DB_PATH}/subscribers.json'