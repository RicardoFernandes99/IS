import socket
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hmac
import os

# A chave secreta compartilhada deve ser a mesma no cliente e servidor
chave_secreta = b'chave_secreta_compartilhada'

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = 'localhost'
porta = 5000
cliente.connect((host, porta))

while True:
    mensagem = input("Digite uma mensagem: ")
    # Gera o HMAC para a mensagem
    h = hmac.HMAC(chave_secreta, hashes.SHA256(), backend=default_backend())
    h.update(mensagem.encode())
    hmac_mensagem = h.finalize()
    # Envia a mensagem e o HMAC ao servidor
    cliente.send(mensagem.encode() + b"||" + hmac_mensagem)
    # Recebe a resposta e o HMAC do servidor
    resposta = cliente.recv(1024)
    partes = resposta.split(b"||")
    mensagem_resposta = partes[0].decode('utf-8')
    hmac_resposta = partes[1]

    print("Recebido do servidor:", mensagem_resposta)

    # Verifica o HMAC da resposta
    h = hmac.HMAC(chave_secreta, hashes.SHA256(), backend=default_backend())
    h.update(partes[0])
    try:
        h.verify(hmac_resposta)
        print("A autenticidade da resposta foi verificada.")
    except Exception as e:
        print("Falha na verificação da autenticidade da resposta.", e)

cliente.close()
