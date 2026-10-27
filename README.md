# 🌿 Driada Dietética y Herboristería

Prototipo web navegable desarrollado como Examen Parcial N° 1 de Práctica Profesionalizante I.

## 👥 Equipo

| Integrante | Rol | GitHub |
|---|---|---|
| Matías Villegas | Programador / Documentador| [@maty2399](https://github.com/maty2399) |
| Gabriela Nieva | Programadora / Diseñadora | [@GabrielaN0](https://github.com/GabrielaN0) |
| Daniela Pulin | Programadora / Documentadora | [@danielapulin](https://github.com/danielapulin) |

## 📄 Páginas

- **Inicio** → `principal/index.html`
- **Productos** → `productos/productos.html`
- **Contacto** → `contacto/contacto.html`

## 🛠️ Tecnologías

- HTML5
- CSS3
- Bootstrap 5.3
- Python y Flask
- SQLite

## 🚀 Ejecutar el servidor

Se necesita Python 3.10 o posterior.

```powershell
cd proyecto_driada
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Abrí `http://127.0.0.1:5000` en el navegador. La base SQLite se crea
automáticamente en `instance/driada.sqlite3` cuando inicia la aplicación.
El formulario de contacto guarda cada consulta en la tabla
`contact_messages`.
Para visualizar la base de datos se debe instalar la siguiente extencion: SQLite Browser

Para ejecutar las pruebas:

```powershell
python -m unittest discover -s tests
```

## 🏫 Institución

IES Manuel Belgrano · Tecnicatura Superior en Redes, Telecomunicaciones y Ciberseguridad · 2026
