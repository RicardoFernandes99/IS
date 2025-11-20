import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, Response
import requests

REST_API_URL = os.getenv("REST_API_URL", "http://rest-api:8001")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "600"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")


def _fetch_documents(collection: str):
    try:
        resp = requests.get(
            f"{REST_API_URL}/documents",
            params={"collection": collection},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("documents", []), None
    except requests.RequestException as exc:
        return [], str(exc)

def _fetch_xml_files():
    try:
        resp = requests.get(f"{REST_API_URL}/xml-files", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("files", []), None
    except requests.RequestException as exc:
        return [], str(exc)

def _validate_xml(filename: str, xsd_filename: str):
    try:
        resp = requests.post(
            f"{REST_API_URL}/validate-xml",
            data={"filename": filename, "xsd_filename": xsd_filename},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


@app.route("/", methods=["GET"])
def index():
    collection = request.args.get("collection") or "Collection"
    documents, error = _fetch_documents(collection)
    xml_files, xml_error = _fetch_xml_files()
    return render_template(
        "index.html",
        documents=documents,
        error=error,
        xml_files=xml_files,
        xml_error=xml_error,
        collection=collection,
    )


@app.route("/upload", methods=["POST"])
def upload():
    filename = request.form.get("filename", "").strip()
    root_name = request.form.get("root_name") or "root"
    row_name = request.form.get("row_name") or "row"

    if not filename:
        flash("Enter a CSV filename located in the shared data directory.", "error")
        return redirect(url_for("index"))

    data = {
        "filename": filename,
        "root_name": root_name,
        "row_name": row_name,
    }

    try:
        resp = requests.post(
            f"{REST_API_URL}/convert-stored-csv",
            data=data,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        flash(f"Converted {filename} to XML file: {payload.get('xml_file')}")
    except requests.RequestException as exc:
        flash(f"Conversion failed: {exc}", "error")

    return redirect(url_for("index"))


@app.route("/import-xml", methods=["POST"])
def import_xml():
    filename = request.form.get("xml_filename", "").strip()
    collection = request.form.get("collection") or "Collection"
    if not filename:
        flash("Choose an XML filename to import.", "error")
        return redirect(url_for("index", collection=collection))

    data = {"filename": filename, "collection": collection}
    try:
        resp = requests.post(
            f"{REST_API_URL}/import-xml",
            data=data,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        flash(f"Imported {filename}. Inserted rows: {payload.get('inserted_count')}")
    except requests.RequestException as exc:
        flash(f"Import failed: {exc}", "error")

    return redirect(url_for("index", collection=collection))


@app.route("/validate-xml", methods=["POST"])
def validate_xml():
    filename = request.form.get("xml_filename", "").strip()
    if not filename:
        flash("Provide an XML filename.", "error")
        return redirect(url_for("index"))
    xsd_filename = filename.replace(".xml", ".xsd")

    result, error = _validate_xml(filename, xsd_filename)
    if error:
        flash(f"Validation failed: {error}", "error")
    else:
        status = result.get("status")
        message = result.get("message")
        if status == "ok":
            flash(f"Validation succeeded: {message}")
        else:
            flash(f"Validation failed: {message}", "error")

    return redirect(url_for("index"))


@app.route("/documents/<doc_id>", methods=["GET"])
def view_document(doc_id: str):
    collection = request.args.get("collection") or "rows"
    target = f"{REST_API_URL}/documents/{doc_id}"
    try:
        resp = requests.get(target, params={"collection": collection}, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        flash(f"Unable to fetch document: {exc}", "error")
        return redirect(url_for("index", collection=collection))

    if resp.status_code == 404:
        flash("Document not found", "error")
        return redirect(url_for("index"))

    if resp.status_code >= 400:
        flash(f"Error retrieving document: {resp.status_code}", "error")
        return redirect(url_for("index"))

    doc_json = resp.json()
    return render_template("document.html", doc_id=doc_id, doc=doc_json, collection=collection)


@app.route("/documents/<doc_id>/download", methods=["GET"])
def download_document(doc_id: str):
    collection = request.args.get("collection") or "rows"
    target = f"{REST_API_URL}/documents/{doc_id}"
    try:
        resp = requests.get(target, params={"collection": collection}, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            flash("Document not found", "error")
            return redirect(url_for("index", collection=collection))
        resp.raise_for_status()
    except requests.RequestException as exc:
        flash(f"Unable to download document: {exc}", "error")
        return redirect(url_for("index", collection=collection))

    doc_json = resp.json()
    filename = f"{doc_id}.json"
    return Response(
        json.dumps(doc_json, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
