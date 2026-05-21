import hashlib


class User:
    def __init__(self, id: str, username: str, password_hash: str,
                 role: str, created_at: str,
                 telegram_id: int = None):
        self.id            = id
        self.username      = username
        self.password_hash = password_hash
        self.role          = role
        self.created_at    = created_at
        self.telegram_id   = telegram_id  # привязанный Telegram ID (по ТЗ)

    def check_password(self, password: str) -> bool:
        return self.password_hash == User.hash_password(password)

    def to_dict(self) -> dict:
        return {
            'id':            self.id,
            'username':      self.username,
            'password_hash': self.password_hash,
            'role':          self.role,
            'created_at':    self.created_at,
            'telegram_id':   self.telegram_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            id            = data['id'],
            username      = data['username'],
            password_hash = data['password_hash'],
            role          = data['role'],
            created_at    = data['created_at'],
            telegram_id   = data.get('telegram_id', None),
        )

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()