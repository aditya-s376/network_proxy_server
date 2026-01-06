# High-Performance Multi-Threaded HTTP/HTTPS Proxy Server

A robust, lightweight, and concurrent web proxy server built from scratch in Python. This project demonstrates low-level network programming concepts including **TCP socket management**, **multi-threading**, **protocol parsing**, and **blind SSL/TLS tunneling**.

Designed to handle high concurrency with stability, featuring configurable access control and production-grade logging.

---

## 🚀 Key Features

* **Multi-Threaded Architecture:** Uses a custom `ThreadPoolExecutor` to handle up to 50+ concurrent connections without blocking.
* **HTTPS Support:** Implements the `CONNECT` method to establish blind tunnels for secure (SSL/TLS) traffic using `select()`-based I/O multiplexing.
* **Access Control System:** Includes an $O(1)$ complexity blacklist engine to block domains and subdomains efficiently.
* **Robust Protocol Parsing:** Handles edge cases like **Chunked Transfer Encoding** and standard `Content-Length` POST requests.
* **Security & Stability:**
    * Enforces strict upload limits to mitigate DoS attacks.
    * Implements graceful shutdown handling (`SIGINT`/`SIGTERM`).
    * Comprehensive logging with rotation policies to prevent disk exhaustion.
* **Configurable:** Fully driven by a `config.json` file for dynamic port, thread, and path management.

## 🛠️ Installation & Setup

### 1. Prerequisites
* Python 3.6+
* No external dependencies required (uses standard libraries: `socket`, `threading`, `json`, `logging`).

### 2. Project Structure
Ensure your directory looks like this:

/project-root
├── proxy.py                 # Main server script
├── config.json              # Configuration file
├── README.md                # This file
└── config/
    └── blocked_domains.txt  # List of blocked sites
### 3. Configuration
The server settings are loaded from `config.json`. You do not need to modify the Python code.

**`config.json` Example:**
json
{
    "server": {
        "host": "0.0.0.0",
        "port": 56000,
        "max_threads": 50,
        "socket_timeout": 10,
        "max_content_length_mb": 10
    },
    "paths": {
        "log_file": "proxy.log",
        "blacklist": "config/blocked_domains.txt"
    },
    "logging": {
        "level": "INFO",
        "max_file_size_mb": 5,
        "backup_count": 2
    }
}

