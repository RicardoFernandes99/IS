import socket
import os

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 8080

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    while True:
        filename = input('Input filename you want to send: ')
        if not filename:  
            break
            
        try:
            with open(filename, "rb") as fi:
                data = fi.read()
                sock.sendall(data)
            
        except IOError:
            print('File not found')
        except Exception as e:
            print(f"Error sending file: {e}")
    
    sock.close()
