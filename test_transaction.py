from app.config.database import SessionLocal
from app.core.exceptions import ConflictException
from app.models.client import Client
from app.services.database import transaction_scope


def test_roolback():
    """Verify transaction rolls back on error"""

    db = SessionLocal()

    try:
        with transaction_scope(db):
            client = Client(
                name="Test",
                email="test@test.com",
                address="123 St",
                phone="1234567890",
                post_addr="12345"
            )
            db.add(client)
            db.flush()

            print(f"✓ Client created: {client.id}")

            client2 = Client(
                name="Test2",
                email="test@test.com",
                address="456 Ave",
                phone="0987654321",
                post_addr="54321"
            )
            db.add(client2)

    except ConflictException as e:
        print(f"✓ Rolled back: {e.message}")

        db.rollback()
        count = db.query(Client).filter(
            Client.email == "test@test.com").count()
        print(f"✓ Verification: {count} clients saved (should be 0)")

    finally:
        db.close()


if __name__ == "__main__":
    test_roolback()
