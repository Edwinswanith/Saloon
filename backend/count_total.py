import sqlite3

conn = sqlite3.connect('instance/salon.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]

total = 0
for t in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {t}')
    total += cursor.fetchone()[0]

print(f'Total SQLite records: {total}')
conn.close()
