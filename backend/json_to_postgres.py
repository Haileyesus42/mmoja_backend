#!/usr/bin/env python3
"""
Script to convert emergency_system.json to PostgreSQL database
"""

import json
import psycopg2
from urllib.parse import urlparse, unquote
import os
from dotenv import load_dotenv
import sys
from datetime import datetime

# Load environment variables
load_dotenv()

def parse_db_url(db_url):
    """
    Parse database URL to extract connection components
    """
    parsed = urlparse(db_url)
    if db_url.startswith("postgresql"):
        # Handle URL encoding in password (like %25 for %)
        password = parsed.password
        if password:
            password = unquote(password)  # Decode URL-encoded characters
        
        return {
            'host': parsed.hostname,
            'port': parsed.port,
            'database': parsed.path[1:],  # Remove leading slash
            'username': parsed.username,
            'password': password
        }
    else:
        raise ValueError(f"Expected PostgreSQL URL, got: {db_url}")

def create_tables_if_not_exist(cursor):
    """
    Create tables if they don't exist in PostgreSQL
    """
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            address TEXT,
            phone VARCHAR(50),
            email VARCHAR(255),
            current_city VARCHAR(255),
            current_country VARCHAR(255),
            hotel_name VARCHAR(255),
            current_location TEXT,
            gps_latitude VARCHAR(50),
            gps_longitude VARCHAR(50)
        );
    """)
    
    # Create emergency_contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            priority INTEGER NOT NULL,
            contact_name VARCHAR(255) NOT NULL,
            relationship VARCHAR(255),
            phone VARCHAR(50),
            whatsapp VARCHAR(50)
        );
    """)
    
    # Create travel_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            country VARCHAR(255) NOT NULL,
            city VARCHAR(255) NOT NULL,
            travel_date VARCHAR(50)
        );
    """)
    
    # Create user_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            token VARCHAR(255) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        );
    """)
    
    # Create emergency_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            contact_id INTEGER NOT NULL,
            call_sid VARCHAR(255),
            call_status VARCHAR(50),
            signal_type VARCHAR(50),
            emergency_context TEXT,
            transcript TEXT,
            call_duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

def json_to_postgres(json_file_path='emergency_system.json'):
    """
    Convert JSON data to PostgreSQL database
    """
    # Read JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get PostgreSQL database URL from environment
    face_db_url = os.getenv("FACE_DB_URL", "postgresql+asyncpg://face_user:Dingle100%25143@localhost/face_recognition")
    
    # Remove the asyncpg part for psycopg2
    postgres_url = face_db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Parse the URL
    postgres_config = parse_db_url(postgres_url)
    
    print("Starting JSON to PostgreSQL conversion...")
    print(f"Source (JSON): {json_file_path}")
    print(f"Destination (PostgreSQL): {postgres_config['host']}:{postgres_config['port'] or 5432}/{postgres_config['database']}")
    
    # Connect to PostgreSQL
    postgres_conn = psycopg2.connect(
        host=postgres_config['host'],
        port=postgres_config['port'] or 5432,  # Default to 5432 if not specified
        database=postgres_config['database'],
        user=postgres_config['username'],
        password=postgres_config['password']
    )
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Create tables if they don't exist
        create_tables_if_not_exist(postgres_cursor)
        
        # Clear existing data (optional - remove if you want to append)
        postgres_cursor.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
        postgres_cursor.execute("TRUNCATE TABLE emergency_contacts RESTART IDENTITY CASCADE;")
        postgres_cursor.execute("TRUNCATE TABLE travel_history RESTART IDENTITY CASCADE;")
        postgres_cursor.execute("TRUNCATE TABLE user_sessions RESTART IDENTITY CASCADE;")
        postgres_cursor.execute("TRUNCATE TABLE emergency_logs RESTART IDENTITY CASCADE;")
        
        # Insert users
        users = data.get('users', [])
        print(f"Found {len(users)} users in JSON file")
        
        for user in users:
            # Prepare the INSERT statement dynamically
            columns = list(user.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])  # Quote column names to handle reserved words
            insert_query = f'INSERT INTO users ({columns_str}) VALUES ({placeholders}) RETURNING id;'
            
            # Extract values in the same order as columns
            values = [user[col] for col in columns]
            
            postgres_cursor.execute(insert_query, values)
        
        print(f"Successfully inserted {len(users)} users into PostgreSQL")
        
        # Insert emergency contacts
        contacts = data.get('emergency_contacts', [])
        print(f"Found {len(contacts)} emergency contacts in JSON file")
        
        for contact in contacts:
            columns = list(contact.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])
            insert_query = f'INSERT INTO emergency_contacts ({columns_str}) VALUES ({placeholders}) RETURNING id;'
            
            values = [contact[col] for col in columns]
            
            postgres_cursor.execute(insert_query, values)
        
        print(f"Successfully inserted {len(contacts)} emergency contacts into PostgreSQL")
        
        # Insert travel history
        travels = data.get('travel_history', [])
        print(f"Found {len(travels)} travel history records in JSON file")
        
        for travel in travels:
            columns = list(travel.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])
            insert_query = f'INSERT INTO travel_history ({columns_str}) VALUES ({placeholders}) RETURNING id;'
            
            values = [travel[col] for col in columns]
            
            postgres_cursor.execute(insert_query, values)
        
        print(f"Successfully inserted {len(travels)} travel history records into PostgreSQL")
        
        # Insert user sessions (if any)
        sessions = data.get('user_sessions', [])
        print(f"Found {len(sessions)} user sessions in JSON file")
        
        for session in sessions:
            columns = list(session.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])
            insert_query = f'INSERT INTO user_sessions ({columns_str}) VALUES ({placeholders}) RETURNING id;'
            
            values = [session[col] for col in columns]
            
            postgres_cursor.execute(insert_query, values)
        
        print(f"Successfully inserted {len(sessions)} user sessions into PostgreSQL")
        
        # Insert emergency logs (if any)
        logs = data.get('emergency_logs', [])
        print(f"Found {len(logs)} emergency logs in JSON file")
        
        for log in logs:
            columns = list(log.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])
            insert_query = f'INSERT INTO emergency_logs ({columns_str}) VALUES ({placeholders}) RETURNING id;'
            
            values = [log[col] for col in columns]
            
            postgres_cursor.execute(insert_query, values)
        
        print(f"Successfully inserted {len(logs)} emergency logs into PostgreSQL")
        
        # Commit all changes
        postgres_conn.commit()
        print("JSON to PostgreSQL conversion completed successfully!")
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        postgres_conn.rollback()
        raise
    finally:
        # Close connection
        postgres_cursor.close()
        postgres_conn.close()

def verify_conversion():
    """
    Verify that data was converted correctly
    """
    # Get PostgreSQL database URL from environment
    face_db_url = os.getenv("FACE_DB_URL", "postgresql+asyncpg://face_user:Dingle100%25143@localhost/face_recognition")
    
    # Remove the asyncpg part for psycopg2
    postgres_url = face_db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Parse the URL
    postgres_config = parse_db_url(postgres_url)
    
    # Connect to PostgreSQL
    postgres_conn = psycopg2.connect(
        host=postgres_config['host'],
        port=postgres_config['port'] or 5432,  # Default to 5432 if not specified
        database=postgres_config['database'],
        user=postgres_config['username'],
        password=postgres_config['password']
    )
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Count records in PostgreSQL
        postgres_cursor.execute("SELECT COUNT(*) FROM users")
        postgres_user_count = postgres_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM emergency_contacts")
        postgres_contact_count = postgres_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM travel_history")
        postgres_travel_count = postgres_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM user_sessions")
        postgres_session_count = postgres_cursor.fetchone()[0]
        
        postgres_cursor.execute("SELECT COUNT(*) FROM emergency_logs")
        postgres_log_count = postgres_cursor.fetchone()[0]
        
        print("\nVerification Results:")
        print(f"Users: {postgres_user_count}")
        print(f"Emergency Contacts: {postgres_contact_count}")
        print(f"Travel History: {postgres_travel_count}")
        print(f"User Sessions: {postgres_session_count}")
        print(f"Emergency Logs: {postgres_log_count}")
        
        total_records = postgres_user_count + postgres_contact_count + postgres_travel_count + postgres_session_count + postgres_log_count
        print(f"\nTotal records in PostgreSQL: {total_records}")
            
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        # Close connection
        postgres_cursor.close()
        postgres_conn.close()

if __name__ == "__main__":
    print("JSON to PostgreSQL Conversion Tool")
    print("=" * 40)
    
    # Read JSON file path from command line argument or use default
    json_file = sys.argv[1] if len(sys.argv) > 1 else 'emergency_system.json'
    
    # Check if JSON file exists
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found!")
        sys.exit(1)
    
    # Run conversion and verification
    try:
        json_to_postgres(json_file)
        print("\n" + "="*40)
        verify_conversion()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)