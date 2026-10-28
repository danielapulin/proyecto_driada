import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import create_app


class ContactFormTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "test.sqlite3"
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": str(database_path),
                "SECRET_KEY": "test-secret",
                "RATELIMIT_KEY_PREFIX": str(database_path),
            }
        )
        self.client = self.app.test_client()
        self.database_path = database_path

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_pages_are_served(self):
        for path in ("/", "/productos", "/contacto"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_homepage_includes_carousel_and_category_links(self):
        response = self.client.get("/")

        self.assertIn(b'id="carouselDriada"', response.data)
        self.assertIn(b"Productos naturales", response.data)
        self.assertIn(b"data-bs-slide-to=\"2\"", response.data)
        for category_anchor in (
            b"/productos#frutos-secos",
            b"/productos#harinas-cereales",
            b"/productos#suplementos",
        ):
            with self.subTest(category_anchor=category_anchor):
                self.assertIn(category_anchor, response.data)

    def test_product_search_script_is_served_separately(self):
        response = self.client.get("/productos")

        self.assertIn(b"/static/productos/buscador.js", response.data)
        script = self.client.get("/static/productos/buscador.js")
        try:
            self.assertEqual(script.status_code, 200)
            self.assertIn(b"searchInput.addEventListener", script.data)
        finally:
            script.close()

    def test_contact_page_loads_its_stylesheet_and_shared_navigation(self):
        response = self.client.get("/contacto")

        self.assertIn(b"static/contacto/formulario.css", response.data)
        self.assertIn(b"class=\"nav-link driada-link active\" href=\"/contacto\"", response.data)
        self.assertIn(b'name="csrf_token"', response.data)
        self.assertIn("Verificación: ¿cuánto es".encode(), response.data)
        with self.client.session_transaction() as browser_session:
            self.assertIn("captcha_id", browser_session)
            self.assertNotIn("captcha_answer", browser_session)
        stylesheet = self.client.get("/static/contacto/formulario.css")
        try:
            self.assertEqual(stylesheet.status_code, 200)
            self.assertIn(b".driada-hero", stylesheet.data)
        finally:
            stylesheet.close()

    def get_contact_form_data(self, **overrides):
        response = self.client.get("/contacto")
        token = re.search(
            rb'<input id="csrf_token" name="csrf_token" type="hidden" value="([^"]+)"',
            response.data,
        )
        self.assertIsNotNone(token)

        challenge = re.search(
            rb'<label for="captcha"[^>]*>[^<]*?([0-9]+) \+ ([0-9]+)',
            response.data,
        )
        self.assertIsNotNone(challenge)
        captcha_answer = str(int(challenge.group(1)) + int(challenge.group(2)))

        data = {
            "csrf_token": token.group(1).decode(),
            "nombre": "Gabriela Nieva",
            "email": "gabriela@example.com",
            "mensaje": "Quisiera consultar por semillas.",
            "captcha": captcha_answer,
        }
        data.update(overrides)
        return data

    def test_contact_message_is_saved(self):
        response = self.client.post("/contacto", data=self.get_contact_form_data())

        self.assertEqual(response.status_code, 302)
        with closing(sqlite3.connect(self.database_path)) as connection:
            message = connection.execute(
                "SELECT name, email, message FROM contact_messages"
            ).fetchone()

        self.assertEqual(
            message,
            (
                "Gabriela Nieva",
                "gabriela@example.com",
                "Quisiera consultar por semillas.",
            ),
        )

        response = self.client.get("/contacto", follow_redirects=True)
        self.assertIn(b"Mensaje enviado", response.data)

    def test_invalid_contact_message_is_not_saved(self):
        response = self.client.post(
            "/contacto",
            data=self.get_contact_form_data(email="correo-invalido"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"correo electr", response.data)
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM contact_messages"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_contact_form_rejects_missing_csrf_token(self):
        response = self.client.post(
            "/contacto",
            data={
                "nombre": "Gabriela",
                "email": "gabriela@example.com",
                "mensaje": "Consulta",
                "captcha": "10",
            },
        )

        self.assertEqual(response.status_code, 400)
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM contact_messages"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_contact_form_rejects_wrong_captcha_answer(self):
        response = self.client.post(
            "/contacto",
            data=self.get_contact_form_data(captcha="0"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("respuesta de verificación".encode(), response.data)
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM contact_messages"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_contact_form_limits_post_attempts(self):
        responses = []
        for _ in range(6):
            responses.append(
                self.client.post(
                    "/contacto",
                    data=self.get_contact_form_data(captcha="0"),
                )
            )

        self.assertTrue(all(response.status_code == 400 for response in responses[:5]))
        self.assertEqual(responses[5].status_code, 429)

    def test_security_headers_and_content_security_policy(self):
        response = self.client.get("/")

        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(
            response.headers["Referrer-Policy"],
            "strict-origin-when-cross-origin",
        )
        policy = response.headers["Content-Security-Policy"]
        self.assertIn("frame-ancestors 'none'", policy)
        self.assertIn("script-src 'self' https://cdn.jsdelivr.net", policy)
        self.assertNotIn("'unsafe-inline'", policy)

    def test_peewee_initialization_preserves_existing_contact_messages(self):
        legacy_database = Path(self.temporary_directory.name) / "legacy.sqlite3"
        with closing(sqlite3.connect(legacy_database)) as connection:
            connection.execute(
                """
                CREATE TABLE contact_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    message TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
                ("Matías", "matias@example.com", "Consulta anterior"),
            )
            connection.commit()

        create_app(
            {
                "TESTING": True,
                "DATABASE": str(legacy_database),
                "SECRET_KEY": "migration-test-secret",
                "RATELIMIT_KEY_PREFIX": str(legacy_database),
            }
        )

        with closing(sqlite3.connect(legacy_database)) as connection:
            saved_message = connection.execute(
                "SELECT name, email, message FROM contact_messages"
            ).fetchone()
        self.assertEqual(
            saved_message,
            ("Matías", "matias@example.com", "Consulta anterior"),
        )


if __name__ == "__main__":
    unittest.main()
