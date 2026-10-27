"""Three different claims hide inside "the write succeeded".

    python3 examples/exists_is_not_created.py

1. The record exists when read back.
2. My request created it.
3. It is the record I meant to write.

A naive check (status OK + read back by id) confirms claim 1 and silently
assumes 2 and 3. This script shows all three diverging with SQLite alone.
"""
import sqlite3

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE comments (id TEXT PRIMARY KEY, parent TEXT, body TEXT)")
db.execute("INSERT INTO comments VALUES ('c1', 'p9', 'an older comment, written by someone else')")


def naive_write(cid, parent, body):
    """Reports success if no exception was raised and the id reads back."""
    db.execute("INSERT OR IGNORE INTO comments VALUES (?, ?, ?)", (cid, parent, body))
    return db.execute("SELECT 1 FROM comments WHERE id = ?", (cid,)).fetchone() is not None


def careful_write(cid, parent, body):
    """Checks what the request did, then reads back the fields it meant to set."""
    cur = db.execute("INSERT OR IGNORE INTO comments VALUES (?, ?, ?)", (cid, parent, body))
    if cur.rowcount != 1:
        return f"NOT CREATED: {cur.rowcount} rows inserted (the id was already taken)"
    row = db.execute("SELECT parent, body FROM comments WHERE id = ?", (cid,)).fetchone()
    if row != (parent, body):
        return f"CREATED BUT WRONG: read back {row!r}, expected {(parent, body)!r}"
    return "created and verified"


print("naive   c1:", naive_write("c1", "p1", "my reply"))     # True, yet nothing of mine was written
print("careful c1:", careful_write("c1", "p1", "my reply"))   # tells the truth
print("careful c2:", careful_write("c2", "p1", "my reply"))   # the honest success case
