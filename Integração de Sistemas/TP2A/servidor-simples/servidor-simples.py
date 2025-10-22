import socket
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hmac
import os

# Geração de uma chave secreta compartilhada (simulada aqui para exemplo)
chave_secreta = b'chave_secreta_compartilhada'

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '127.0.0.1'
porta = 5000
servidor.bind((host, porta))
servidor.listen(1)
print("Servidor esperando conexões em", host, ":", porta)

conexao, endereco = servidor.accept()
print("Conectado por", endereco)

while True:
    resposta = conexao.recv(1024)
    if not resposta:
        break

    # Separa a mensagem do HMAC
    partes = resposta.split(b"||")
    mensagem_decodificada = partes[0].decode('utf-8')
    hmac_recebido = partes[1]

    print("Recebido do cliente:", mensagem_decodificada)

    # Verifica o HMAC
    h = hmac.HMAC(chave_secreta, hashes.SHA256(), backend=default_backend())
    h.update(partes[0])
    try:
        h.verify(hmac_recebido)
        print("A autenticidade da mensagem foi verificada.")
    except Exception as e:
        print("Falha na verificação da autenticidade da mensagem.")

    dados_resposta = input("Digite uma mensagem: ")
    # Gera o HMAC para a resposta
    h = hmac.HMAC(chave_secreta, hashes.SHA256(), backend=default_backend())
    h.update(dados_resposta.encode())
    hmac_resposta = h.finalize()
    # Envia a resposta e o HMAC ao cliente
    conexao.send(dados_resposta.encode() + b"||" + hmac_resposta)

conexao.close()
