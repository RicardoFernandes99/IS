import socket, struct, json, time

HOST, PORT = "127.0.0.1", 5000

def build_framed(obj, flags=0):
    data = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    # O primeiro carácter ! diz “usa ordem de bytes de rede”, que é big endian.
    # B é “unsigned int” de 1 byte, serve para as flags.
    # I é “unsigned int” de 4 bytes, para o comprimento.
    header = struct.pack("!BI", flags, len(data))  # 1 byte flags + 4 bytes length
    return header + data

m1 = build_framed({"request_id": 1, "op": "sum", "params": {"a": 2, "b": 2}})
m2 = build_framed({"request_id": 2, "op": "sum", "params": {"a": 100, "b": 23}})

def soma(a, b):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
        c.connect((HOST, PORT))
        m3 = build_framed({"request_id": 3, "op": "sum", "params": {"a": a, "b": b}})
        c.sendall(m3)

        msg = c.recv(1024)
        result = int.from_bytes(msg, byteorder='big') 
        print("Resposta do servidor:", result)

if __name__ == "__main__":
    a = int(input("Insira um numero: "))
    b = int(input("Insira outro numero: "))
    soma(a, b)