from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # Encode to bytes and truncate to 72 bytes, which is bcrypt's limit
    # This prevents the ValueError crash
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)

def verify_password(plain: str, hashed: str) -> bool:
    # Use the same truncation logic for verification
    password_bytes = plain.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes, hashed)