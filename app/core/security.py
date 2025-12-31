from datetime import datetime
from passlib.context import CryptContext

# API key hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_api_key(api_key: str) -> str:
    """Hash an API key using bcrypt.
    
    Bcrypt has a 72 byte limit, so we truncate if necessary.
    We use a safety margin of 60 bytes to avoid any edge cases.
    """
    # Bcrypt limit is 72 bytes, use 60 as safety margin
    api_key_bytes = api_key.encode('utf-8')
    if len(api_key_bytes) > 60:
        # Truncate to 60 bytes for safety
        api_key_bytes = api_key_bytes[:60]
        # Decode back to string, ignoring any incomplete UTF-8 sequences
        api_key = api_key_bytes.decode('utf-8', errors='ignore')
    # Ensure we're passing a string that's definitely under 72 bytes
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash.
    
    Bcrypt has a 72 byte limit, so we truncate if necessary (same as hash).
    We use a safety margin of 60 bytes to match hash behavior.
    """
    # Bcrypt limit is 72 bytes, use 60 as safety margin (must match hash behavior)
    plain_key_bytes = plain_key.encode('utf-8')
    if len(plain_key_bytes) > 60:
        plain_key_bytes = plain_key_bytes[:60]
        plain_key = plain_key_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_key, hashed_key)

