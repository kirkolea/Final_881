"""One-off script: downsample high-rate sensor tables so the DB fits under
GitHub's 100 MB limit. Keeps every 20th row of the noisy channels.
Run once: python shrink_db.py
"""
import sqlite3
import os

DB = "wearable_data.db"
before = os.path.getsize(DB) / 1e6
print(f"Before: {before:.1f} MB")

conn = sqlite3.connect(DB)
for tbl in ["acc", "bvp", "eda", "temp", "hr"]:
    try:
        n_before = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        conn.execute(f"DELETE FROM {tbl} WHERE rowid % 20 != 0")
        n_after = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl}: {n_before:,} -> {n_after:,}")
    except sqlite3.OperationalError as e:
        print(f"  skip {tbl}: {e}")
conn.commit()
conn.execute("VACUUM")
conn.close()

after = os.path.getsize(DB) / 1e6
print(f"After: {after:.1f} MB")
