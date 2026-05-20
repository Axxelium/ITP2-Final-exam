import json
import os
from models.user   import User
from models.record import Record


class DatabaseService:
    def __init__(self, users_path: str, records_path: str,
                 departments_path: str = 'data/departments.json'):
        self.users_path        = users_path
        self.records_path      = records_path
        self.departments_path  = departments_path
        self._ensure_files()

    def _ensure_files(self):
        for path in [self.users_path, self.records_path, self.departments_path]:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump([], f)

    # ══ USERS ════════════════════════════════════════════════════

    def _load_users(self) -> list:
        with open(self.users_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_users(self, data: list):
        with open(self.users_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all_users(self) -> list[User]:
        return [User.from_dict(u) for u in self._load_users()]

    def get_user_by_id(self, user_id: str) -> User | None:
        for u in self._load_users():
            if u['id'] == user_id:
                return User.from_dict(u)
        return None

    def get_user_by_username(self, username: str) -> User | None:
        for u in self._load_users():
            if u['username'] == username:
                return User.from_dict(u)
        return None

    def save_user(self, user: User):
        data = self._load_users()
        data.append(user.to_dict())
        self._save_users(data)

    def update_user(self, user: User):
        data = self._load_users()
        for i, u in enumerate(data):
            if u['id'] == user.id:
                data[i] = user.to_dict()
                break
        self._save_users(data)

    def delete_user(self, user_id: str) -> bool:
        data     = self._load_users()
        new_data = [u for u in data if u['id'] != user_id]
        if len(new_data) < len(data):
            self._save_users(new_data)
            return True
        return False

    # ══ RECORDS ══════════════════════════════════════════════════

    def _load_records(self) -> list:
        with open(self.records_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_records(self, data: list):
        with open(self.records_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all_records(self) -> list[Record]:
        return [Record.from_dict(r) for r in self._load_records()]

    def get_records_by_user(self, user_id: str) -> list[Record]:
        return [Record.from_dict(r)
                for r in self._load_records()
                if r['user_id'] == user_id]

    def get_record_by_id(self, record_id: str) -> Record | None:
        for r in self._load_records():
            if r['id'] == record_id:
                return Record.from_dict(r)
        return None

    def save_record(self, record: Record):
        data = self._load_records()
        data.append(record.to_dict())
        self._save_records(data)

    def update_record(self, record: Record):
        data = self._load_records()
        for i, r in enumerate(data):
            if r['id'] == record.id:
                data[i] = record.to_dict()
                break
        self._save_records(data)

    def delete_records_by_user(self, user_id: str):
        data = self._load_records()
        self._save_records([r for r in data if r['user_id'] != user_id])

    # ══ DEPARTMENTS ═══════════════════════════════════════════════

    def _load_departments(self) -> list:
        with open(self.departments_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_departments(self, data: list):
        with open(self.departments_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all_departments(self) -> list[dict]:
        return self._load_departments()

    def get_department_by_id(self, dept_id: str) -> dict | None:
        for d in self._load_departments():
            if d['id'] == dept_id:
                return d
        return None

    def save_department(self, dept: dict):
        data = self._load_departments()
        data.append(dept)
        self._save_departments(data)

    def update_department(self, dept_id: str, name: str) -> bool:
        data = self._load_departments()
        for d in data:
            if d['id'] == dept_id:
                d['name'] = name
                self._save_departments(data)
                return True
        return False

    def delete_department(self, dept_id: str) -> bool:
        data     = self._load_departments()
        new_data = [d for d in data if d['id'] != dept_id]
        if len(new_data) < len(data):
            self._save_departments(new_data)
            return True
        return False