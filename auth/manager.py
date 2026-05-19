from getpass import getpass
from typing import Optional
import bcrypt  # Thay vì từ passlib.hash import bcrypt
from pymongo.errors import DuplicateKeyError
from datetime import datetime


def ensure_indexes(db_client):
    """Create necessary indexes for users collection."""
    users = db_client.users()
    try:
        users.create_index('username', unique=True)
    except Exception:
        pass


def truncate_password(password: str) -> bytes:
    """Truncate password to 72 bytes for bcrypt compatibility."""
    if not password:
        return b''

    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        return password_bytes[:72]
    return password_bytes


def register_user(db_client, username: str, password: str,
                  full_name: Optional[str] = None,
                  age: Optional[int] = None,
                  position: Optional[str] = None,
                  email: Optional[str] = None,
                  phone: Optional[str] = None) -> bool:
    """Register a new user. Returns True on success, False on failure.

    Passwords are hashed with bcrypt. Stores basic profile information.
    """
    users = db_client.users()

    # Truncate password if it's longer than 72 bytes
    password_bytes = truncate_password(password)

    # Hash với bcrypt trực tiếp
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Convert bytes to string for storage
    hashed_str = hashed.decode('utf-8')

    # sanitize age
    try:
        age_val = int(age) if age is not None and str(age).strip() != '' else None
    except Exception:
        age_val = None

    doc = {
        'username': username,
        'password': hashed_str,
        'full_name': full_name or username,
        'age': age_val,
        'position': position,
        'email': email,
        'phone': phone,
        'created_at': datetime.utcnow(),
    }
    try:
        users.insert_one(doc)
        return True
    except DuplicateKeyError:
        return False
    except Exception as e:
        print(f"Registration error: {e}")
        return False


def authenticate_user(db_client, username: str, password: str) -> Optional[dict]:
    """Authenticate username/password against MongoDB.

    Returns the user document (without password) on success, or None on failure.
    """
    users = db_client.users()
    user = users.find_one({'username': username})
    if not user:
        return None
    try:
        # Truncate password for verification as well
        password_bytes = truncate_password(password)

        # Get stored hash
        stored_hash = user.get('password', '')
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')

        if bcrypt.checkpw(password_bytes, stored_hash):
            # don't return password hash
            user_copy = {k: v for k, v in user.items() if k != 'password'}
            return user_copy
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None


def prompt_register(db_client):
    print('\n=== Register New Account ===')
    username = input('Username: ').strip()
    if not username:
        print('Invalid username')
        return None
    password = getpass('Password: ')
    confirm = getpass('Confirm password: ')
    if password != confirm:
        print('Passwords do not match')
        return None
    name = input('Full name (optional): ').strip() or None
    age = input('Age (optional): ').strip() or None
    position = input('Position (optional): ').strip() or None
    email = input('Email (optional): ').strip() or None
    phone = input('Phone (optional): ').strip() or None
    success = register_user(db_client, username, password, name, age, position, email, phone)
    if success:
        print('✅ Registered successfully')
        return authenticate_user(db_client, username, password)
    else:
        print('❌ Registration failed (username may already exist)')
        return None


def prompt_login(db_client):
    print('\n=== Login ===')
    username = input('Username: ').strip()
    password = getpass('Password: ')
    user = authenticate_user(db_client, username, password)
    if user:
        print('✅ Login successful')
        return user
    else:
        print('❌ Login failed')
        return None