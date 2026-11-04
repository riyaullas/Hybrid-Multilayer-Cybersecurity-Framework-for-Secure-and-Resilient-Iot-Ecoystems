
import os
import sys
import sqlite3
from pathlib import Path

# --------------------------------------------------
# 1. Configure the existing backend database
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BACKEND_DIR / "medsecure.db"

if not DATABASE_PATH.exists():
    raise FileNotFoundError(
        f"Database not found: {DATABASE_PATH}\n"
        "Please verify that this is the correct backend folder."
    )

# Use an absolute SQLite database path.
os.environ["DATABASE_URL"] = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Allow imports from the backend application.
sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base, engine, SessionLocal
from app.models import Device, Audit
from app.security import new_device_keypair


# --------------------------------------------------
# 2. Define the synthetic demonstration devices
# --------------------------------------------------

SAMPLES = [
    (
        "MON-001",
        "Bedside Monitor 01",
        "Patient monitor",
        "192.0.2.11",
    ),
    (
        "WRB-002",
        "Wearable Sensor 02",
        "Wearable sensor",
        "192.0.2.12",
    ),
    (
        "GW-001",
        "Monitoring Gateway",
        "Remote patient-monitoring gateway",
        "192.0.2.20",
    ),
    (
        "MED-003",
        "Smart Infusion Unit 03",
        "Smart medical equipment",
        "192.0.2.13",
    ),
    (
        "ENV-004",
        "Room Environment Sensor",
        "Environmental monitoring sensor",
        "192.0.2.14",
    ),
]


# --------------------------------------------------
# 3. Prepare the local demonstration key directory
# --------------------------------------------------

KEY_DIR = BACKEND_DIR / "device_keys"
KEY_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 4. Initialize the devices
# --------------------------------------------------

def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        existing_count = db.query(Device).count()

        if existing_count > 0:
            print(f"Devices already exist: {existing_count}")
            print("No new devices were created.")

        else:
            created_devices = []

            for device_id, name, device_type, ip_address in SAMPLES:
                private_key, public_key, fingerprint = new_device_keypair()

                device = Device(
                    device_id=device_id,
                    name=name,
                    device_type=device_type,
                    ip_address=ip_address,
                    public_key_pem=public_key,
                    key_fingerprint=fingerprint,
                )

                db.add(device)
                created_devices.append(
                    (device_id, private_key)
                )

            # Save device records first.
            db.flush()

            # Save local private keys for the demo.
            for device_id, private_key in created_devices:
                key_path = KEY_DIR / f"{device_id}.pem"

                with key_path.open("w", encoding="utf-8") as key_file:
                    key_file.write(private_key)

                try:
                    os.chmod(key_path, 0o600)
                except OSError:
                    pass

            # Record the synthetic initialization in the audit log.
            db.add(
                Audit(
                    actor="local-demo-setup",
                    action="demo.seed",
                    resource="devices",
                    outcome="success",
                    metadata_json={
                        "count": len(created_devices),
                        "synthetic": True,
                    },
                )
            )

            db.commit()

            print(
                f"SUCCESS: Created {len(created_devices)} "
                "synthetic demonstration devices."
            )

        # Display the final device list.
        print("\nCurrent device list:")

        devices = (
            db.query(Device)
            .order_by(Device.device_id)
            .all()
        )

        for device in devices:
            print(f"  {device.device_id} - {device.name}")

        print(f"\nTotal devices: {len(devices)}")
        print(f"Database: {DATABASE_PATH}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
