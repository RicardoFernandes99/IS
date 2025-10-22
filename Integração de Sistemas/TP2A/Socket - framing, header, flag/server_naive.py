import socket, json

HOST, PORT = "0.0.0.0", 5000
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)

    print("Servidor escutando na porta ", PORT)

    conn, addr = s.accept()
    
    with conn:
        print("Ligado a ", addr)
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                break
            print("Recebido bruto: ", chunk) 
            try:
                msg = json.loads(chunk.decode("utf-8"))
                print("JSON OK:\n", msg)
            except Exception as e:
                print("Falhou a parsear JSON: ", e)

#### TCP é stream de bytes, não de mensagens!!!!!!!