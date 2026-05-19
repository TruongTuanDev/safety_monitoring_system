from dataclasses import dataclass


@dataclass
class User:
    username: str
    password_hash: str
    full_name: str | None = None
    age: int | None = None
    position: str | None = None
    email: str | None = None
    phone: str | None = None
