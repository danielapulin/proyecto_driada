import hmac
import os
import secrets
import time
from pathlib import Path
from random import SystemRandom

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm, CSRFProtect
from dotenv import load_dotenv
from peewee import CharField, IntegerField, Model, SqliteDatabase, TextField
from wtforms import EmailField, StringField, TextAreaField
from wtforms.validators import Email, InputRequired, Length


class ContactForm(FlaskForm):
    nombre = StringField(
        validators=[
            InputRequired(message="Completa tu nombre."),
            Length(max=120, message="El nombre no puede superar los 120 caracteres."),
        ],
        filters=[lambda value: value.strip() if value else value],
    )
    email = EmailField(
        validators=[
            InputRequired(message="Completa tu correo electrónico."),
            Length(max=254, message="El correo no puede superar los 254 caracteres."),
            Email(message="El correo electrónico es inválido."),
        ],
        filters=[lambda value: value.strip() if value else value],
    )
    mensaje = TextAreaField(
        validators=[
            InputRequired(message="Completa tu consulta."),
            Length(max=2000, message="La consulta no puede superar los 2000 caracteres."),
        ],
        filters=[lambda value: value.strip() if value else value],
    )
    captcha = StringField(
        validators=[InputRequired(message="Resuelve la verificación.")],
        filters=[lambda value: value.strip() if value else value],
    )


def create_app(test_config=None):
    load_dotenv(Path(__file__).resolve().parent / ".env")
    app = Flask(__name__)
    default_database = Path(__file__).resolve().parent / "instance" / "driada.sqlite3"
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32),
        DATABASE=str(default_database),
        WTF_CSRF_ENABLED=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true",
        RATELIMIT_STORAGE_URI=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
        RATELIMIT_DEFAULT=[],
    )

    if test_config:
        app.config.update(test_config)

    database_path = app.config["DATABASE"]
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    database = SqliteDatabase(database_path, timeout=10)

    class ContactMessage(Model):
        name = TextField()
        email = TextField()
        message = TextField()

        class Meta:
            table_name = "contact_messages"

    class CaptchaChallenge(Model):
        id = CharField(max_length=64, primary_key=True)
        answer = CharField(max_length=2)
        expires_at = IntegerField()

        class Meta:
            table_name = "captcha_challenges"

    ContactMessage._meta.set_database(database)
    CaptchaChallenge._meta.set_database(database)

    with database:
        database.create_tables([ContactMessage, CaptchaChallenge])

    CSRFProtect(app)
    limiter = Limiter(key_func=get_remote_address, default_limits=[])
    limiter.init_app(app)

    @app.before_request
    def connect_contact_database():
        if request.endpoint == "contacto" and database.is_closed():
            database.connect()

    @app.teardown_appcontext
    def close_database(exception):
        if not database.is_closed():
            database.close()

    @app.after_request
    def add_security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    def issue_captcha():
        first = SystemRandom().randint(2, 9)
        second = SystemRandom().randint(2, 9)
        previous_challenge_id = session.pop("captcha_id", None)
        if previous_challenge_id:
            CaptchaChallenge.delete().where(
                CaptchaChallenge.id == previous_challenge_id
            ).execute()
        CaptchaChallenge.delete().where(
            CaptchaChallenge.expires_at <= int(time.time())
        ).execute()
        challenge_id = secrets.token_urlsafe(32)
        CaptchaChallenge.create(
            id=challenge_id,
            answer=str(first + second),
            expires_at=int(time.time()) + 600,
        )
        session["captcha_id"] = challenge_id
        return f"{first} + {second}"

    def verify_captcha(submitted_answer):
        challenge_id = session.pop("captcha_id", None)
        if not challenge_id:
            return False

        challenge = CaptchaChallenge.get_or_none(
            (CaptchaChallenge.id == challenge_id)
            & (CaptchaChallenge.expires_at > int(time.time()))
        )
        if challenge is None:
            return False

        expected_answer = challenge.answer
        challenge.delete_instance()
        return hmac.compare_digest(expected_answer, submitted_answer)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/productos")
    def productos():
        return render_template("productos.html")

    @app.route("/contacto", methods=["GET", "POST"])
    @limiter.limit("30 per minute", methods=["GET"])
    @limiter.limit("5 per minute", methods=["POST"])
    def contacto():
        form = ContactForm()
        captcha_question = issue_captcha() if request.method == "GET" else None
        status_code = 200

        if request.method == "POST":
            if form.validate_on_submit():
                submitted_answer = form.captcha.data or ""
                if verify_captcha(submitted_answer):
                    ContactMessage.create(
                        name=form.nombre.data,
                        email=form.email.data,
                        message=form.mensaje.data,
                    )
                    flash("Mensaje enviado", "success")
                    return redirect(url_for("contacto"))

                form.captcha.errors.append("La respuesta de verificación es incorrecta.")
            else:
                session.pop("captcha_id", None)
            status_code = 400
            captcha_question = issue_captcha()

        return (
            render_template(
                "contacto.html",
                form=form,
                captcha_question=captcha_question,
            ),
            status_code,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "").lower() == "true")
