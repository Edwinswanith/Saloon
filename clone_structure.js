// mongosh "mongodb+srv://edwin:<db_password>@saloon.8fxk7vz.mongodb.net/?appName=Saloon" --file clone_structure.js

const sourceDB = "Saloon";
const targetDB = "Saloon_prod";

const src = db.getSiblingDB(sourceDB);
const tgt = db.getSiblingDB(targetDB);

src.getCollectionNames().forEach((coll) => {
  const info = src.getCollectionInfos({ name: coll })[0];

  // Create collection with same options (validators, collation, etc.)
  const options = info.options || {};
  try {
    tgt.createCollection(coll, options);
    print(`Created collection: ${coll}`);
  } catch (e) {
    if (e.code === 48) { // Collection already exists
      print(`Collection already exists: ${coll}`);
    } else {
      print(`Collection creation failed (${coll}): ${e.message}`);
    }
  }

  // Recreate indexes
  const indexes = src.getCollection(coll).getIndexes();
  indexes.forEach((idx) => {
    if (idx.name === "_id_") return; // auto-created
    const key = idx.key;
    const idxOptions = { ...idx };
    delete idxOptions.key;
    delete idxOptions.ns;
    delete idxOptions.v;

    try {
      tgt.getCollection(coll).createIndex(key, idxOptions);
      print(`  Created index: ${coll}.${idx.name}`);
    } catch (e) {
      if (e.code === 85) { // Index already exists
        print(`  Index already exists: ${coll}.${idx.name}`);
      } else {
        print(`  Index creation failed (${coll}.${idx.name}): ${e.message}`);
      }
    }
  });
});

print("Done.");

