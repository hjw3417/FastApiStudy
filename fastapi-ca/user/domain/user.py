from dataclasses import dataclass
from datetime import datetime

@dataclass
class Profile:
    name: str
    email: str

@dataclass
class User:
    id: str
    profile: Profile
    password: str
    created_at: datetime
    updated_at: datetime