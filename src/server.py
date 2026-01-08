import socket
import concurrent.futures
import signal
import sys
import select
import logging
import os
from logging.handlers import RotatingFileHandler

# specifications of the server
HOST  = '0.0.0.0'
PORT = 56000
MAX_THREADS = 25
TIMEOUT = 10
# Get the path relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLACKLIST = os.path.join(os.path.dirname(SCRIPT_DIR), "config", "blocked_domains.txt")
MAX_CONTENT_LENGTH = 10*1024*1024

# logger setup
logger = logging.getLogger('ProxyServer')
logger.setLevel(logging.INFO)



# rotating_file_handler keeps the log file under 5 MB with two backups
file_handler = RotatingFileHandler('proxy.log', maxBytes=5*1024*1024, backupCount=2)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(file_formatter)

logger.addHandler(file_handler) #handles file writing
logger.addHandler(console_handler) #handles console printing




# loads the blacklist from the source txt file into a set for
# easy domain lookups
def load_blacklist(BLACKLIST):
    blacklist = set()
    try:
        with open(BLACKLIST, 'r') as f:
            for line in f:
                clean_line = line.strip().lower()
                if clean_line and not clean_line.startswith('#'):
                    blacklist.add(clean_line)
        print(f"[CONFIG] loaded the blacklist with {len(blacklist)} domains")
    except FileNotFoundError:
        print(f"Blacklist file not found at {BLACKLIST}")
    except Exception as err:
        print(f"Blacklist not loaded : {err}")
    return blacklist

the_blacklist = load_blacklist(BLACKLIST)

# returns boolean to determin if the domain is blocked or not
def is_domain_blocked(host , the_blacklist):
    for blocked_domain in the_blacklist:
        if host == blocked_domain: # exact match with blocked domain
            return True
        if host.endswith("."+blocked_domain): # in case of sub-domain, the dot prevents misidentification
            return True
    return False


# parses the HTTP request and returns the method, host, port, path
def parse_request(request_data_raw):
    decoded_req = request_data_raw.decode('utf-8', errors = 'ignore')
    lines = decoded_req.split("\r\n")

    request_line = lines[0] # first line contains method, host_port, path
    
    
    parts = request_line.split(" ")
    if len(parts) < 3: # invalid request
        return None, None, None, None
    
    method = parts[0]
    url = parts[1]

    # to exclude "https://" from the url
    if "://" in url:
        temp = url.split("://" , 1)
        url = temp[1]
    
    # to find the string containing the host and the port
    path_find = url.find("/")
    if path_find == -1:
        host_port = url
        path = "/"
    else:
        host_port = url[:path_find]
        path = url[path_find:]



    # to get the host and the port requested
    if ":" in host_port:
        host = host_port.split(":")[0]
        port = (host_port.split(":", 1)[1])
        port = int(port)
    else:
        host = host_port
        port = 80
    
    logger.info(f'[REQUEST] Method: {method} | Host = {host} | Port = {port}')

    
    return method , host , port, path
    



# handles requests with GET or POST method
def http_bridge(client_sock, host, port, request_data):

    # keeps count of transferred data
    total_bytes = 0 

    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_sock.settimeout(TIMEOUT)

    try:
        remote_sock.connect((host,port))
        remote_sock.sendall(request_data)

        while True: # loop recv to receive complete data
            response_packet = remote_sock.recv(4096)
            if len(response_packet) > 0:
                client_sock.sendall(response_packet)
                total_bytes += len(response_packet)
            else:
                break
        
        logger.info(f"[ALLOWED] {host}:{port} - {total_bytes} bytes transferred")
    except socket.error as err:
        logger.error(f"[ERROR] Bridge to {host} failed: {err}")
    finally:
        remote_sock.close()
        client_sock.close()




# handles requests with the CONNECT method / https requests
# uses select module to maintain unblocked transfer of data from and to both sockets
def https_tunnel(client_sock, remote_sock):
    sockets_to_watch = [client_sock, remote_sock]
    while True:
        readable, _, _ = select.select(sockets_to_watch, [] , [] , TIMEOUT)

        if not readable:
            break

        for sock in readable:
            try:
                data = sock.recv(4096)
                if not data:
                    return
                if sock is client_sock:
                    remote_sock.sendall(data)
                else:
                    client_sock.sendall(data)
            except socket.error:
                return
            
                


# handles the client
# receives the request and parses it further
# implements the blocklist check
# handles the POST method and body
def handle_client(client_sock):
    client_addr = client_sock.getpeername()

    request_data = b""

    # loop to receive complete data
    while b"\r\n\r\n" not in request_data: 
        packet = client_sock.recv(4096)
        if not packet:
            break
        request_data += packet
    
    if request_data:
        method, host, port , path = parse_request(request_data)
    if not host:
        client_sock.close()
        return
    host = host.lower()
    logger.info(f"[REQUEST] {client_addr[0]} requested {method} {host}:{port}")

    # blacklist check
    if is_domain_blocked(host , the_blacklist):
        logger.warning(f"[BLOCKED] {client_addr[0]} tried accessing {host}")
 
        forbidden_response = (
            b"HTTP/1.1 403 Forbidden\r\n"
            b"Content-Type: text/plain\r\n"
            b"Connection: close\r\n"
            b"\r\n"
            b"Error 403: The website you are trying to reach is blocked by this proxy."
        )
        client_sock.sendall(forbidden_response)
        client_sock.close()
        return
    
    # handles the case if the method is POST
    if method == "POST":
        
        content_length = 0
        # byte surgery to obtain the content-length from the request
        header_str = request_data.decode('utf-8', errors='ignore')
        for line in header_str.split("\r\n"):
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":")[1].strip())
                break
        
        # upload size check to prevent server crash in case of very large upload
        if content_length > MAX_CONTENT_LENGTH:
            logger.warning(f"[BLOCKED] Upload too large: {content_length} bytes")
            client_sock.sendall(b"HTTP/1.1 413 Payload Too Large\r\n\r\n")
            client_sock.close()
            return


        parts = request_data.split(b"\r\n\r\n" , 1)

        # to check how much of the body is already received
        current_body_len = len(parts[1]) if len(parts) > 1 else 0
        # loop to get complete body
        while(current_body_len < content_length):
            remaining  = content_length-current_body_len
            body_packet = client_sock.recv(min(remaining, 4096))
            if not body_packet:
                break
            request_data += body_packet
            current_body_len += len(body_packet)

    # need to start https_tunnel if method is CONNECT
    if method == "CONNECT":
        logger.info(f"[HTTPS] Tunnel starting for {host}:{port}")
        remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            remote_sock.connect((host,port))
            client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            https_tunnel(client_sock , remote_sock)
        except Exception as err:
            print(f"[HTTPS ERROR] {err}")
        finally:
            client_sock.close()
            remote_sock.close()
            return
    # need to start the http_bridge if the method is not CONNECT
    else:
        lines = request_data.split(b"\r\n")
        lines[0] = f"{method} {path} HTTP/1.1".encode()

        # byte surgery to change connection type to close connections after request completion
        for i in range(1,len(lines)):
            if lines[i].lower().startswith(b"connection:") or lines[i].lower().startswith(b"proxy-connection:"):
                lines[i] = b"Connection: close"


        final_request = b"\r\n".join(lines)
        http_bridge(client_sock , host , port , final_request)
    


# handles shutdown of server by tracking the keyboard interrupt
def handle_shutdown(signum, frame):
    print("\n[SHUTDOWN] Gracefully stopping the server...")
    logging.info("[SHUTDOWN] Server stopping...")
    sys.exit(0)

# starts the server
# uses the thread_pool_executor to handle multiple clients
# has limit of MAX_THREADS threads at once, rest go into waiting queue
def start_proxy_server():
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # prevents error in case of port already in use
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST,PORT))
    server.listen()
    logger.info(f'[INIT] Server started on {HOST}:{PORT}')
    with concurrent.futures.ThreadPoolExecutor(max_workers= MAX_THREADS) as exec:
        while True:
            client_sock, addr = server.accept()
            logger.debug(f'[CONN] Connection from {addr}')
            exec.submit(handle_client, client_sock)
            


if __name__ == "__main__":
    start_proxy_server()





        



