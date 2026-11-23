
import socket
import threading
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from transfer_common import receive_file, save_history

HOST = "0.0.0.0"
PORT = 5001

BASE_DIR = Path(__file__).resolve().parent


class ReceiverApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Secure File Transfer - Receiver")
        self.root.geometry("650x550")
        self.root.configure(bg="#101827")

        self.running = False
        self.server = None
        self.save_folder = BASE_DIR / "received_files"

        self.create_widgets()

    def create_widgets(self):
        tk.Label(
            self.root,
            text="SECURE FILE TRANSFER",
            font=("Arial", 23, "bold"),
            fg="#38BDF8",
            bg="#101827"
        ).pack(pady=(25, 5))

        tk.Label(
            self.root,
            text="RECEIVER DASHBOARD",
            fg="white",
            bg="#101827"
        ).pack()

        self.status = tk.Label(
            self.root,
            text="SERVER STOPPED",
            fg="#F87171",
            bg="#101827",
            font=("Arial", 13, "bold")
        )
        self.status.pack(pady=20)

        tk.Button(
            self.root,
            text="START SERVER",
            command=self.start_server,
            bg="#16A34A",
            fg="white",
            width=22
        ).pack(pady=8)

        tk.Button(
            self.root,
            text="STOP SERVER",
            command=self.stop_server,
            bg="#DC2626",
            fg="white",
            width=22
        ).pack(pady=8)

        tk.Label(
            self.root,
            text=f"Port: {PORT}",
            fg="white",
            bg="#101827"
        ).pack(pady=10)

        tk.Button(
            self.root,
            text="Choose Save Folder",
            command=self.choose_folder
        ).pack(pady=8)

        self.folder_label = tk.Label(
            self.root,
            text=str(self.save_folder),
            fg="#93C5FD",
            bg="#101827",
            wraplength=550
        )
        self.folder_label.pack()

        self.log = tk.Text(
            self.root,
            height=10,
            width=70,
            bg="#1E293B",
            fg="white"
        )
        self.log.pack(padx=20, pady=15)

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def log_message(self, message):
        self.root.after(
            0,
            lambda: self.write_log(message)
        )

    def write_log(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)

    def choose_folder(self):
        folder = filedialog.askdirectory()

        if folder:
            self.save_folder = Path(folder)
            self.folder_label.config(text=folder)

    def start_server(self):
        if self.running:
            return

        self.running = True

        threading.Thread(
            target=self.server_loop,
            daemon=True
        ).start()

    def server_loop(self):
        try:
            self.server = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            self.server.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            self.server.bind((HOST, PORT))
            self.server.listen(5)
            self.server.settimeout(1)

            self.root.after(
                0,
                lambda: self.status.config(
                    text="SERVER RUNNING",
                    fg="#4ADE80"
                )
            )

            self.log_message("Server listening on port 5001...")

            while self.running:
                try:
                    client, address = self.server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                with client:
                    client.settimeout(60)

                    self.log_message(
                        f"Connection from {address[0]}"
                    )

                    try:
                        received_file = receive_file(
                            client,
                            self.save_folder
                        )

                        save_history(
                            "RECEIVED",
                            received_file.name,
                            "SUCCESS",
                            "SHA-256 verified"
                        )

                        self.log_message(
                            f"Received: {received_file.name}"
                        )

                        self.log_message(
                            "SHA-256 verification successful!"
                        )

                    except Exception as error:
                        self.log_message(
                            f"Transfer failed: {error}"
                        )

                        try:
                            save_history(
                                "RECEIVED",
                                "Unknown",
                                "FAILED",
                                str(error)
                            )
                        except Exception:
                            pass

        except Exception as error:
            self.log_message(f"Server error: {error}")

        finally:
            self.running = False

            if self.server:
                self.server.close()
                self.server = None

            self.root.after(
                0,
                lambda: self.status.config(
                    text="SERVER STOPPED",
                    fg="#F87171"
                )
            )

    def stop_server(self):
        self.running = False

        if self.server:
            self.server.close()

        self.log_message("Stopping server...")

    def close_app(self):
        self.stop_server()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiverApp(root)
    root.mainloop()
