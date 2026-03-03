import socket
import ssl
import os

# --- Configuration ---
HOST = '10.0.6.232'  # IMPORTANT: This must be the server's actual IP address!
PORT = 9999
CHUNK_SIZE = 1024 # Size of data chunks to send

# --- SSL Setup ---
context = ssl.create_default_context()

try:
    # Client must trust the server's certificate (server.crt)
    # The certificate must be present in the same directory as this script.
    context.load_verify_locations(cafile="server.crt")
except FileNotFoundError:
    print("FATAL: server.crt not found! Ensure it is in the same directory.")
    exit()
    
context.verify_mode = ssl.CERT_REQUIRED
# This is set to False because the certificate's Common Name (CN) is 'localhost', 
# but the connection IP is '10.0.2.92'.
context.check_hostname = False 

# --- Helper Functions ---

def upload_file(secure_sock, filename):
    """Sends a file to the server using the PUT command."""
    try:
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return

        # 1. Send the PUT command
        secure_sock.send(f"PUT {filename}".encode())
        
        # 2. Wait for server to be ready
        ready_response = secure_sock.recv(1024).decode().strip()
        if not ready_response.startswith("200 READY"):
            print(f"Server refused upload: {ready_response}")
            return
            
        # 3. Send the file data in chunks
        with open(filename, 'rb') as f:
            while True:
                data = f.read(CHUNK_SIZE)
                if not data:
                    break
                secure_sock.send(data)

        # 4. Send termination marker
        secure_sock.send(b'FILE_END')
        print(f"Finished sending {filename}. Waiting for confirmation...")
        
        # 5. Receive final confirmation
        confirmation = secure_sock.recv(1024).decode().strip()
        print(f"Server: {confirmation}")

    except Exception as e:
        print(f"❌ Upload failed: {e}")


def download_file(secure_sock, filename):
    """Receives a file from the server using the GET command."""
    try:
        # 1. Send the GET command
        secure_sock.send(f"GET {filename}".encode())
        
        # 2. Receive server response (ready or error)
        response_header = secure_sock.recv(1024).decode().strip()
        print(f"Server response: {response_header}")

        if response_header.startswith("200 READY"):
            
            # Send acknowledgement to start the transfer
            secure_sock.send(b"ACK_READY")
            
            output_path = f"DOWNLOADED_{filename}"
            print(f"Receiving file and saving as {output_path}...")
            
            with open(output_path, 'wb') as f:
                while True:
                    file_chunk = secure_sock.recv(1024)
                    if file_chunk == b'FILE_END':
                        break
                    f.write(file_chunk)
            
            print(f"✅ Download complete: '{output_path}' saved.")
        
        elif response_header.startswith("404 ERROR"):
            print("Download failed: File not found on server.")

    except Exception as e:
        print(f"❌ Download failed: {e}")


# --- Main Client Logic ---
client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # 3. WRAP the socket with SSL and connect
    secure_sock = context.wrap_socket(client_sock, server_hostname=HOST)
    secure_sock.connect((HOST, PORT))
    
    print(f"✅ Secure connection established with {HOST}:{PORT}!")
    
    # 4. Authentication Logic
    initial_prompt = secure_sock.recv(1024).decode()
    print(f"Server: {initial_prompt.strip()}")

    user = input("Username: ")
    password = input("Password: ")

    login_command = f"LOGIN {user} {password}"
    secure_sock.send(login_command.encode())

    auth_response = secure_sock.recv(1024).decode().strip()
    print(f"Server: {auth_response}")

    if auth_response.startswith("200 OK"):
        print("\n--- Login Success! Commands: PUT <file>, GET <file>, LOGOUT ---")
        
        while True:
            cmd = input("Command > ").strip()
            
            if not cmd:
                continue

            parts = cmd.upper().split()
            command = parts[0]

            if command == "LOGOUT":
                secure_sock.send(cmd.encode())
                response = secure_sock.recv(1024).decode().strip()
                print(f"Server: {response}")
                break

            elif command == "PUT":
                try:
                    _, filename = cmd.split()
                    upload_file(secure_sock, filename)
                except ValueError:
                    print("Usage: PUT <filename>")
                continue
                
            elif command == "GET":
                try:
                    _, filename = cmd.split()
                    download_file(secure_sock, filename)
                except ValueError:
                    print("Usage: GET <filename>")
                continue

            else:
                # Send unknown command to server
                secure_sock.send(cmd.encode())
                response = secure_sock.recv(1024).decode().strip()
                print(f"Server: {response}")
    
    # 5. Close the connection
    secure_sock.close()

except ConnectionRefusedError:
    print("❌ Connection Error: Ensure the server is running!")
except ssl.SSLCertVerificationError as e:
    print(f"❌ SSL Error: Could not verify server certificate. {e}")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")