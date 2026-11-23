
import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from transfer_common import send_file, save_history

PORT = 5001


class SenderApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Secure File Transfer - Sender")
        self.root.geometry("650x550")
        self.root.configure(bg="#101827")

        self.selected_file = None
        self.sending = False

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
            text="SENDER DASHBOARD",
            font=("Arial", 12),
            fg="white",
            bg="#101827"
        ).pack(pady=5)

        tk.Label(
            self.root,
            text="Receiver IP Address",
            fg="white",
            bg="#101827"
        ).pack(pady=(20, 5))

        self.host_entry = tk.Entry(
            self.root,
            width=35,
            font=("Arial", 12),
            justify="center"
        )
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.pack(pady=5)

        tk.Label(
            self.root,
            text=f"Port: {PORT}",
            fg="white",
            bg="#101827"
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="SELECT FILE",
            command=self.select_file,
            bg="#2563EB",
            fg="white",
            font=("Arial", 12, "bold"),
            width=22
        ).pack(pady=15)

        self.file_label = tk.Label(
            self.root,
            text="No file selected",
            fg="#93C5FD",
            bg="#101827",
            wraplength=550
        )
        self.file_label.pack(pady=5)

        self.progress = ttk.Progressbar(
            self.root,
            length=450,
            mode="determinate"
        )
        self.progress.pack(pady=20)

        self.progress_label = tk.Label(
            self.root,
            text="Waiting to send...",
            fg="white",
            bg="#101827"
        )
        self.progress_label.pack()

        self.send_button = tk.Button(
            self.root,
            text="ENCRYPT AND SEND",
            command=self.start_transfer,
            bg="#16A34A",
            fg="white",
            font=("Arial", 13, "bold"),
            width=22
        )
        self.send_button.pack(pady=20)

        self.log = tk.Text(
            self.root,
            height=7,
            width=70,
            bg="#1E293B",
            fg="#E2E8F0"
        )
        self.log.pack(padx=20, pady=10)

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_app
        )

    def log_message(self, message):
        self.root.after(
            0,
            lambda: self.write_log(message)
        )

    def write_log(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)

    def select_file(self):
        filename = filedialog.askopenfilename()

        if filename:
            self.selected_file = filename

            self.file_label.config(
                text=Path(filename).name
            )

            self.log_message(
                f"Selected file: {filename}"
            )

    def start_transfer(self):
        if self.sending:
            return

        if not self.selected_file:
            messagebox.showwarning(
                "Warning",
                "Please select a file first."
            )
            return

        host = self.host_entry.get().strip()

        if not host:
            messagebox.showwarning(
                "Warning",
                "Enter receiver IP address."
            )
            return

        self.sending = True
        self.send_button.config(state="disabled")
        self.progress["value"] = 0
        self.progress_label.config(text="Connecting...")

        threading.Thread(
            target=self.transfer,
            args=(host, self.selected_file),
            daemon=True
        ).start()

    def update_progress(self, sent, total):
        percentage = (
            (sent / total) * 100 if total else 100
        )

        self.root.after(
            0,
            lambda: self.update_progress_ui(
                percentage, sent, total
            )
        )

    def update_progress_ui(self, percentage, sent, total):
        self.progress["value"] = percentage

        self.progress_label.config(
            text=f"{percentage:.1f}% ({sent}/{total} bytes)"
        )

    def transfer(self, host, filename):
        try:
            self.log_message("Connecting to receiver...")

            with socket.create_connection(
                (host, PORT),
                timeout=15
            ) as client:

                client.settimeout(60)

                self.log_message("Connected successfully.")
                self.log_message("Encrypting and transferring...")

                file_hash = send_file(
                    client,
                    filename,
                    self.update_progress
                )

            save_history(
                "SENT",
                Path(filename).name,
                "SUCCESS",
                f"SHA-256: {file_hash}"
            )

            self.log_message("File sent successfully!")
            self.log_message("SHA-256: " + file_hash)

            self.root.after(
                0,
                lambda: self.finish_transfer(
                    True,
                    "File transferred and verified successfully!"
                )
            )

        except Exception as error:
            self.log_message(
                f"Transfer failed: {error}"
            )

            self.root.after(
                0,
                lambda: self.finish_transfer(
                    False,
                    str(error)
                )
            )

    def finish_transfer(self, success, message):
        self.sending = False
        self.send_button.config(state="normal")

        if success:
            self.progress["value"] = 100
            self.progress_label.config(text="Transfer complete!")

            messagebox.showinfo("Success", message)
        else:
            self.progress_label.config(text="Transfer failed.")

            messagebox.showerror("Transfer Error", message)

    def close_app(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SenderApp(root)
    root.mainloop()
