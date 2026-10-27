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

    def test_contact_message_is_saved(self):
        response = self.client.post(
            "/contacto",
            data={
                "nombre": "Gabriela Nieva",
                "email": "gabriela@example.com",
                "mensaje": "Quisiera consultar por semillas.",
            },
        )

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
            data={
                "nombre": "Gabriela",
                "email": "correo-invalido",
                "mensaje": "Consulta",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"correo electr", response.data)
        with closing(sqlite3.connect(self.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM contact_messages"
            ).fetchone()[0]
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
