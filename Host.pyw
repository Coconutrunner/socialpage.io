# host.py
import threading
import webbrowser
import os
import sys
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from flask import Flask, send_from_directory, request
import logging

# === Flask setup ===
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, "home.html")

@app.route('/<path:filename>')
def serve_files(filename):
    return send_from_directory(BASE_DIR, filename)

# === Only log connections ===
log = logging.getLogger('werkzeug')
log.disabled = True  # disable default werkzeug logs

@app.after_request
def log_request(response):
    ip = request.remote_addr
    path = request.path
    print(f"[CONNECT] {ip} -> {path} ({response.status_code})")
    return response

# === Redirect Python prints to GUI ===
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        if message.strip():  # ignore empty lines
            self.text_widget.insert(END, message + "\n")
            self.text_widget.see(END)

    def flush(self):
        pass

# === Tkinter GUI ===
class ServerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Social Project Host")

        Label(master, text="Social Project Webserver", font=("Arial", 14)).pack(pady=10)

        # IP input
        ip_frame = Frame(master)
        ip_frame.pack(pady=2)
        Label(ip_frame, text="IP:").pack(side=LEFT)
        self.ip_entry = Entry(ip_frame)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(side=LEFT)

        # Port input
        port_frame = Frame(master)
        port_frame.pack(pady=2)
        Label(port_frame, text="Port:").pack(side=LEFT)
        self.port_entry = Entry(port_frame, width=6)
        self.port_entry.insert(0, "8080")
        self.port_entry.pack(side=LEFT)

        # Buttons
        self.start_button = Button(master, text="Start Server", command=self.start_server)
        self.start_button.pack(pady=5)

        self.stop_button = Button(master, text="Stop Server", command=self.stop_server, state=DISABLED)
        self.stop_button.pack(pady=5)

        self.console_button = Button(master, text="Open Console", command=self.open_console, state=DISABLED)
        self.console_button.pack(pady=5)

        self.url_label = Label(master, text="", fg="blue")
        self.url_label.pack(pady=10)

        self.server_thread = None
        self.console_window = None
        self.ip = "127.0.0.1"
        self.port = 8080

    def run_flask(self):
        app.run(host=self.ip, port=self.port, debug=False, use_reloader=False)

    def start_server(self):
        if not self.server_thread:
            self.ip = self.ip_entry.get().strip()
            try:
                self.port = int(self.port_entry.get().strip())
            except ValueError:
                print("[ERROR] Invalid port number, defaulting to 8080")
                self.port = 8080

            self.server_thread = threading.Thread(target=self.run_flask, daemon=True)
            self.server_thread.start()

            self.start_button.config(state=DISABLED)
            self.stop_button.config(state=NORMAL)
            self.console_button.config(state=NORMAL)

            self.url_label.config(text=f"Server running at http://{self.ip}:{self.port}/")
            webbrowser.open(f"http://{self.ip}:{self.port}/")

    def stop_server(self):
        print("[INFO] Server stopped (close GUI to fully exit).")
        self.master.quit()

    def open_console(self):
        if self.console_window:
            return  # already open

        self.console_window = Toplevel(self.master)
        self.console_window.title("Console Output")
        self.console_window.geometry("600x400")

        text_area = ScrolledText(self.console_window, wrap=WORD, state=NORMAL)
        text_area.pack(expand=True, fill=BOTH)

        # Redirect stdout/stderr so only requests are shown
        sys.stdout = ConsoleRedirector(text_area)
        sys.stderr = ConsoleRedirector(text_area)

        print("[INFO] Console opened. Waiting for connections...")

# === Main ===
if __name__ == "__main__":
    root = Tk()
    gui = ServerGUI(root)
    root.mainloop()
