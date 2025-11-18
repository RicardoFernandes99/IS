from fastapi import FastAPI, File, UploadFile, HTTPException
import rpc_client
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), root_name: str = "root", row_name: str = "row"):
    csv_bytes = await file.read()

    # CSV → XML (RPC)
    xml_string = rpc_client.convert_csv(csv_bytes, root_name=root_name, row_name=row_name)

    # Insert into MongoDB (RPC)
    doc_id = rpc_client.insert_xml(xml_string)

    return {"status": "ok", "document_id": doc_id, "xml": xml_string}

@app.get("/documents")
def list_docs():
    return {"documents": rpc_client.list_documents()}

@app.get("/documents/{doc_id}", response_class=PlainTextResponse)
def get_doc(doc_id: str):
    xml = rpc_client.get_document(doc_id)
    if not xml:
        raise HTTPException(404, "Document not found")
    return xml