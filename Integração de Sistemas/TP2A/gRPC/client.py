import grpc
import file_transfer_pb2
import file_transfer_pb2_grpc

def file_chunks(filename):
    with open(filename, "rb") as f:
        while True:
            content = f.read(4096)
            if not content:
                break
            yield file_transfer_pb2.FileChunk(filename=filename, content=content)

def run():
    channel = grpc.insecure_channel('127.0.0.1:8080')
    stub = file_transfer_pb2_grpc.FileTransferStub(channel)

    filename = input("Enter filename to send: ")
    try:
        response = stub.UploadFile(file_chunks(filename))
        print(f"Server response: {response.message}")
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    run()
