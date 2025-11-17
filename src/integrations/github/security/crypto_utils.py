from cryptography.fernet import Fernet
import os

# stores the key in the user's home directory
KEY_FILE = os.path.expanduser("~/.portfolio_github_key")

def load_key():
    """
    Load the encryption key from file or generate one if it is missing.
    The key persists per-machine so tokens remain decryptable next run
    """

    # look for key, if it exists return it, exits function
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
        
    # generate key
    key = Fernet.generate_key()

    # store key
    with open(KEY_FILE, "wb") as f:
        f.write(key)

    # return key for encryption
    return key

def encrypt_token(token: str) -> bytes:
    f = Fernet(load_key())
    return f.encrypt(token.encode())

def decrypt_token(token_bytes: bytes) -> str:
    f = Fernet(load_key())
    return f.decrypt(token_bytes).decode()