import sqlite3
import json
from datetime import datetime
import os

def convert_db_to_json(db_path='emergency_system.db', output_path='emergency_system.json'):
    """
    Convert SQLite database to JSON format
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Dictionary to store all data
    db_data = {}
    
    for table in tables:
        table_name = table[0]
        print(f"Processing table: {table_name}")
        
        # Skip system tables if present
        if table_name.startswith('sqlite_') or table_name == 'alembic_version':
            continue
            
        # Get all records from the table
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Convert rows to dictionaries
        table_data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                
                # Handle datetime fields (they might be stored as strings)
                if isinstance(value, str):
                    try:
                        # Try to parse as datetime if it looks like a datetime string
                        if 'created_at' in column or 'updated_at' in column or 'expires_at' in column:
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        pass  # Not a datetime string, keep as is
                
                # Handle None values
                if value is None:
                    row_dict[column] = None
                else:
                    row_dict[column] = value
                    
            table_data.append(row_dict)
        
        db_data[table_name] = table_data
    
    # Close the connection
    conn.close()
    
    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Database converted to JSON successfully! Output file: {output_path}")
    print(f"Tables processed: {list(db_data.keys())}")
    return db_data

if __name__ == "__main__":
    # Activate the virtual environment first
    import sys
    import subprocess
    
    # Check if we're in the right directory and convert the database
    if os.path.exists('emergency_system.db'):
        convert_db_to_json()
    else:
        print("emergency_system.db not found in current directory!")