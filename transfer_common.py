
import csv
import hashlib
import json
import math
import socket
import struct
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

BASE_DIR = Path(__file__).resolve().parent
KEY_FILE = BASE_DIR / "secret.key"
HISTORY_FILE = BASE_DIR / "transfer_history.csv"

CHUNK_SIZE = 64 * 1024
MAX_HEADER_SIZE = 1024 * 1024
MAX_TOKEN_SIZE = 1024 * 1024


def load_fernet():
    if not KEY_FILE.exists():
        raise FileNotFoundError("secret.key not found.")

    return Fernet(KEY_FILE.read_bytes())


def receive_exact(sock, size):
    data = bytearray()

    while len(data) < size:
        part = sock.recv(size - len(data))

        if not part:
            raise ConnectionError("Connection closed.")

        data.extend(part)

    return bytes(data)


def send_packet(sock, data):
    sock.sendall(struct.pack("!I", len(data)))
    sock.sendall(data)


def receive_packet(sock, maximum=MAX_HEADER_SIZE):
    length = struct.unpack("!I", receive_exact(sock, 4))[0]

    if length <= 0 or length > maximum:
        raise ValueError("Invalid packet size.")

    return receive_exact(sock, length)


def calculate_hash(filename):
    digest = hashlib.sha256()
    size = 0

    with open(filename, "rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            digest.update(chunk)
            size += len(chunk)

    return digest.hexdigest(), size


def save_history(direction, filename, status, details=""):
    new_file = not HISTORY_FILE.exists()

    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if new_file:
            writer.writerow([
                "Date and Time",
                "Direction",
                "Filename",
                "Status",
                "Details"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            direction,
            filename,
            status,
            details
        ])


def send_file(sock, filename, progress_callback=None):
    fernet = load_fernet()
    filename = Path(filename)

    if not filename.is_file():
        raise FileNotFoundError("File not found.")

    file_hash, file_size = calculate_hash(filename)
    chunks = math.ceil(file_size / CHUNK_SIZE)

    header = {
        "filename": filename.name,
        "size": file_size,
        "chunks": chunks,
        "sha256": file_hash,
        "chunk_size": CHUNK_SIZE,
        "auth": fernet.encrypt(
            b"secure-file-transfer-v1"
        ).decode("utf-8")
    }

    send_packet(sock, json.dumps(header).encode("utf-8"))

    sent = 0

    with open(filename, "rb") as file:
        while True:
            data = file.read(CHUNK_SIZE)

            if not data:
                break

            send_packet(sock, fernet.encrypt(data))
            sent += len(data)

            if progress_callback:
                progress_callback(sent, file_size)

    response = json.loads(receive_packet(sock).decode("utf-8"))

    if response.get("status") != "success":
        raise RuntimeError(response.get("message", "Transfer failed."))

    return file_hash


def receive_file(sock, save_folder):
    fernet = load_fernet()

    header = json.loads(receive_packet(sock).decode("utf-8"))

    try:
        auth = fernet.decrypt(header["auth"].encode("utf-8"))
    except (InvalidToken, KeyError, TypeError):
        raise PermissionError("Authentication failed.")

    if auth != b"secure-file-transfer-v1":
        raise PermissionError("Invalid authentication.")

    filename = Path(header["filename"]).name
    file_size = header["size"]
    chunks = header["chunks"]
    expected_hash = header["sha256"]

    if (
        not filename
        or not isinstance(file_size, int)
        or not isinstance(chunks, int)
        or file_size < 0
        or chunks < 0
        or chunks > 1000000
        or file_size > 10 * 1024 * 1024 * 1024
        or chunks != math.ceil(file_size / CHUNK_SIZE)
        or header["chunk_size"] != CHUNK_SIZE
    ):
        raise ValueError("Invalid file information.")

    save_folder = Path(save_folder)
    save_folder.mkdir(parents=True, exist_ok=True)

    output_path = save_folder / filename
    counter = 1

    while output_path.exists():
        output_path = save_folder / (
            f"{Path(filename).stem}_{counter}{Path(filename).suffix}"
        )
        counter += 1

    temp_path = output_path.with_name(output_path.name + ".part")

    digest = hashlib.sha256()
    received_size = 0

    try:
        with open(temp_path, "wb") as file:
            for _ in range(chunks):
                encrypted_data = receive_packet(sock, MAX_TOKEN_SIZE)
                data = fernet.decrypt(encrypted_data)

                if not data or len(data) > CHUNK_SIZE:
                    raise ValueError("Invalid file chunk.")

                received_size += len(data)

                if received_size > file_size:
                    raise ValueError("File size exceeded.")

                digest.update(data)
                file.write(data)

        if received_size != file_size:
            raise ValueError("File size verification failed.")

        if digest.hexdigest() != expected_hash:
            raise ValueError("SHA-256 verification failed.")

        temp_path.replace(output_path)

        send_packet(
            sock,
            json.dumps({
                "status": "success",
                "message": "File received and verified."
            }).encode("utf-8")
        )

        return output_path

    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise
