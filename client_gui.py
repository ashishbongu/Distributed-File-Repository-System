import tkinter as tk
from tkinter import messagebox, filedialog
import socket
import ssl
import os
from threading import Thread, Lock
import time

# --- Configuration ---
HOST = '127.0.0.1' # Server IP
PORT = 9998
CHUNK_SIZE = 1024 

class FileClientApp:
    def __init__(self, master):
        self.master = master
        master.title("Secure Client with Chat")
        master.geometry("1000x650")
        
        self.secure_sock = None
        self.is_authenticated = False
        self.lock = Lock() 
        
        self.context = ssl.create_default_context()
        self.context.check_hostname = False 
        self.context.verify_mode = ssl.CERT_NONE 

        self.setup_gui()

    def setup_gui(self):
        # --- Main Layout ---
        main_pane = tk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_pane)
        right_frame = tk.Frame(main_pane, bg="lightgray", width=350)
        
        main_pane.add(left_frame)
        main_pane.add(right_frame)

        # === LEFT FRAME (Files) ===
        
        # 1. Connection
        conn_frame = tk.LabelFrame(left_frame, text="Connection", padx=10, pady=10)
        conn_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(conn_frame, text="Host:").grid(row=0, column=0)
        self.host_entry = tk.Entry(conn_frame, width=15); self.host_entry.insert(0, HOST)
        self.host_entry.grid(row=0, column=1)

        tk.Label(conn_frame, text="User:").grid(row=0, column=2)
        self.user_entry = tk.Entry(conn_frame, width=10); self.user_entry.insert(0, "admin")
        self.user_entry.grid(row=0, column=3)
        
        tk.Label(conn_frame, text="Pass:").grid(row=0, column=4)
        self.pass_entry = tk.Entry(conn_frame, width=10, show="*"); self.pass_entry.insert(0, "secret123")
        self.pass_entry.grid(row=0, column=5)

        self.login_btn = tk.Button(conn_frame, text="Connect", command=self.start_login, bg="#4CAF50", fg="white")
        self.login_btn.grid(row=0, column=6, padx=10)

        self.status_lbl = tk.Label(conn_frame, text="Disconnected", fg="red")
        self.status_lbl.grid(row=1, columnspan=7, sticky="w")

        # 2. Server Files
        file_list_frame = tk.LabelFrame(left_frame, text="Server Files", padx=10, pady=10)
        file_list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.file_listbox = tk.Listbox(file_list_frame, height=10)
        self.file_listbox.pack(fill='both', expand=True, side=tk.LEFT)
        
        scrollbar = tk.Scrollbar(file_list_frame, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill='x', padx=10, pady=5)
        tk.Button(btn_frame, text="🔄 Refresh Files", command=self.req_list_files).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="⬇️ Download", command=self.start_download).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=self.start_delete, fg="red").pack(side=tk.LEFT, padx=5)

        # 3. Upload
        upload_frame = tk.LabelFrame(left_frame, text="Upload File", padx=10, pady=10)
        upload_frame.pack(fill='x', padx=10, pady=10)
        self.upload_entry = tk.Entry(upload_frame, width=30)
        self.upload_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(upload_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT)
        tk.Button(upload_frame, text="⬆️ Upload", command=self.start_upload, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=10)

        # === RIGHT FRAME (Logs & Chat) ===
        
        # LOGS SECTION (Top Half)
        tk.Label(right_frame, text="Global Activity Logs", bg="lightgray", font=("Arial", 9, "bold")).pack(pady=2)
        self.log_text = tk.Text(right_frame, width=30, height=15, state=tk.DISABLED, bg="#f0f0f0", font=("Consolas", 8))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # CHAT SECTION (Bottom Half)
        tk.Label(right_frame, text="Group Chat", bg="lightgray", font=("Arial", 9, "bold")).pack(pady=(10, 2))
        
        self.chat_display = tk.Text(right_frame, width=30, height=12, state=tk.DISABLED, bg="white", font=("Arial", 9))
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        chat_input_frame = tk.Frame(right_frame, bg="lightgray")
        chat_input_frame.pack(fill='x', padx=5, pady=5)
        
        self.chat_entry = tk.Entry(chat_input_frame)
        self.chat_entry.pack(side=tk.LEFT, fill='x', expand=True)
        self.chat_entry.bind("<Return>", lambda event: self.send_chat()) # Enter key to send
        
        tk.Button(chat_input_frame, text="Send", command=self.send_chat, bg="#008CBA", fg="white").pack(side=tk.RIGHT, padx=5)

    def log_gui(self, message):
        self.status_lbl.config(text=message, fg="blue")

    def browse_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.upload_entry.delete(0, tk.END)
            self.upload_entry.insert(0, f)

    # --- Networking Logic ---

    def start_login(self):
        t = Thread(target=self.connect)
        t.start()

    def connect(self):
        try:
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.secure_sock = self.context.wrap_socket(raw_sock, server_hostname=self.host_entry.get())
            self.secure_sock.settimeout(5) # Add timeout to prevent hanging
            self.secure_sock.connect((self.host_entry.get(), PORT))
            
            # Auth
            self.secure_sock.recv(1024) 
            creds = f"LOGIN {self.user_entry.get()} {self.pass_entry.get()}"
            self.secure_sock.send(creds.encode())
            
            resp = self.secure_sock.recv(1024).decode()
            if "200" in resp:
                self.is_authenticated = True
                self.log_gui("Connected!")
                self.status_lbl.config(fg="green")
                self.req_list_files()
                self.req_logs()
                
                # Start Auto-Refresh Thread for Chat
                Thread(target=self.start_auto_refresh, daemon=True).start()
            else:
                self.log_gui("Login Failed")
                self.secure_sock.close()
        except Exception as e:
            self.log_gui(f"Connection Error: {e}")

    def start_auto_refresh(self):
        """Background thread to poll for chat/logs updates every 2 seconds"""
        while self.is_authenticated:
            time.sleep(2)
            try:
                self.req_chat_update()
                self.req_logs()
            except:
                break

    # --- Commands ---

    def send_chat(self):
        msg = self.chat_entry.get()
        if not msg: return
        self.chat_entry.delete(0, tk.END)
        
        def task():
            try:
                with self.lock:
                    self.secure_sock.send(f"CHAT {msg}".encode())
                    self.secure_sock.recv(1024) # Wait for confirmation
                self.req_chat_update() # Immediate update
            except: pass
        Thread(target=task).start()

    def req_chat_update(self):
        if not self.is_authenticated: return
        with self.lock:
            try:
                self.secure_sock.send(b"GET_CHAT")
                resp = self.secure_sock.recv(4096).decode()
                if resp.startswith("200 CHAT"):
                    chat_data = resp[9:].split("||")
                    self.master.after(0, self.update_chat_ui, chat_data)
            except: pass

    def update_chat_ui(self, messages):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        for msg in messages:
            self.chat_display.insert(tk.END, msg + "\n")
        self.chat_display.see(tk.END) # Scroll to bottom
        self.chat_display.config(state=tk.DISABLED)

    def req_list_files(self):
        if not self.is_authenticated: return
        def task():
            try:
                with self.lock:
                    self.secure_sock.send(b"LIST")
                    resp = self.secure_sock.recv(4096).decode()
                if resp.startswith("200 LIST"):
                    files = resp[9:].split(",") if "EMPTY" not in resp else []
                    self.file_listbox.delete(0, tk.END)
                    for f in files: self.file_listbox.insert(tk.END, f)
            except: pass
        Thread(target=task).start()

    def req_logs(self):
        if not self.is_authenticated: return
        # Note: Threading handled by caller or auto-refresh
        with self.lock:
            try:
                self.secure_sock.send(b"LOGS")
                resp = self.secure_sock.recv(4096).decode()
                if resp.startswith("200 LOGS"):
                    logs = resp[9:].split("||")
                    self.master.after(0, self.update_logs_ui, logs)
            except: pass

    def update_logs_ui(self, logs):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        for l in logs: self.log_text.insert(tk.END, l + "\n")
        self.log_text.config(state=tk.DISABLED)

    def start_delete(self):
        sel = self.file_listbox.curselection()
        if not sel: return
        filename = self.file_listbox.get(sel[0])
        if not messagebox.askyesno("Confirm", f"Delete {filename}?"): return
        def task():
            with self.lock:
                self.secure_sock.send(f"DELETE {filename}".encode())
                self.secure_sock.recv(1024)
            self.req_list_files()
        Thread(target=task).start()

    def start_upload(self):
        path = self.upload_entry.get()
        if not path: return
        def task():
            filename = os.path.basename(path)
            with self.lock:
                self.secure_sock.send(f"PUT {filename}".encode())
                if "200 READY" in self.secure_sock.recv(1024).decode():
                    with open(path, 'rb') as f:
                        while True:
                            data = f.read(CHUNK_SIZE)
                            if not data: break
                            self.secure_sock.send(data)
                    self.secure_sock.send(b'FILE_END')
                    self.secure_sock.recv(1024)
                    self.log_gui(f"Uploaded {filename}")
            self.req_list_files()
        Thread(target=task).start()

    def start_download(self):
        sel = self.file_listbox.curselection()
        if not sel: return
        filename = self.file_listbox.get(sel[0])
        def task():
            with self.lock:
                self.secure_sock.send(f"GET {filename}".encode())
                if "200 READY" in self.secure_sock.recv(1024).decode():
                    self.secure_sock.send(b"ACK")
                    with open(f"DOWNLOADED_{filename}", 'wb') as f:
                        while True:
                            data = self.secure_sock.recv(CHUNK_SIZE)
                            if data.endswith(b'FILE_END'):
                                f.write(data[:-8]); break
                            f.write(data)
                    self.log_gui(f"Downloaded {filename}")
        Thread(target=task).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileClientApp(root)
    root.mainloop()