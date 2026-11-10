# Surviconix — Plataforma de encuestas y votaciones

Aplicación web desarrollada con **Django** para crear encuestas, votar, valorar y comentar,
con un panel de moderación para administradores. Proyecto académico construido siguiendo el
proceso **ICONIX** (análisis → diseño → implementación).

> **Estado:** funcional y completo a nivel de funcionalidades. Sin despliegue público y sin
> pruebas automatizadas todavía. Ver [Estado y limitaciones](#estado-y-limitaciones).

---

## Qué resuelve

Crear una encuesta suele terminar en un formulario de Google sin control: no sabés quién votó,
no podés evitar votos repetidos y no hay forma de moderar comentarios. Surviconix cubre ese
ciclo completo dentro de una sola aplicación:

- Un usuario registrado crea una encuesta con hasta 5 opciones y una fecha límite.
- Cada usuario puede votar **una sola vez** por encuesta.
- Al cerrar la encuesta, el creador o un administrador puede **exportar los resultados a CSV**.
- Los usuarios valoran con estrellas y comentan; los comentarios se pueden responder y likear.
- Los administradores bloquean encuestas, resuelven reportes y suspenden cuentas.

---

## Funcionalidades

### Visitantes
- Ver el listado de encuestas y la página principal con las más recientes.
- Buscar encuestas por título.
- Registrarse e iniciar sesión.

### Usuarios registrados
- Crear encuestas con título, descripción, categoría, fecha límite y entre 1 y 5 respuestas.
- Editar y eliminar sus propias encuestas (los administradores pueden hacerlo con cualquiera).
- Votar una sola vez por encuesta.
- Valorar encuestas de 1 a 5 estrellas; el promedio se muestra con estrellas completas y medias.
- Comentar, responder comentarios, dar "me gusta" y borrar los propios.
- Reportar encuestas o comentarios.
- Editar su perfil: biografía, país, dirección, teléfono, fecha de nacimiento y foto.

### Administradores (staff)
- Panel de gestión de encuestas con bloqueo y motivo del bloqueo.
- Panel de gestión de usuarios: suspender con duración y motivo, o eliminar cuentas.
- Bandeja de reportes pendientes y resolución de cada uno.
- Exportar resultados a CSV una vez cerrada la encuesta.

### Reglas de negocio
| Regla | Implementación |
|---|---|
| Un voto por usuario y encuesta | `unique_together = ('user', 'survey')` en `UserVote` |
| Una valoración por usuario y encuesta | `unique_together` en `Rating` + `update_or_create` |
| No se vota ni comenta en encuestas bloqueadas | Validación en la vista `vote` y `post_comment` |
| No se vota después de la fecha límite | Validación en `rate_survey` y en el detalle |
| Solo el creador o staff edita/elimina/exporta | `UserPassesTestMixin` por vista |
| El export solo existe con la encuesta cerrada | `test_func` valida `timezone.now() > survey.deadline` |
| Un suspendido no puede navegar | `CheckSuspensionMiddleware` redirige al login |

---

## Stack

- **Python 3.12 / 3.13**
- **Django 5.1.6** (vistas basadas en clases y en funciones)
- **SQLite** (desarrollo)
- **Pillow** para el manejo de imágenes de perfil
- **HTML y CSS propios** (sin framework de UI)
- **JavaScript** para interacciones sin recargar (valoraciones, likes, comentarios, moderación)

Dependencias exactas en [`requirements.txt`](requirements.txt):

```
asgiref==3.8.1
Django==5.1.6
pillow==11.1.0
sqlparse==0.5.3
tzdata==2025.1
```

---

## Arquitectura

```
Web-Encuestas/
├── django_project/          # Configuración del proyecto
│   ├── settings.py          # Apps, middleware, BD, media, auth
│   ├── urls.py              # Rutas raíz
│   ├── asgi.py
│   └── wsgi.py
├── users/                   # Autenticación y perfiles
│   ├── models.py            # User (AbstractUser) + Profile
│   ├── views.py             # Registro, perfil, login, gestión de usuarios
│   ├── auth_middleware.py   # CheckSuspensionMiddleware
│   ├── forms.py
│   ├── signals.py           # Creación automática del perfil
│   └── templates/
├── survey/                  # Dominio de encuestas
│   ├── models.py            # Survey, Answer, UserVote, Rating, Comment, Report
│   ├── views.py             # CRUD, voto, valoración, comentarios, moderación, export
│   ├── forms.py             # Formularios con respuestas dinámicas (1–5)
│   ├── urls.py
│   ├── templatetags/        # Filtro para calcular porcentajes en plantillas
│   ├── migrations/          # 8 migraciones
│   └── templates/
├── media/profile_pics/      # Imágenes subidas por los usuarios
├── manage.py
└── requirements.txt
```

### Modelo de datos

```
User (AbstractUser) 1──1 Profile
  │
  ├──1:N── Survey ──1:N── Answer
  │           │
  │           ├──1:N── Rating      (unique: user + survey)
  │           ├──1:N── Comment ──1:N── Comment (respuestas anidadas)
  │           │            └──M:N── User (likes)
  │           └──1:N── UserVote    (unique: user + survey)
  │
  └──1:N── Report ── GenericForeignKey → Survey | Comment
```El Documento del proceso Iconix es el siguiente:

[Surviconix - Proceso ICONIX.pdf](https://github.com/user-attachments/files/19056472/Surviconix.-.Proceso.ICONIX.pdf)


- **`Survey`**: título, descripción, categoría (`GEN`, `TEC`, `EDU`, `POL`), fecha límite,
  creador, estado de bloqueo y motivo.
- **`Answer`**: opción de respuesta con contador de votos.
- **`UserVote`**: registra que un usuario ya votó, para impedir votos múltiples.
- **`Rating`**: 1–5 estrellas; el promedio se calcula con `Avg` y se renderiza en medias estrellas.
- **`Comment`**: autorreferenciado (`parent`) para respuestas anidadas, con `likes` many-to-many.
- **`Report`**: usa `GenericForeignKey` para reportar tanto encuestas como comentarios con un
  solo modelo.

---

## Cómo ejecutarlo

```bash
# 1. Clonar
git clone https://github.com/KevinGuio/Web-Encuestas.git
cd Web-Encuestas

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Base de datos
#    El repo incluye db.sqlite3 con el esquema y datos de ejemplo.
#    Si preferís una base limpia:
rm db.sqlite3
python manage.py migrate

# 5. Usuario administrador
python manage.py createsuperuser

# 6. Servidor
python manage.py runserver
```

Aplicación en `http://127.0.0.1:8000/` y panel de administración en
`http://127.0.0.1:8000/admin/`.

---

## Decisiones técnicas

- **Voto único a nivel de base de datos.** No se controla solo en la vista: la restricción
  `unique_together` garantiza la integridad incluso con peticiones concurrentes.
- **`update_or_create` para las valoraciones.** Permite que un usuario cambie su calificación
  sin generar duplicados ni errores de unicidad.
- **Middleware de suspensión.** Centraliza la expulsión de cuentas suspendidas en un solo punto
  en lugar de repetir la validación en cada vista; además levanta la suspensión sola cuando
  vence.
- **`GenericForeignKey` para reportes.** Un único modelo cubre encuestas y comentarios, sin
  duplicar tablas ni lógica de moderación.
- **Optimización de consultas en el panel de reportes.** Se resuelven los objetos reportados con
  `in_bulk()` por tipo de contenido, evitando una consulta por reporte (N+1).
- **Respuestas dinámicas de 1 a 5.** El formulario expone cinco campos opcionales y valida solo
  los que el usuario declara usar.

---

## Documentación de diseño

El proceso ICONIX completo (casos de uso, diagramas de clases y de secuencia) está en:

📄 [`Surviconix.-.Proceso.ICONIX.pdf`](Surviconix.-.Proceso.ICONIX.pdf)

---

## Estado y limitaciones

Este es un proyecto académico, y el README lo dice para que nadie se lleve una sorpresa:

- **Sin pruebas automatizadas.** `tests.py` está vacío; es lo primero que agregaría.
- **Sin despliegue público.** Corre en local con SQLite.
- **Configuración de desarrollo.** `DEBUG = True` y `SECRET_KEY` están en el repositorio; en
  producción irían en variables de entorno.
- **SQLite.** Para producción migraría a PostgreSQL.
- **Archivos versionados que no deberían estarlo.** `db.sqlite3`, `__pycache__/` y las imágenes
  de `media/` están en el repo.

## Próximos pasos

- [ ] Pruebas con `pytest-django`: voto único, cierre por fecha, permisos de edición y export.
- [ ] Mover `SECRET_KEY`, `DEBUG` y `ALLOWED_HOSTS` a variables de entorno.
- [ ] Migrar a PostgreSQL y desplegar (Railway o Render) con `gunicorn` y `whitenoise`.
- [ ] Añadir `.gitignore` y limpiar `db.sqlite3`, `__pycache__/` y `media/` del historial.
- [ ] Paginación configurable y filtros por categoría en el listado.
- [ ] Resultados en vivo con gráficos (Chart.js) en el detalle de la encuesta.

---

## Autor

**Kevin Daniel Guio Covilla** — Ingeniero de Sistemas e Informática, Universidad Nacional de Colombia

- LinkedIn: [linkedin.com/in/kevin-guio](https://www.linkedin.com/in/kevin-guio/)
- GitHub: [github.com/KevinGuio](https://github.com/KevinGuio)
- Correo: kevinguiocovilla@gmail.com
