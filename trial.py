import sys
import socket
import threading
import time
import concurrent.futures


def parse_request(request_data_raw):
    decoded_req = request_data_raw.decode('utf-8' errors = 'ignore')
    lines = decoded_req.split("\r\n")

    request_line = lines[0]
    
    
    parts = request_line.split(" ")
    if len(parts) < 3:
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
    
    print(f'[REQUEST] Method: {method} | Host = {host} | Port = {port}')

    
    return method , host , port, path


        
        





