import socket
import os

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 8080
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(1)  
    
    print('Waiting for client connection...')
    
    conn, addr = sock.accept()
    print(f'Connected with client at {addr}')
        
    buffer_size = 4096  
    filename = 'output.csv'
    total_bytes = 0
    
    try:
        with open(filename, "wb") as fo:  
            while True:
                data = conn.recv(buffer_size)
                if not data:
                    break
                fo.write(data)

        
        print("\nFile transfer complete!")
        
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            print(f'File Saved')
        else:
            print('Error: File was not saved properly')
    
    except Exception as e:
        print(f"Error during file transfer: {e}")
    
    finally:
        conn.close()
