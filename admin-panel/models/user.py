import hashlib
from datetime import datetime


class User:
    def __init__(self, id: str, username: str, password_hash: str,
                 role: str, created_at: str,
                 salary: int = 0, department: str = ''):
        self.id            = id
        self.username      = username
        self.password_hash = password_hash
        self.role          = role
        self.created_at    = created_at
        self.salary        = salary
        self.department    = department

    def check_password(self, password: str) -> bool:
        return self.password_hash == User.hash_password(password)

    def to_dict(self) -> dict:
        return {
            'id':            self.id,
            'username':      self.username,
            'password_hash': self.password_hash,
            'role':          self.role,
            'created_at':    self.created_at,
            'salary':        self.salary,
            'department':    self.department,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            id            = data['id'],
            username      = data['username'],
            password_hash = data['password_hash'],
            role          = data['role'],
            created_at    = data['created_at'],
            salary        = data.get('salary', 0),
            department    = data.get('department', ''),
        )

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()