import sqlite3
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for


def get_database_connection(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path):
    database_file = Path(database_path)
    database_file.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(database_file))
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()
        del connection


def create_app(test_config=None):
    app = Flask(__name__)

    default_database = Path(__file__).resolve().parent / "instance" / "driada.sqlite3"
    app.config.from_mapping(
        SECRET_KEY="driada-secret-key",
        DATABASE=str(default_database),
    )

    if test_config:
        app.config.update(test_config)

    def get_db():
        if "db" not in g:
            g.db = get_database_connection(app.config["DATABASE"])
        return g.db

    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()
            del db

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/productos")
    def productos():
        return render_template("productos.html")

    @app.route("/contacto", methods=["GET", "POST"])
    def contacto():
        if request.method == "POST":
            nombre = (request.form.get("nombre") or "").strip()
            email = (request.form.get("email") or "").strip()
            mensaje = (request.form.get("mensaje") or "").strip()

            if not nombre or not email or not mensaje:
                return render_template(
                    "contacto.html",
                    error="Completa todos los campos para enviar tu consulta.",
                    form_data=request.form.to_dict(),
                ), 400

            if "@" not in email or "." not in email.split("@")[-1]:
                return render_template(
                    "contacto.html",
                    error="El correo electrónico es inválido.",
                    form_data=request.form.to_dict(),
                ), 400

            db = get_db()
            db.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
                (nombre, email, mensaje),
            )
            db.commit()

            flash("Mensaje enviado", "success")
            return redirect(url_for("contacto"))

        return render_template("contacto.html")

    with app.app_context():
        init_db(app.config["DATABASE"])

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)