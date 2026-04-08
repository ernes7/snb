# Flask + SQLite Engineering Principles

> Production-grade standards for a server-rendered Flask app with SQLite. Non-negotiable.

---

## Stack

- **Server:** Flask (app factory + blueprints)
- **DB:** SQLite via SQLAlchemy ORM
- **Templates:** Jinja2 with component macros
- **Rendering:** 100% server-rendered — Flask queries the DB and renders HTML. No SPA, no frontend framework.

---

## Quick Reference

| # | Principle | Rule |
|---|-----------|------|
| 1 | File size | Max 300 lines, single responsibility |
| 2 | Typing | Type hints everywhere, `mypy --strict` |
| 3 | Blueprints | Every feature is a blueprint, no exceptions |
| 4 | Templates | Component-based Jinja2 — macros + includes |
| 5 | Dependencies | Minimal. Build custom unless it saves weeks |
| 6 | SQLite | WAL mode, one writer, respect the constraints |
| 7 | Config | Environment-based, never hardcoded secrets |
| 8 | Tech debt | Fix immediately, DRY on 2nd occurrence |
| 9 | Models | One model per file, fat models thin views |
| 10 | Structure | Feature-based blueprints + shared components |
| 11 | Testing | Test boundaries: routes, services, models |
| — | **Clean Code** | **SRP, DRY, YAGNI, KISS — simplicity wins** |

---

## Detailed Rules

### 1. 300 Lines Max + Single Responsibility

No file exceeds 300 lines. Each file does one thing well.

**SRP test:** If you can't describe what a file does in one sentence, split it.

**When approaching 300 lines:** Extract into services, utils, or sub-blueprints.

```
blueprints/
  auth/
    routes.py        # only route definitions, <300 lines
    services.py      # business logic
    forms.py         # WTForms or manual validation
```

---

### 2. Type Hints + Mypy Strict

```ini
# mypy.ini
[mypy]
strict = True
disallow_any_generics = True
```

**Non-negotiable:**
- Every function has parameter and return type hints
- No `Any` — use `Union`, `Optional`, or custom types
- Dataclasses or TypedDict for structured data, never raw dicts passed around
- Type ignore comments require a justification

```python
# good — clear contract
def get_user_by_email(email: str) -> User | None:
    return User.query.filter_by(email=email).first()

# bad — nobody knows what this returns
def get_user_by_email(email):
    return User.query.filter_by(email=email).first()
```

---

### 3. Everything Is a Blueprint

No routes in `app.py`. Ever. Every feature lives in its own blueprint.

```python
# blueprints/auth/__init__.py
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='templates')

from . import routes  # noqa: E402
```

```python
# app.py — only wiring, never logic
def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)
    app.config.from_object(configs[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)

    return app
```

**Adding a new feature should be:**
1. Create blueprint folder
2. Define routes, services, templates
3. One line in `register_blueprints()`

That's it. If it's harder than this, the architecture is wrong.

---

### 4. Component-Based Templates

Jinja2 macros are your components. Reusable, data-driven, composable.

**Base layout (the shell):**
```html
{# templates/base.html #}
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{% endblock %} | {{ config.APP_NAME }}</title>
    {% block head %}{% endblock %}
</head>
<body>
    {% include 'components/navbar.html' %}
    {% include 'components/flash_messages.html' %}

    <main>{% block content %}{% endblock %}</main>

    {% include 'components/footer.html' %}
    {% block scripts %}{% endblock %}
</body>
</html>
```

**Macros = components with props:**
```html
{# templates/components/card.html #}
{% macro card(title, subtitle='', variant='default') %}
<div class="card card--{{ variant }}">
    <h3 class="card__title">{{ title }}</h3>
    {% if subtitle %}<p class="card__subtitle">{{ subtitle }}</p>{% endif %}
    <div class="card__body">{{ caller() }}</div>
</div>
{% endmacro %}
```

**Using the component — just like passing props:**
```html
{% from 'components/card.html' import card %}
{% from 'components/form_field.html' import form_field %}
{% from 'components/button.html' import button %}

{% extends 'base.html' %}
{% block content %}
    {% call card(title='Create Account', variant='elevated') %}
        {{ form_field(name='email', type='email', label='Email', required=true) }}
        {{ form_field(name='password', type='password', label='Password', required=true) }}
        {{ button(text='Sign Up', variant='primary', type='submit') }}
    {% endcall %}
{% endblock %}
```

**A new page should be:** extend base, import components, pass data. Zero copy-paste HTML.

**Component library — build once, use everywhere:**
```
templates/
  components/
    button.html          # {{ button(text, variant, size, href) }}
    card.html            # {% call card(title, variant) %} ... {% endcall %}
    form_field.html      # {{ form_field(name, type, label, error) }}
    modal.html           # {% call modal(id, title) %} ... {% endcall %}
    table.html           # {{ table(headers, rows, empty_message) }}
    pagination.html      # {{ pagination(paginated_query) }}
    flash_messages.html  # auto-renders Flask flash messages
    navbar.html          # site nav, reads from config
    empty_state.html     # {{ empty_state(icon, title, message, action_url) }}
    confirm_delete.html  # {{ confirm_delete(url, item_name) }}
```

---

### 5. Minimal Dependencies + YAGNI

**Build custom:** Flash message styling, pagination helper, form helpers, simple validation, formatters.

**Use libraries:** SQLAlchemy (ORM), Flask-Migrate/Alembic (migrations), WTForms (complex forms), Flask-Login (auth sessions).

**Don't even think about it:** Celery, Redis, task queues, API serializers — this is a server-rendered SQLite app, not a distributed system.

**YAGNI:**
- No "just in case" abstractions
- No generic base classes nobody extends
- No config toggles nobody asked for

---

### 6. SQLite Rules

SQLite is the database. Respect its strengths and constraints.

**Enable WAL mode on app startup — always:**
```python
# extensions.py
from sqlalchemy import event

def init_db(app: Flask) -> None:
    db.init_app(app)

    @event.listens_for(db.engine, 'connect')
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')      # concurrent reads while writing
        cursor.execute('PRAGMA synchronous=NORMAL')     # safe + fast balance
        cursor.execute('PRAGMA foreign_keys=ON')        # enforce FK constraints
        cursor.execute('PRAGMA busy_timeout=5000')      # wait 5s instead of failing instantly
        cursor.close()
```

**DB file lives in instance folder:**
```python
SQLALCHEMY_DATABASE_URI: str = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db')
```

**SQLite constraints to respect:**
- One writer at a time — keep write transactions short
- No `ALTER TABLE DROP COLUMN` on older SQLite versions — plan migrations carefully
- No concurrent write-heavy workloads — if you need that, switch to Postgres
- Always use SQLAlchemy relationships, never raw JOINs scattered in routes

**Backup is just copying a file:**
```python
# lib/backup.py
import shutil
from datetime import datetime

def backup_db(db_path: str, backup_dir: str) -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(backup_dir, f'app_{timestamp}.db')
    shutil.copy2(db_path, dest)
    return dest
```

**Model timestamps mixin — use on every model:**
```python
# models/mixins.py
from datetime import datetime

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

---

### 7. Config Management

```python
# lib/config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class BaseConfig:
    APP_NAME: str = 'MyApp'
    SECRET_KEY: str = os.environ['SECRET_KEY']  # crash on missing, don't default
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'app.db')

class DevConfig(BaseConfig):
    DEBUG: bool = True

class ProdConfig(BaseConfig):
    DEBUG: bool = False
    SECRET_KEY: str = os.environ['SECRET_KEY']

class TestConfig(BaseConfig):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite://'  # in-memory for tests, instant

configs: dict[str, type[BaseConfig]] = {
    'dev': DevConfig,
    'prod': ProdConfig,
    'testing': TestConfig,
    'default': DevConfig,
}
```

**Rules:**
- Secrets crash loudly if missing — never silently default
- SQLite path always points to `instance/` folder (gitignored)
- Test config uses in-memory SQLite — instant setup, instant teardown

---

### 8. Error Handling

**At the app level, not scattered in routes:**
```python
# app.py
def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500
```

**Service layer raises, routes catch via Flask's error handling.** No `try/except` in routes unless you're handling a specific, expected exception.

---

### 9. Fat Models, Thin Views

Routes should be 5-10 lines max. Business logic lives in services or model methods.

```python
# bad — route does everything
@auth_bp.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    if User.query.filter_by(email=email).first():
        flash('Email taken', 'error')
        return redirect(url_for('auth.register'))
    user = User(email=email)
    user.set_password(request.form['password'])
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for('main.dashboard'))
```

```python
# good — route is just glue
@auth_bp.route('/register', methods=['POST'])
def register():
    form = RegisterForm(request.form)
    if not form.validate():
        return render_template('auth/register.html', form=form)

    user = AuthService.register(form.data)
    login_user(user)
    return redirect(url_for('main.dashboard'))
```

```python
# services/auth_service.py — testable, reusable
class AuthService:
    @staticmethod
    def register(data: dict) -> User:
        if User.query.filter_by(email=data['email']).first():
            raise ValidationError('Email already registered')
        user = User(email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return user
```

**The pattern is always:** Route validates input → calls service → renders template with result.

---

### 10. Project Structure

```
project/
├── app.py                      # create_app factory only
├── extensions.py               # db, migrate, login_manager init
├── blueprints/
│   ├── auth/
│   │   ├── __init__.py         # blueprint registration
│   │   ├── routes.py           # route definitions
│   │   ├── services.py         # business logic
│   │   └── forms.py            # WTForms or validation
│   ├── main/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── services.py
│   └── admin/
│       ├── __init__.py
│       ├── routes.py
│       └── services.py
├── models/
│   ├── __init__.py             # import all models here
│   ├── user.py                 # one model per file
│   └── mixins.py               # TimestampMixin, SoftDeleteMixin
├── services/                   # cross-cutting services
├── lib/
│   ├── config.py
│   ├── backup.py               # SQLite backup utility
│   └── utils.py
├── templates/
│   ├── base.html               # master layout
│   ├── components/             # reusable Jinja2 macros
│   └── errors/                 # 404.html, 500.html
├── static/
│   ├── css/
│   └── js/
├── tests/
│   ├── conftest.py             # fixtures, in-memory SQLite
│   ├── test_auth/
│   └── test_main/
├── instance/                   # gitignored — app.db lives here
├── migrations/                 # alembic
└── requirements/
    ├── base.txt
    └── dev.txt
```

**Naming:** Models `PascalCase`, files `snake_case`, blueprints `snake_case`, constants `UPPER_SNAKE`.

---

### 11. Testing Strategy

Test boundaries, not internals. In-memory SQLite makes tests instant.

```python
# conftest.py
@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def seed_user(app):
    user = User(email='test@test.com')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user
```

**What to test:**
- Routes: status codes, redirects, flash messages, rendered content
- Services: business logic, edge cases, error paths
- Models: custom methods, validations, relationships

**What not to test:**
- Flask or SQLAlchemy internals
- Private methods — test through the public interface
- That Jinja2 renders HTML correctly (trust the engine)

---

## The "New Page" Checklist

Adding a page should take 5 minutes:

1. Add route in the blueprint's `routes.py` (5-10 lines)
2. Create template — extend base, import components, pass data
3. Add service method if there's business logic
4. That's it. If there's a step 4, refactor.

```python
# routes.py — the whole route
@main_bp.route('/dashboard')
@login_required
def dashboard():
    stats = DashboardService.get_stats(current_user)
    recent = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return render_template('main/dashboard.html', stats=stats, recent=recent)
```

```html
{# templates/main/dashboard.html — the whole template #}
{% extends 'base.html' %}
{% from 'components/card.html' import card %}
{% from 'components/table.html' import table %}
{% from 'components/empty_state.html' import empty_state %}

{% block title %}Dashboard{% endblock %}
{% block content %}
    {% call card(title='Overview') %}
        {{ table(headers=['Metric', 'Value'], rows=stats.summary) }}
    {% endcall %}

    {% if recent %}
        {% call card(title='Recent Posts') %}
            {{ table(headers=['Title', 'Date'], rows=recent) }}
        {% endcall %}
    {% else %}
        {{ empty_state(title='No posts yet', message='Create your first post.') }}
    {% endif %}
{% endblock %}
```

---

## The Data Flow

Every request follows the same path. No exceptions.

```
Browser request
  → Flask route (validate input, call service, render)
    → Service (business logic, talks to models)
      → SQLAlchemy model (queries SQLite)
    ← Data back to route
  ← render_template('page.html', data=data)
    ← Jinja2 assembles base + components + data
← Full HTML response to browser
```

If you find yourself breaking this flow — fetching data in templates, putting logic in routes, or doing raw SQL in services — stop and refactor.

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Routes with business logic | Services layer (fat models, thin views) |
| Raw dicts as data contracts | Dataclasses, TypedDict, or model instances |
| Copy-paste HTML between pages | Jinja2 macros — build it once |
| Routes in `app.py` | Blueprints, always |
| `try/except` everywhere | Error handlers at app level |
| Files > 300 lines | Extract services, utils, sub-blueprints |
| Silent config defaults for secrets | Crash loudly on missing env vars |
| `from app import db` circular | `extensions.py` pattern |
| Raw SQL scattered in routes | Model methods or service queries |
| Hardcoded URLs in templates | `url_for()` everywhere |
| Forgetting `PRAGMA foreign_keys=ON` | Set it on every connection (see §6) |
| Long write transactions | Keep writes short — SQLite is single-writer |
| DB file in project root | `instance/` folder, gitignored |
| Querying the DB inside templates | Pass all data from the route |

---

*Last updated: April 2026*
