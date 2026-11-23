
from cryptography.fernet import Fernet
from pathlib import Path

KEY_FILE = Path(__file__).resolve().parent / "secret.key"


def generate_key():
    if KEY_FILE.exists():
        print("A key already exists.")
        print("Delete it only if you intend to replace it.")
        return

    key = Fernet.generate_key()

    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

    print("Encryption key generated successfully!")
    print("Key saved in secret.key")


if __name__ == "__main__":
    generate_key()
