import socket
import threading

host = '127.0.0.1'
port = 56000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((host,port))
    while True:
        msg = input()
        client.sendall(msg.encode())
        data = client.recv(1024)
        if data == b'quit':
            print('this is it, bye')
            client.close()
            break
        print(f'received "{data.decode()}" from server')


