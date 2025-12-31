from datetime import datetime
from passlib.context import CryptContext

# API key hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_api_key(api_key: str) -> str:
    """Hash an API key using bcrypt.
    
    Bcrypt has a 72 byte limit, so we truncate if necessary.
    """
    # Bcrypt limit is 72 bytes, truncate if longer
    api_key_bytes = api_key.encode('utf-8')
    if len(api_key_bytes) > 72:
        api_key_bytes = api_key_bytes[:72]
        api_key = api_key_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash.
    
    Bcrypt has a 72 byte limit, so we truncate if necessary (same as hash).
    """
    # Bcrypt limit is 72 bytes, truncate if longer (must match hash behavior)
    plain_key_bytes = plain_key.encode('utf-8')
    if len(plain_key_bytes) > 72:
        plain_key_bytes = plain_key_bytes[:72]
        plain_key = plain_key_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_key, hashed_key)

