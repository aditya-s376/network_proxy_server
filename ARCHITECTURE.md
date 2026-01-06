# System Design Document

## 1. High-Level Architecture
The proxy operates as a Layer 7 intermediary for HTTP and a Layer 4 tunnel for HTTPS. It intercepts traffic, enforces policy, and relays data between Client and Server.



**Core Components:**
* **Listener:** Binds to the port and accepts incoming TCP connections.
* **Thread Manager:** A `ThreadPoolExecutor` that assigns a worker thread to each client connection.
* **Parser:** Extracts Method, Host, and Headers from the raw byte stream.
* **Blacklist Engine:** Performs $O(1)$ lookups to block restricted domains.
* **Traffic Handlers:**
    * **HTTP Bridge:** Parses and modifies headers for clear-text traffic.
    * **HTTPS Tunnel:** Uses `select()` for blind, bi-directional SSL/TLS piping.

## 2. Concurrency Model
**Model:** Pre-allocated Thread Pool (Default: 50 threads).

**Rationale:**
* **Resource Safety:** Caps the maximum number of active threads to prevent RAM exhaustion and OS thrashing during high load.
* **Efficiency:** Python releases the GIL during network I/O operations, making threads highly efficient for this network-bound application without the complexity of an asynchronous event loop.

## 3. Data Flow



**A. Incoming Request:**
1.  Client connects $\rightarrow$ Listener accepts $\rightarrow$ Dispatched to Worker Thread.
2.  Thread reads headers $\rightarrow$ Checks Blacklist.
    * *Match:* Return `403 Forbidden` and close.
    * *No Match:* Proceed.

**B. Outbound Forwarding:**
* **HTTP:** Proxy resolves IP, connects to remote server, sends request, and streams the response back to the client.
* **HTTPS (CONNECT):** Proxy establishes a connection to the remote server, returns `200 Connection Established`, and enters a `select()` loop to blindly pipe encrypted bytes between client and server.

## 4. Error Handling & Security

**Error Handling:**
* **Timeouts:** All socket operations use a strict `TIMEOUT` (10s) to prevent hanging threads.
* **Graceful Exit:** Captures `SIGINT` signals to close sockets and flush logs safely.

**Security:**
* **DoS Protection:** Enforces `MAX_CONTENT_LENGTH` on uploads and caps concurrent threads to prevent flooding.
* **Input Sanitization:** Handles malformed headers gracefully to prevent crashes.
* **Isolation:** Uses `SO_REUSEADDR` for reliable port rebinding.
