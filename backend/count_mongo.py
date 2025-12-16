from app import app
import mongoengine

with app.app_context():
    db = mongoengine.connection.get_db()
    collections = db.list_collection_names()

    total = 0
    for c in collections:
        count = db[c].count_documents({})
        total += count
        print(f'{c}: {count}')

    print(f'\nTotal MongoDB records: {total}')
