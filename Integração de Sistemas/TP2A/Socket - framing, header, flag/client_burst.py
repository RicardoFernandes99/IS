import socket, json, time

HOST, PORT = "127.0.0.1", 5000

m1 = json.dumps({"op":"sum","a":2,"b":2}).encode()
m2 = json.dumps({"op":"sum","a":100,"b":23}).encode()

cut = len(m1) // 2

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(m1[:cut])           # meia mensagem 1
    time.sleep(0.01)              # pequeno intervalo para aumentar a probabilidade de flush
    s.sendall(m1[cut:])           # segunda metade da mensagem 1
    s.sendall(m2)                 # mensagem 2 inteira logo a seguir