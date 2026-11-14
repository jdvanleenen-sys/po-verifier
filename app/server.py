"""The phone app's web server: routes only. Every route reads the house's state from the folder's
files, does one step, and answers in plain words. Start it on the laptop that holds the folder:

    .venv\\Scripts\\python app/server.py --folder "<the folder>"

It prints the link to open on the phone (same Wi-Fi). The link carries a key; without it the app
answers nothing, so someone else on the Wi-Fi cannot open a house."""
import argparse
import re
import secrets
import socket
import sys
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file, send_from_directory

import house_view
import lock
import request_pdf
import steps
from folder import Folder
from jobs import Jobs

STATIC = Path(__file__).resolve().parent / "static"
HOUSE = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")
COOKIE = "po_checker_key"


def create_app(folder, key):
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 120 * 1024 * 1024
    jobs = Jobs(folder)

    def body():
        return request.get_json(silent=True) or {}

    def house_or_404(house):
        if not HOUSE.match(house) or not folder.stage("01 intake", house).is_dir():
            abort(404)
        return house

    @app.before_request
    def need_key():
        given = request.args.get("k") or request.cookies.get(COOKIE)
        if not secrets.compare_digest(str(given or ""), key):
            return "Open the link the laptop printed when the app started.", 403

    @app.after_request
    def keep_key(response):
        if request.args.get("k") == key:
            response.set_cookie(COOKIE, key, max_age=60 * 60 * 24 * 30, samesite="Strict", httponly=True)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(steps.Stopped)
    @app.errorhandler(lock.Refused)
    @app.errorhandler(ValueError)
    def plain_words(err):
        return jsonify({"error": str(err)}), 400

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html")

    @app.get("/static/<path:name>")
    def static_file(name):
        return send_from_directory(STATIC, name)

    @app.get("/api/houses")
    def list_houses():
        return jsonify(house_view.summary(folder, jobs))

    @app.post("/api/hold")
    def hold():
        files = lambda field: [(f.filename, f.read()) for f in request.files.getlist(field) if f.filename]
        held = lock.hold(folder, request.form.get("address"), request.form.get("measured"),
                         request.form.get("covers") == "yes", files("pos"), files("notes"))
        return jsonify(held)

    @app.post("/api/lock")
    def lock_and_read():
        house = lock.lock(folder, body().get("id"), body().get("answers") or {})
        steps.start_read(folder, jobs, house)
        return jsonify({"house": house})

    @app.get("/api/house/<house>")
    def show(house):
        return jsonify(house_view.detail(folder, jobs, house_or_404(house)))

    @app.post("/api/house/<house>/<action>")
    def act(house, action):
        house_or_404(house)
        done = house_view.act(folder, jobs, house, action, body())
        return jsonify({"ok": True, **(done or {})})

    @app.get("/api/house/<house>/pdf")
    def pdf(house):
        house_or_404(house)
        path = request_pdf.numbered(folder, house) if request.args.get("numbered") else \
            request_pdf.draft(folder, house)["pdf"]
        if path is None:
            abort(404)
        return send_file(path, mimetype="application/pdf", download_name=path.name)

    @app.get("/api/house/<house>/notes/<int:n>")
    def notes_photo(house, n):
        photos = house_view.note_photos(folder, house_or_404(house))
        if not 0 <= n < len(photos):
            abort(404)
        return send_file(photos[n])

    return app


def lan_address():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def main(argv=None):
    parser = argparse.ArgumentParser(description="PO Checker phone app")
    parser.add_argument("--folder", required=True)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    folder = Folder(args.folder)
    key = secrets.token_urlsafe(9)
    print(f"Folder: {folder.root}")
    print(f"On the phone (same Wi-Fi), open:  http://{lan_address()}:{args.port}/?k={key}")
    create_app(folder, key).run(host="0.0.0.0", port=args.port, threaded=True)


if __name__ == "__main__":
    sys.exit(main())
