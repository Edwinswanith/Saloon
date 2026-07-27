"""Load application secrets from .env only — never hardcode credentials."""
from pathlib import Path
import os

from dotenv import load_dotenv

_loaded = False


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


def get_mongodb_uri():
    return get_env('MONGODB_URI', required=True)


def get_mongodb_db(default='Saloon_prod'):
    return get_env('MONGODB_DB', default=default)


def get_jwt_secret():
    return get_env('JWT_SECRET', required=True)
