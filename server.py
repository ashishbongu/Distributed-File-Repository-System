import socket
import ssl
import os
import threading
import datetime
import time

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 9998
USERS = {"admin": "secret123", "guest": "welcome", "ashish": "pass",""
"taran":"pass","shreyas":"pass","yash":"pass"} 
SERVER_FILES_DIR = "server_files"
CHUNK_SIZE = 1024


activity_logs = []
chat_history = [] 

if not os.path.exists(SERVER_FILES_DIR): os.makedirs(SERVER_FILES_DIR)

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
try:
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
except FileNotFoundError:
    print("FATAL: server.crt or server.key not found.")
    exit()

def log_action(user, action):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {user}: {action}"
    activity_logs.append(entry)
    if len(activity_logs) > 50: activity_logs.pop(0)
    print(entry)

def handle_client(client_sock, addr):
    user = "Unknown"
    secure_sock = None
    try:
        secure_sock = context.wrap_socket(client_sock, server_side=True)
        print(f"✅ Secure connection from {addr}")

        # --- Auth ---
        secure_sock.send(b"AUTH_REQUIRED\n")
        raw_data = secure_sock.recv(1024).decode().strip()
        
        is_authenticated = False
        if raw_data.startswith("LOGIN"):
            try:
                _, u, p = raw_data.split()
                if USERS.get(u) == p:
                    is_authenticated = True
                    user = u
                    secure_sock.send(b"200 OK")
                    log_action("System", f"User '{user}' logged in.")
                else:
                    secure_sock.send(b"401 ERROR")
            except:
                secure_sock.send(b"400 ERROR")
        
        if not is_authenticated:
            secure_sock.close(); return

        # --- Loop ---
        while True:
            try:
                header = secure_sock.recv(1024).decode().strip()
                if not header: break 
                
                parts = header.split(" ", 1)
                command = parts[0].upper()

                if command == "LOGOUT":
                    secure_sock.send(b"200 BYE")
                    break

                elif command == "LIST":
                    files = os.listdir(SERVER_FILES_DIR)
                    file_str = ",".join(files) if files else "EMPTY"
                    secure_sock.send(f"200 LIST {file_str}".encode())

                elif command == "LOGS":
                    logs_str = "||".join(activity_logs) if activity_logs else "No activity yet."
                    secure_sock.send(f"200 LOGS {logs_str}".encode())

                elif command == "CHAT":
                    if len(parts) > 1:
                        chat_history.append(f"{user}: {parts[1]}")
                        if len(chat_history) > 50: chat_history.pop(0)
                        secure_sock.send(b"200 SENT")
                    else:
                        secure_sock.send(b"400 EMPTY")

                elif command == "GET_CHAT":
                    msgs_str = "||".join(chat_history[-20:]) if chat_history else "Welcome!"
                    secure_sock.send(f"200 CHAT {msgs_str}".encode())

                elif command == "DELETE":
                    if len(parts) > 1:
                        filepath = os.path.join(SERVER_FILES_DIR, parts[1])
                        if os.path.exists(filepath):
                            try:
                                os.remove(filepath)
                                log_action(user, f"Deleted {parts[1]}")
                                secure_sock.send(b"200 DELETED")
                            except PermissionError:
                                # Catch WinError 32 specifically here
                                secure_sock.send(b"400 ERROR: File is busy/in use")
                            except Exception as e:
                                secure_sock.send(f"400 ERROR: {str(e)}".encode())
                        else:
                            secure_sock.send(b"404 NOT FOUND")
                    else:
                        secure_sock.send(b"400 BAD REQUEST")

                elif command == "PUT":
                    if len(parts) > 1:
                        secure_sock.send(b"200 READY")
                        filepath = os.path.join(SERVER_FILES_DIR, parts[1])
                        try:
                            with open(filepath, 'wb') as f:
                                while True:
                                    data = secure_sock.recv(CHUNK_SIZE)
                                    if data.endswith(b'FILE_END'):
                                        f.write(data[:-8]); break
                                    f.write(data)
                            log_action(user, f"Uploaded {parts[1]}")
                            secure_sock.send(b"200 UPLOADED")
                        except PermissionError:
                             # Read remaining data to clear buffer even if file write failed
                            while True:
                                data = secure_sock.recv(CHUNK_SIZE)
                                if data.endswith(b'FILE_END'): break
                            secure_sock.send(b"400 ERROR: Server file locked")
                    else:
                        secure_sock.send(b"400 BAD REQUEST")

                elif command == "GET":
                    if len(parts) > 1:
                        filepath = os.path.join(SERVER_FILES_DIR, parts[1])
                        if os.path.exists(filepath):
                            secure_sock.send(b"200 READY")
                            secure_sock.recv(1024) # ACK
                            with open(filepath, 'rb') as f:
                                while True:
                                    data = f.read(CHUNK_SIZE)
                                    if not data: break
                                    secure_sock.send(data)
                            secure_sock.send(b'FILE_END')
                            log_action(user, f"Downloaded {parts[1]}")
                        else:
                            secure_sock.send(b"404 NOT FOUND")
                    else:
                        secure_sock.send(b"400 BAD REQUEST")
                
                else:
                    secure_sock.send(b"400 UNKNOWN COMMAND")

            except ConnectionResetError:
                break 
            except ssl.SSLEOFError:
                break 
            except Exception as e:
                print(f"⚠️ Command Error for {user}: {e}")
                # Don't break the loop, just print error and continue listening
                continue 

    except Exception as e:
        print(f"Auth/Conn Error: {e}")
    finally:
        if secure_sock: secure_sock.close()
        print(f"❌ Connection closed for {user}")

# --- Start Server ---
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse port immediately
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f"🔒 Server running on {HOST}:{PORT}")

while True:
    client_sock, addr = server_socket.accept()
    threading.Thread(target=handle_client, args=(client_sock, addr)).start()