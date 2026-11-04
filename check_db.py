import sqlite3

database_path = "backend/medsecure.db"
connection = sqlite3.connect(database_path)

print("\n--- DATABASE TABLES ---")
tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

for table in tables:
    print(table[0])

print("\n--- DEVICE TABLE ---")

try:
    devices = connection.execute("SELECT * FROM devices").fetchall()
    print("Number of devices:", len(devices))

    for device in devices:
        print(device)

except sqlite3.Error as error:
    print("Device table check:", error)

connection.close()