from fastapi import FastAPI, Form, HTTPException
import rpc_client

app = FastAPI()

@app.post("/convert-stored-csv")
def convert_stored_csv(
    filename: str = Form(...),
    root_name: str = Form("root"),
    row_name: str = Form("row"),
):
    """Convert a CSV already in the shared data dir and save the XML alongside it."""
    if not filename:
        raise HTTPException(400, "Filename is required.")

    try:
        result = rpc_client.convert_csv_to_file(filename, root_name=root_name, row_name=row_name)
    except Exception as exc:
        raise HTTPException(400, f"Unable to convert stored CSV '{filename}': {exc}")

    return {"status": "ok", "source": filename, **result}

@app.post("/group-xml")
def group_xml(
    filename: str = Form(...),
    attr_tag: str = Form(...),
    filter_value: str = Form(None),
    row_tag: str = Form("row"),
    root_name: str = Form("root"),
    output_filename: str = Form(None),
):
    """Create a grouped/filtered XML + XSD from an existing XML in the shared data dir."""
    if not filename or not attr_tag:
        raise HTTPException(400, "filename and attr_tag are required.")

    try:
        result = rpc_client.group_xml_file(
            filename,
            attr_tag=attr_tag,
            filter_value=filter_value,
            row_tag=row_tag,
            root_name=root_name,
            output_filename=output_filename,
        )
    except Exception as exc:
        raise HTTPException(400, f"Unable to group XML '{filename}': {exc}")

    return {"status": "ok", "source": filename, **result}

@app.get("/xml-files")
def list_xml_files():
    return {"files": rpc_client.list_xml_files()}

@app.post("/import-xml")
def import_xml(
    filename: str = Form(...),
    collection: str = Form("Collection"),
):
    """Insert an XML file from the shared data dir into MongoDB."""
    if not filename:
        raise HTTPException(400, "Filename is required.")

    try:
        inserted_ids = rpc_client.insert_xml_file(filename, collection=collection)
    except Exception as exc:
        raise HTTPException(400, f"Unable to import XML '{filename}': {exc}")

    return {"status": "ok", "inserted_ids": inserted_ids, "inserted_count": len(inserted_ids)}

@app.post("/validate-xml")
def validate_xml(
    filename: str = Form(...),
    xsd_filename: str = Form(...),
):
    if not filename or not xsd_filename:
        raise HTTPException(400, "Filename and XSD filename are required.")

    try:
        ok, message = rpc_client.validate_xml(filename, xsd_filename)
    except Exception as exc:
        raise HTTPException(400, f"Validation failed: {exc}")

    status = "ok" if ok else "invalid"
    return {"status": status, "message": message}

@app.get("/documents")
def list_docs(collection: str = "Collection"):
    return {"documents": rpc_client.list_documents(collection=collection)}

@app.get("/documents/{doc_id}")
def get_doc(doc_id: str, collection: str = "Collection"):
    doc = rpc_client.get_document(doc_id, collection=collection)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc
