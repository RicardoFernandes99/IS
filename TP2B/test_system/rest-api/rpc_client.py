from xmlrpc.client import ServerProxy

rpc = ServerProxy("http://rpc-server:8000/RPC2", allow_none=True)

def convert_csv(csv_bytes, root_name="root", row_name="row"):
    return rpc.convert_csv(csv_bytes, root_name, row_name)

def insert_xml(xml_string):
    return rpc.insert_xml(xml_string)

def list_documents():
    return rpc.list_documents()

def get_document(doc_id):
    return rpc.get_document(doc_id)
