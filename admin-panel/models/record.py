class Record:
    def __init__(self, id: str, name: str, salary: int, department: str,
                 worked_since: int, user_id: str, created_at: str):
        self.id           = id
        self.name         = name
        self.salary       = salary
        self.department   = department
        self.worked_since = worked_since  # год
        self.user_id      = user_id       # владелец записи
        self.created_at   = created_at

    def to_dict(self) -> dict:
        return {
            'id':           self.id,
            'name':         self.name,
            'salary':       self.salary,
            'department':   self.department,
            'worked_since': self.worked_since,
            'user_id':      self.user_id,
            'created_at':   self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Record':
        return cls(
            id           = data['id'],
            name         = data['name'],
            salary       = data['salary'],
            department   = data['department'],
            worked_since = data['worked_since'],
            user_id      = data['user_id'],
            created_at   = data['created_at'],
        )