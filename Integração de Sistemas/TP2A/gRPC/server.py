import grpc
from concurrent import futures
import file_transfer_pb2
import file_transfer_pb2_grpc
import os

class FileTransferServicer(file_transfer_pb2_grpc.FileTransferServicer):
    def UploadFile(self, request_iterator, context):
        filename = None
        with open("received_file", "wb") as f:
            for chunk in request_iterator:
                if not filename:
                    filename = chunk.filename
                    print(f"Receiving file: {filename}")
                f.write(chunk.content)
        file_saved = os.path.exists("received_file") and os.path.getsize("received_file") > 0
        message = f"File '{filename}' received successfully!" if file_saved else "Error saving file"
        return file_transfer_pb2.UploadStatus(message=message, success=file_saved)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    file_transfer_pb2_grpc.add_FileTransferServicer_to_server(FileTransferServicer(), server)
    server.add_insecure_port('[::]:8080')
    server.start()
    print("Server is listening on port 8080...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
