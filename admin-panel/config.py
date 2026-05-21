class Config:
    SECRET_KEY = 'just-text'
    DB_PATH    = 'data'
    BOT_TOKEN  = 'TOKEN'
    DEBUG      = True

    USERS_JSON       = f'{DB_PATH}/users.json'
    DEPARTMENTS_JSON = f'{DB_PATH}/departments.json'
    SUBSCRIBERS_JSON = f'{DB_PATH}/subscribers.json'