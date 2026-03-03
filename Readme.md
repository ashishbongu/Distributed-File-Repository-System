# 🗄️ Distributed File Repository System

A secure, multi-client file management system with real-time chat capabilities built on a Client-Server architecture.

![Demo](image1.png)
![Demo](image2.png)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📤 **Upload** | Securely upload files to a central server with chunked transfer |
| 📥 **Download** | Download files from the server with encrypted transmission |
| 🗑️ **Delete** | Remove files from the server repository |
| 💬 **Real-Time Chat** | Store-and-forward messaging system between users |
| 👥 **Multi-User Support** | Concurrent connections with multi-threading |
| 🔐 **Security** | SSL/TLS encryption, certificate-based authentication |
| 🖥️ **GUI** | User-friendly graphical interface |

---

## 🏗️ System Architecture

### Client-Server Model

The system operates on a **Client-Server Architecture** where:
- **Server**: Acts as a "Private Cloud" running on a specific IP and TCP port (9998). It is **concurrent** - handles multiple users simultaneously without blocking.
- **Clients**: User-facing GUI applications that initiate requests. They don't store data permanently - they only **push** (upload) or **pull** (download) data from the central server.

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│   Client A  │◄───────►│   Server (Cloud)  │◄───────►│  Client B   │
│   (GUI)     │         │  10.0.14.87:9998  │         │    (GUI)    │
└─────────────┘         └──────────────────┘         └─────────────┘
                                                        │
                                              ┌─────────▼─────────┐
                                              │    Client C       │
                                              │    (GUI)          │
                                              └───────────────────┘
```

---

## 🔒 Security Layer

### SSL/TLS Handshake

1. **Socket Creation**: Standard TCP stream socket ensures reliable data delivery
2. **TLS Handshake**: Server presents its digital certificate (`server.crt`)
3. **Encrypted Tunnel**: All data (passwords, files, chat) is encrypted before transmission

```
Client                            Server
  │                                  │
  │───── TCP Connection ─────────────►│
  │                                  │
  │───── TLS Handshake ─────────────►│
  │    (Certificate Exchange)        │
  │◄───── Encrypted Tunnel ──────────│
  │                                  │
  │───── Encrypted Data ────────────►│
  │◄───── Encrypted Response ────────│
```

---

## 🔑 Authentication

The server implements session-based authentication:

1. Client establishes secure connection
2. Client sends: `LOGIN <username> <password>`
3. Server validates credentials against internal dictionary
4. Success → `200 OK` + `is_authenticated = True`
5. Failure → Connection rejected

Only authenticated users can access the `server_files` directory.

---

## 🧵 Multi-Threading

The server uses Python's `threading` module for concurrent user handling:

- **Main Server Loop**: Listens for new connections
- **Per-Client Thread**: Spawns `handle_client` thread for each new user
- **Result**: User A can upload, User B can delete, User C can chat - **simultaneously!**

```
                    ┌─────────────────┐
                    │  Main Server    │
                    │     Loop        │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │  Thread 1  │   │  Thread 2   │   │  Thread 3   │
    │ (User A)   │   │ (User B)    │   │ (User C)    │
    │  UPLOAD    │   │   DELETE    │   │    CHAT     │
    └────────────┘   └─────────────┘   └─────────────┘
```

---

## 📦 File Transfer Mechanics

### Chunking Technique

Files are transferred in **1KB blocks** to avoid loading entire files into RAM:

1. Client sends: `PUT <filename>`
2. Server opens file and responds: `READY`
3. Client loop: Read 1KB → Encrypt → Send → Repeat
4. Client sends: `FILE_END` marker
5. Server decrypts and writes each chunk to disk

```
┌─────────────────────────────────────────────────────┐
│                   FILE TRANSFER                      │
├─────────────────────────────────────────────────────┤
│  Client                                              │
│    │                                                │
│    ├──► READ 1KB ───► ENCRYPT ───► SEND             │
│    │                                                │
│    ├──► READ 1KB ───► ENCRYPT ───► SEND             │
│    │                                                │
│    └──► SEND FILE_END ─────────────────────────────►│
│                                                      │
│  Server                                              │
│    │                                                │
│    ├──◄ RECEIVE ───► DECRYPT ───► WRITE to disk    │
│    │                                                │
│    ├──◄ RECEIVE ───► DECRYPT ───► WRITE to disk    │
│    │                                                │
│    └──◄ FILE_END                                    │
└─────────────────────────────────────────────────────┘
```

---

## 💬 Chat System: Store-and-Forward

### Polling Mechanism

Since TCP is a single data stream, the server acts as a temporary mailbox:

1. **User A** sends a message → Stored in `chat_history` list
2. **User B** polls every 2 seconds: `GET_CHAT`
3. Server responds with latest chat history
4. Result: **Real-time chat illusion** without complex async protocols

```
┌─────────┐     Polls every 2s      ┌─────────┐
│ Client A│◄────────────────────────►│ Server  │
│         │    "Any new messages?"  │         │
└─────────┘                         └────┬────┘
                                         │
                            ┌────────────┴────────────┐
                            │   chat_history: []      │
                            │   [msg1, msg2, msg3...] │
                            └─────────────────────────┘
                                         │
┌─────────┐     Receives                 │
│ Client B│◄─────────────────────────────┘
│         │    [msg1, msg2, msg3...]
└─────────┘
```

---

## 🔒 Client-Side Concurrency: Thread Lock (Mutex)

The Client GUI handles two simultaneous operations:
1. **Background**: Auto-refreshes chat every 2 seconds
2. **Foreground**: Waiting for user to click "Upload"

### The Problem
If both happen simultaneously, data streams could mix → **Protocol Violation**

### The Solution: Thread Lock (Mutex)
- Acts like a "talking stick"
- Before sending data, a function must **acquire the Lock**
- If Upload holds the Lock, Chat Refresh **waits** until upload finishes
- **Prevents crashes during simultaneous operations**

---

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- Required libraries: `socket`, `ssl`, `threading`, `tkinter`

### Running the Server

```bash
python server.py
```

The server will start on `0.0.0.0:9998` and use SSL/TLS encryption.

### Running the Client

```bash
python client_gui.py
```

Connect to the server using the server's IP address and port 9998.

---

## 📁 Project Structure

```
Distributed-File-Repository-System/
├── client_gui.py          # Client GUI application
├── server.py              # Server application
├── server.crt            # SSL certificate
├── server.key            # SSL private key
├── server_files/         # Repository directory for files
├── image1.png            # Demo screenshot 1
├── image2.png            # Demo screenshot 2
└── Readme.md             # This file
```

---

## 🔧 Supported Commands

| Command | Description |
|---------|-------------|
| `LOGIN <user> <pass>` | Authenticate with server |
| `PUT <filename>` | Upload a file |
| `GET <filename>` | Download a file |
| `DELETE <filename>` | Delete a file from server |
| `LIST` | List all files on server |
| `GET_CHAT` | Retrieve chat history |
| `SEND_CHAT <msg>` | Send a chat message |

---

## 🛡️ Security Features

- ✅ **TLS/SSL Encryption** - All data encrypted in transit
- ✅ **Certificate-Based Authentication** - Server identity verification
- ✅ **Session Management** - Authentication state tracking
- ✅ **Per-User Thread Isolation** - Secure multi-user environment

---

## 📊 Technical Highlights

- **Protocol**: TCP Stream Sockets with SSL/TLS
- **Port**: 9998
- **Chunk Size**: 1024 bytes (1KB)
- **Chat Poll Interval**: 2 seconds
- **Concurrency**: Multi-threaded (one thread per client)

---

*Built with ❤️ using Python*

