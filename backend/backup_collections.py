"""
Lightweight backup of `bills` and `cash_transactions` collections to JSON files.

Equivalent in safety to mongodump for the scope of this cleanup. The output
files preserve every field including ObjectIds and dates as JSON-compatible
strings; a companion restore script is at `restore_backup.py`.

Usage:
    cd backend
    python backup_collections.py                          # default: ./backup_<timestamp>/
    python backup_collections.py --out ./backup_2026-05-05
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, date
from bson import ObjectId

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from mongoengine import connect
from mongoengine.connection import get_db


def connect_db():
    uri = os.environ.get(
        'MONGODB_URI',
        'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon',
    )
    db_name = os.environ.get('MONGODB_DB', 'Saloon_prod')
    base = uri
    if '@' in base and '/' in base.split('@', 1)[1]:
        creds, host_part = base.split('@', 1)
        host_only = host_part.split('?', 1)[0].split('/', 1)[0]
        params = '?' + host_part.split('?', 1)[1] if '?' in host_part else ''
        base = f'{creds}@{host_only}{params}'
    if f'/{db_name}' not in base:
        base = base.replace('?', f'/{db_name}?', 1) if '?' in base else f'{base}/{db_name}'
    sep = '&' if '?' in base else '?'
    extras = []
    if 'retryWrites' not in base: extras.append('retryWrites=true')
    if 'w=' not in base: extras.append('w=majority')
    if 'tls=' not in base and 'ssl=' not in base: extras.append('tls=true')
    if extras: base = f"{base}{sep}{'&'.join(extras)}"
    connect(host=base, alias='default', db=db_name,
            serverSelectionTimeoutMS=30000, connectTimeoutMS=30000, socketTimeoutMS=30000)
    print(f'Connected to MongoDB: {db_name}\n')
    return db_name


def serialize(obj):
    """Recursively convert MongoDB types to JSON-friendly forms while preserving info."""
    if isinstance(obj, ObjectId):
        return {'$oid': str(obj)}
    if isinstance(obj, datetime):
        return {'$date': obj.isoformat()}
    if isinstance(obj, date):
        return {'$date': obj.isoformat()}
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize(v) for v in obj]
    return obj


def parse_args():
    p = argparse.ArgumentParser(description='Back up bills + cash_transactions to JSON')
    p.add_argument('--out', help='Output directory (default: ./backup_<timestamp>)')
    return p.parse_args()


def main():
    args = parse_args()
    connect_db()
    db = get_db()

    out_dir = args.out
    if not out_dir:
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        out_dir = os.path.join(SCRIPT_DIR, f'backup_{ts}')
    os.makedirs(out_dir, exist_ok=True)
    print(f'Output directory: {out_dir}\n')

    for coll_name in ['bills', 'cash_transactions']:
        coll = db[coll_name]
        total = coll.count_documents({})
        print(f'Backing up {coll_name}... ({total} documents)')
        path = os.path.join(out_dir, f'{coll_name}.json')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('[\n')
            first = True
            for doc in coll.find({}):
                if not first:
                    f.write(',\n')
                first = False
                json.dump(serialize(doc), f, ensure_ascii=False)
            f.write('\n]\n')
        size_kb = os.path.getsize(path) / 1024
        print(f'  -> {path}  ({size_kb:.1f} KB)')

    print(f'\nBackup complete. Folder: {out_dir}')
    print('Keep this folder until you are confident the cleanup result is correct.')


if __name__ == '__main__':
    main()
