"""Load application secrets from .env only — never hardcode credentials."""
from pathlib import Path
import os

from dotenv import load_dotenv

_loaded = False
VALID_APP_RUNTIMES = {'production', 'demo'}


class RuntimeConfigurationError(RuntimeError):
    """Raised when the server runtime is absent or ambiguous."""


def _env_file_paths():
    backend_dir = Path(__file__).resolve().parent.parent
    root_dir = backend_dir.parent
    yield root_dir / '.env'
    yield backend_dir / '.env'


def load_env():
    """Load the first .env file found (project root, then backend/)."""
    global _loaded
    if _loaded:
        return

    for path in _env_file_paths():
        if path.is_file():
            load_dotenv(path)
            _loaded = True
            return

    load_dotenv()
    _loaded = True


def get_env(name, default=None, required=False):
    load_env()
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f'{name} is not set. Copy .env.example to .env and add your value.'
        )
    return value


def get_app_runtime(environ=None):
    """Return an explicit runtime without falling back across environments."""
    load_env()
    source = environ if environ is not None else os.environ
    raw_runtime = source.get('APP_RUNTIME')
    if (
        not isinstance(raw_runtime, str)
        or raw_runtime not in VALID_APP_RUNTIMES
    ):
        raise RuntimeConfigurationError(
            'APP_RUNTIME must be explicitly set to production or demo.'
        )
    return raw_runtime


def is_demo_runtime(environ=None):
    return get_app_runtime(environ) == 'demo'


def get_mongodb_uri():
    if is_demo_runtime():
        return get_env('MONGODB_URI_DEMO', required=True)
    return get_env('MONGODB_URI', required=True)


def get_mongodb_db(default='Saloon_prod'):
    if is_demo_runtime():
        database = get_env('MONGODB_DB_DEMO', required=True)
        if database != 'Saloon_demo':
            raise RuntimeConfigurationError(
                'MONGODB_DB_DEMO must be exactly Saloon_demo.'
            )
        return database
    database = get_env('MONGODB_DB', default=default)
    if not database or 'demo' in database.lower():
        raise RuntimeConfigurationError(
            'The production runtime requires a non-demo MONGODB_DB.'
        )
    return database


def get_jwt_secret():
    if is_demo_runtime():
        demo_secret = get_env('JWT_SECRET_DEMO', required=True)
        production_secret = get_env('JWT_SECRET')
        if production_secret and demo_secret == production_secret:
            raise RuntimeConfigurationError(
                'JWT_SECRET_DEMO must differ from JWT_SECRET.'
            )
        return demo_secret
    return get_env('JWT_SECRET', required=True)
