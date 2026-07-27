#!/usr/bin/env python3
"""Print docker --build-arg flags from root .env (for Vite build args)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'backend'))

from utils.env_config import get_env, load_env

BUILD_ARG_KEYS = ('VITE_API_BASE_URL', 'VITE_PUBLIC_BASE_URL')


def main():
    load_env()
    args = []
    for key in BUILD_ARG_KEYS:
        value = get_env(key)
        if value:
            args.append(f'--build-arg {key}={value}')
    print(' '.join(args))


if __name__ == '__main__':
    main()
