import os
import json
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from secrets import token_bytes


def _kdf(password: bytes, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=2**15, r=8, p=1)
    return kdf.derive(password)


def create_keystore(path: str, password: str, payload: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    salt = os.urandom(16)
    key = _kdf(password.encode(), salt)
    aead = ChaCha20Poly1305(key)
    nonce = os.urandom(12)
    ct = aead.encrypt(nonce, json.dumps(payload).encode(), None)
    with open(path, "wb") as f:
        f.write(b"KS1" + salt + nonce + ct)


def load_keystore(path: str, password: str) -> dict:
    blob = open(path, "rb").read()
    assert blob[:3] == b"KS1"
    salt, nonce, ct = blob[3:19], blob[19:31], blob[31:]
    key = _kdf(password.encode(), salt)
    aead = ChaCha20Poly1305(key)
    data = aead.decrypt(nonce, ct, None)
    return json.loads(data.decode())