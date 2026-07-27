#!/usr/bin/env python3
"""Write gcloud --env-vars-file YAML from .env (for Cloud Run deploy)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'backend'))

from utils.env_config import get_env, get_jwt_secret, get_mongodb_db, get_mongodb_uri, load_env


def main():
    load_env()
    out_path = ROOT / '.gcloud.env.yaml'
    lines = [
        f'MONGODB_URI: "{get_mongodb_uri()}"',
        f'MONGODB_DB: "{get_mongodb_db()}"',
        f'JWT_SECRET: "{get_jwt_secret()}"',
    ]
    optional_keys = (
        'REDIS_URL',
        'WHATSAPP_API_TOKEN',
        'WHATSAPP_PHONE_NUMBER_ID',
        'BUSINESS_NAME',
        'FLASK_ENV',
    )
    for key in optional_keys:
        value = get_env(key)
        if value:
            lines.append(f'{key}: "{value}"')
    out_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Wrote {out_path}')


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
