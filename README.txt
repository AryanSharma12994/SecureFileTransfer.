SECURE FILE TRANSFER PROJECT
============================

Files:
- generate_key.py: creates secret.key if it does not already exist.
- transfer_common.py: shared encryption, transfer, SHA-256 verification, and history functions.
- sender_gui.py: sender desktop GUI.
- receiver_gui.py: receiver desktop GUI.
- secret.key: Fernet key used by both sender and receiver.
- received_files/: destination folder created automatically by the receiver.

SETUP
1. Install Python 3.
2. Open PowerShell in this folder.
3. Install the dependency: python -m pip install cryptography
4. Keep the same secret.key file in this folder on both sender and receiver computers.
   Share the key securely; do not send it over an untrusted channel.

RUN
1. Start the receiver first: python receiver_gui.py
2. Click START SERVER.
3. On the sender computer, run: python sender_gui.py
4. Enter the receiver computer's IP address. Use 127.0.0.1 only when both apps
   are running on the same computer. Keep port 5001 available in the firewall.
5. Select a file and click ENCRYPT AND SEND.

NOTE
The older command-line sender.py and encryption.py are included as uploaded.
The GUI version uses transfer_common.py; run the GUI files for the current workflow.
