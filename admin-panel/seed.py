import json, hashlib, os
from datetime import datetime

os.makedirs('data', exist_ok=True)

def h(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

users = [
    {"id": "1", "username": "admin",  "password_hash": h("admin123"),
     "role": "admin", "created_at": datetime.now().isoformat()},
    {"id": "2", "username": "user1",  "password_hash": h("user123"),
     "role": "user",  "created_at": datetime.now().isoformat()},
]

with open('data/users.json', 'w') as f:
    json.dump(users, f, indent=2)

print("✓ data/users.json создан")
print("  admin / admin123")
print("  user1 / user123")