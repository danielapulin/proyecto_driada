# 🌿 Driada Dietética y Herboristería

Prototipo web navegable desarrollado como Examen Parcial N° 2 de Práctica Profesionalizante I.

## 👥 Equipo

| Integrante | Rol | GitHub |
|---|---|---|
| Matías Villegas | Programador | [@maty2399](https://github.com/maty2399) |
| Gabriela Nieva | Programadora / Diseñadora | [@GabrielaN0](https://github.com/GabrielaN0) |
| Daniela Pulin | Programadora | [@danielapulin](https://github.com/danielapulin) |
| Belén Mansilla | Programadora / Documentadora | [@bmansillaroque-hash](https://github.com/bmansillaroque-hash) |
## 📄 Páginas

- **Inicio** → `http://127.0.0.1:5000/`
- **Productos** → `http://127.0.0.1:5000/productos`
- **Contacto** → `http://127.0.0.1:5000/contacto`

Las páginas se renderizan desde `templates/`; los archivos de `static/` contienen
hojas de estilo e imágenes.

## 🛠️ Tecnologías

- HTML5
- CSS3
- Bootstrap 5.3
- Python y Flask
- SQLite

## 🚀 Instalación y ejecución

Se necesita Python 3.10 o posterior y Git. En Windows, abrí PowerShell y
reemplazá `<URL-del-repositorio>` por el enlace del repositorio:

```powershell
git clone <URL-del-repositorio> proyecto_driada
cd proyecto_driada
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$secret = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
Set-Content -Path .env -Value "SECRET_KEY=$secret"
python .\app.py
```

Si PowerShell / terminal, impide activar el entorno virtual, ejecutá
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` en esa misma
ventana y volvé a activar `.venv`.

El comando genera una `SECRET_KEY` propia para esa instalación. El archivo
`.env` la conserva entre reinicios y está excluido de Git:Por eso no se comparte ni se sube el .env con key.
El archivo `.env.example` es solo una referencia, no se usa como
configuración activa.

Con Flask iniciado, abrí `http://127.0.0.1:5000`. Si no se incluyó la base de
datos en el repositorio, no hace falta crearla manualmente: al iniciar, la
aplicación crea `instance/driada.sqlite3` y las tablas necesarias. Esa base
local comienza sin mensajes de contacto; los nuevos se guardan en
`contact_messages`.

Para detener el servidor, presioná `Ctrl+C` en la terminal. En futuras sesiones,
volvé a la carpeta del proyecto, activá `.venv` y ejecutá `python .\app.py`;
no vuelvas a generar la clave si ya existe `.env`.

La base se puede inspeccionar con DB Browser for SQLite.

Para ejecutar las pruebas:

```powershell
python -m unittest discover -s tests
```

## 🏫 Institución

IES Manuel Belgrano · Tecnicatura Superior en Redes, Telecomunicaciones y Ciberseguridad · 2026
