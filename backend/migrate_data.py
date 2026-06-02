#!/usr/bin/env python3
"""
Migration script to transfer user data between PostgreSQL databases
This script copies user data, emergency contacts, and travel history between PostgreSQL databases
"""

import psycopg2
from urllib.parse import urlparse, unquote
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def parse_db_url(db_url):
    """
    Parse database URL to extract connection components
    Now only handles PostgreSQL URLs
    """
    parsed = urlparse(db_url)
    if not db_url.startswith("postgresql"):
        raise ValueError(f"Expected PostgreSQL URL, got: {db_url}")
    
    # Handle URL encoding in password (like %25 for %)
    password = parsed.password
    if password:
        password = unquote(password)  # Decode URL-encoded characters
    
    return {
        'host": parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:],  # Remove leading slash
        'username': parsed.username,
        'password': password
    }

def migrate_users_postgres_to_postgres(source_db_url=None, dest_db_url=None):
    """
    Migrate user data from one PostgreSQL database to another PostgreSQL database
    """
    # Get database URLs from environment or parameters
    if source_db_url is None:
        source_db_url = os.getenv("SOURCE_DB_URL", "postgresql+asyncpg://face_user:Dingle100%25143@localhost/face_recognition")
    if dest_db_url is None:
        dest_db_url = os.getenv("DEST_DB_URL", "postgresql+asyncpg://face_user:Dingle100%25143@localhost/face_recognition_backup")

    # Remove the asyncpg part for psycopg2
    source_postgres_url = source_db_url.replace("postgresql+asyncpg://", "postgresql://")
    dest_postgres_url = dest_db_url.replace("postgresql+asyncpg://", "postgresql://")

    # Parse the URLs
    source_config = parse_db_url(source_postgres_url)
    dest_config = parse_db_url(dest_postgres_url)

    print("Starting migration from PostgreSQL to PostgreSQL...")
    print(f"Source (PostgreSQL): {source_config['host']}:{source_config['port'] or 5432}/{source_config['database']}")
    print(f"Destination (PostgreSQL): {dest_config['host']}:{dest_config['port'] or 5432}/{dest_config['database']}")

    # Connect to source PostgreSQL
    source_conn = psycopg2.connect(
        host=source_config['host'],
        port=source_config['port'] or 5432,
        database=source_config['database'],
        user=source_config['username'],
        password=source_config['password']
    )
    source_cursor = source_conn.cursor()

    # Connect to destination PostgreSQL
    dest_conn = psycopg2.connect(
        host=dest_config['host'],
        port=dest_config['port'] or 5432,
        database=dest_config['database'],
        user=dest_config['username'],
        password=dest_config['password']
    )
    dest_cursor = dest_conn.cursor()

    try:
        # Fetch all users from source PostgreSQL
        source_cursor.execute("SELECT * FROM users")
        users = source_cursor.fetchall()
        user_columns = [desc[0] for desc in source_cursor.description]

        print(f"Found {len(users)} users in source PostgreSQL database")

        # Clear existing users in destination PostgreSQL (if any)
        dest_cursor.execute("DELETE FROM users;")

        # Insert users into destination PostgreSQL
        for user in users:
            # Create INSERT statement dynamically based on columns
            placeholders = ', '.join(['%s'] * len(user))
            columns_str = ', '.join(user_columns)
            insert_query = f"INSERT INTO users ({columns_str}) VALUES ({placeholders})"
            dest_cursor.execute(insert_query, user)

        print(f"Successfully migrated {len(users)} users to destination PostgreSQL")

        # Fetch all emergency contacts from source PostgreSQL
        source_cursor.execute("SELECT * FROM emergency_contacts")
        contacts = source_cursor.fetchall()
        contact_columns = [desc[0] for desc in source_cursor.description]

        print(f"Found {len(contacts)} emergency contacts in source PostgreSQL database")

        # Clear existing contacts in destination PostgreSQL (if any)
        dest_cursor.execute("DELETE FROM emergency_contacts;")

        # Insert contacts into destination PostgreSQL
        for contact in contacts:
            # Create INSERT statement dynamically based on columns
            placeholders = ', '.join(['%s'] * len(contact))
            columns_str = ', '.join(contact_columns)
            insert_query = f"INSERT INTO emergency_contacts ({columns_str}) VALUES ({placeholders})"
            dest_cursor.execute(insert_query, contact)

        print(f"Successfully migrated {len(contacts)} emergency contacts to destination PostgreSQL")

        # Fetch all travel history from source PostgreSQL
        source_cursor.execute("SELECT * FROM travel_history")
        travels = source_cursor.fetchall()
        travel_columns = [desc[0] for desc in source_cursor.description]

        print(f"Found {len(travels)} travel history records in source PostgreSQL database")

        # Clear existing travel history in destination PostgreSQL (if any)
        dest_cursor.execute("DELETE FROM travel_history;")

        # Insert travel history into destination PostgreSQL
        for travel in travels:
            # Create INSERT statement dynamically based on columns
            placeholders = ', '.join(['%s'] * len(travel))
            columns_str = ', '.join(travel_columns)
            insert_query = f"INSERT INTO travel_history ({columns_str}) VALUES ({placeholders})"
            dest_cursor.execute(insert_query, travel)

        print(f"Successfully migrated {len(travels)} travel history records to destination PostgreSQL")

        # Commit all changes to destination
        dest_conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        dest_conn.rollback()
        raise
    finally:
        # Close connections
        source_conn.close()
        source_cursor.close()
        dest_cursor.close()
        dest_conn.close()

def verify_migration(source_db_url=None, dest_db_url=None):
    """
    Verify that data was migrated correctly
    """
    if source_db_url is None:
        source_db_url = os.getenv("SOURCE_DB_URL", "postgresql+asyncpg://face_user:Dingle100%25143@localhost/face_recognition")
    if dest_db_url is None:
        dest_db_url = os.getenv("DEST_DB_URL", "postgresql+asyncpg://face_user:Dingle100%25143@localhost/face_recognition_backup")

    # Remove the asyncpg part for psycopg2
    source_postgres_url = source_db_url.replace("postgresql+asyncpg://", "postgresql://")
    dest_postgres_url = dest_db_url.replace("postgresql+asyncpg://", "postgresql://")

    # Parse the URLs
    source_config = parse_db_url(source_postgres_url)
    dest_config = parse_db_url(dest_postgres_url)

    # Connect to source PostgreSQL
    source_conn = psycopg2.connect(
        host=source_config['host'],
        port=source_config['port'] or 5432,
        database=source_config['database'],
        user=source_config['username'],
        password=source_config['password']
    )
    source_cursor = source_conn.cursor()

    # Connect to destination PostgreSQL
    dest_conn = psycopg2.connect(
        host=dest_config['host'],
        port=dest_config['port'] or 5432,
        database=dest_config['database'],
        user=dest_config['username'],
        password=dest_config['password']
    )
    dest_cursor = dest_conn.cursor()

    try:
        # Count records in both databases
        source_cursor.execute("SELECT COUNT(*) FROM users")
        source_user_count = source_cursor.fetchone()[0]

        dest_cursor.execute("SELECT COUNT(*) FROM users")
        dest_user_count = dest_cursor.fetchone()[0]

        source_cursor.execute("SELECT COUNT(*) FROM emergency_contacts")
        source_contact_count = source_cursor.fetchone()[0]

        dest_cursor.execute("SELECT COUNT(*) FROM emergency_contacts")
        dest_contact_count = dest_cursor.fetchone()[0]

        source_cursor.execute("SELECT COUNT(*) FROM travel_history")
        source_travel_count = source_cursor.fetchone()[0]

        dest_cursor.execute("SELECT COUNT(*) FROM travel_history")
        dest_travel_count = dest_cursor.fetchone()[0]

        print("\nVerification Results:")
        print(f"Users - Source: {source_user_count}, Destination: {dest_user_count}")
        print(f"Emergency Contacts - Source: {source_contact_count}, Destination: {dest_contact_count}")
        print(f"Travel History - Source: {source_travel_count}, Destination: {dest_travel_count}")

        if (source_user_count == dest_user_count and 
            source_contact_count == dest_contact_count and 
            source_travel_count == dest_travel_count):
            print("\n✓ Verification successful! Data counts match between databases.")
        else:
            print("\n✗ Verification failed! Data counts don't match.")

    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        # Close connections
        source_conn.close()
        source_cursor.close()
        dest_cursor.close()
        dest_conn.close()

if __name__ == "__main__":
    print("PostgreSQL to PostgreSQL Data Migration Tool")
    print("=" * 45)

    # Run both migrate and verify actions automatically
    try:
        migrate_users_postgres_to_postgres()
        print("\n" + "="*45)
        verify_migration()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)