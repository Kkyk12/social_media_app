import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


_ENV_KEY_NAME = "CHAT_ENCRYPTION_KEY"


def _get_fernet() -> Fernet:
    key = os.getenv(_ENV_KEY_NAME)
    if not key:
        raise RuntimeError(
            f"Environment variable {_ENV_KEY_NAME} is not set. "
            "Generate a Fernet key with cryptography.fernet.Fernet.generate_key() "
            "and set it in your environment before starting the app."
        )
    return Fernet(key.encode() if not key.startswith("gAAAA") and len(key) != 44 else key.encode())


def encrypt_text(plain_text: str) -> str:
    """Encrypt plain_text and return a URL-safe base64 string."""
    f = _get_fernet()
    token = f.encrypt(plain_text.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: str) -> Optional[str]:
    """Decrypt token and return plain text. Returns None if decryption fails."""
    f = _get_fernet()
    try:
        plain = f.decrypt(token.encode("utf-8"))
        return plain.decode("utf-8")
    except InvalidToken:
        return None


__all__ = ["encrypt_text", "decrypt_text"]
