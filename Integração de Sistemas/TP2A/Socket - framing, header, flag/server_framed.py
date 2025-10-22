import socket, struct, json, binascii

def recv_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError()
        buf += chunk
    print("Lendo o buffer...")
    return buf

def hexbytes(b):
    return binascii.hexlify(b).decode("ascii")

HOST, PORT = "0.0.0.0", 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print("Servidor escutando na porta ", PORT)
    conn, addr = s.accept()

    try:
        with conn:
            print("Ligado a ", addr)
            while True:
                header = recv_exact(conn, 5) # 5 bytes de header: 1 flag + 4 length
                flags = header[0]
                (length,) = struct.unpack("!I", header[1:5])

                print(f"Header bruto: {hexbytes(header)}  | flags={flags:08b}  length={length}")

                payload = recv_exact(conn, length)
                print(f"Payload {length} bytes: {hexbytes(payload[:min(16,len(payload))])}{'…' if len(payload)>16 else ''}")

                try:
                    msg = json.loads(payload.decode("utf-8"))
                    if msg.get("op") == "sum":
                        a = msg["params"]["a"]
                        b = msg["params"]["b"]
                        result = a + b
                        print(f"Resultado da soma {a} + {b} = {result}")
                except json.JSONDecodeError as e:
                    print("Erro a parsear JSON:", e)
                    continue
                conn.send(result.to_bytes(4, byteorder='big'))
                print("Mensagem:", msg)
    except ConnectionError:
        print("Cliente fechou a ligação. Fim.")