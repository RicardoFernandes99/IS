import os
from flask import Flask, render_template, request, redirect, url_for, flash, Response
import requests

REST_API_URL = os.getenv("REST_API_URL", "http://rest-api:8001")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "600"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")


def _fetch_documents():
    try:
        resp = requests.get(f"{REST_API_URL}/documents", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("documents", []), None
    except requests.RequestException as exc:
        return [], str(exc)


@app.route("/", methods=["GET"])
def index():
    documents, error = _fetch_documents()
    return render_template("index.html", documents=documents, error=error)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("csv_file")
    root_name = request.form.get("root_name") or "root"
    row_name = request.form.get("row_name") or "row"

    if not file:
        flash("Choose a CSV file before submitting.", "error")
        return redirect(url_for("index"))

    files = {"file": (file.filename or "upload.csv", file.stream, file.mimetype or "text/csv")}
    data = {"root_name": root_name, "row_name": row_name}

    try:
        resp = requests.post(
            f"{REST_API_URL}/upload-csv",
            files=files,
            data=data,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        flash(f"Uploaded successfully. Document ID: {payload.get('document_id')}")
    except requests.RequestException as exc:
        flash(f"Upload failed: {exc}", "error")

    return redirect(url_for("index"))


@app.route("/documents/<doc_id>", methods=["GET"])
def view_document(doc_id: str):
    target = f"{REST_API_URL}/documents/{doc_id}"
    try:
        resp = requests.get(target, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        flash(f"Unable to fetch document: {exc}", "error")
        return redirect(url_for("index"))

    if resp.status_code == 404:
        flash("Document not found", "error")
        return redirect(url_for("index"))

    if resp.status_code >= 400:
        flash(f"Error retrieving document: {resp.status_code}", "error")
        return redirect(url_for("index"))

    xml_text = resp.text
    return render_template("document.html", doc_id=doc_id, xml=xml_text)


@app.route("/documents/<doc_id>/download", methods=["GET"])
def download_document(doc_id: str):
    target = f"{REST_API_URL}/documents/{doc_id}"
    try:
        resp = requests.get(target, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            flash("Document not found", "error")
            return redirect(url_for("index"))
        resp.raise_for_status()
    except requests.RequestException as exc:
        flash(f"Unable to download document: {exc}", "error")
        return redirect(url_for("index"))

    filename = f"{doc_id}.xml"
    return Response(
        resp.text,
        mimetype="application/xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
