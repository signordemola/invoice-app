"""
Database reset script - USE ONLY IN DEVELOPMENT
Drops all tables and recreates them from models
"""

from app.config.database import engine, Base
from app.models import client, invoice, item, payment, user, expense, email_queue, email_receipt, recurrent_bill


def reset_database():
    """Drop all tables and recreate from models"""

    print("⚠️  WARNING: This will delete ALL data in the database!")
    print("📁 Database:", engine.url)

    confirmation = input("\nType 'RESET' to confirm: ")

    if confirmation != "RESET":
        print("❌ Reset cancelled")
        return

    print("\n🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")

    print("\n📦 Creating tables from models...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created")

    print("\n🎉 Database reset complete!")
    print("   - Invoice table now has 'status' column")
    print("   - All tables recreated with latest schema")


if __name__ == "__main__":
    reset_database()
