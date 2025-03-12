from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import os
from dotenv import load_dotenv

load_dotenv()

def create_keyspace_and_tables():
    # Get Cassandra configuration from environment variables
    host = os.getenv('CASSANDRA_HOST', 'localhost')
    port = int(os.getenv('CASSANDRA_PORT', '9042'))
    keyspace = os.getenv('CASSANDRA_KEYSPACE', 'vectorshift')
    user = os.getenv('CASSANDRA_USER')
    password = os.getenv('CASSANDRA_PASSWORD')

    try:
        # Connect to Cassandra
        auth_provider = None
        if user and password:
            auth_provider = PlainTextAuthProvider(username=user, password=password)

        cluster = Cluster([host], port=port, auth_provider=auth_provider)
        session = cluster.connect()

        # Create keyspace
        print(f"Creating keyspace {keyspace} if it doesn't exist...")
        session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {keyspace}
            WITH REPLICATION = {{
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }}
        """)

        # Switch to the keyspace
        session.set_keyspace(keyspace)

        # Create users table
        print("Creating users table...")
        session.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email text PRIMARY KEY,
                password_hash text,
                created_at timestamp
            )
        """)

        # Create password_reset_tokens table
        print("Creating password_reset_tokens table...")
        session.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                user_email text,
                reset_token text,
                created_at timestamp,
                PRIMARY KEY (user_email, reset_token)
            )
        """)

        # Create user_credentials table
        print("Creating user_credentials table...")
        session.execute("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                user_id text,
                provider text,
                access_token text,
                refresh_token text,
                expires_at timestamp,
                created_at timestamp,
                metadata map<text, text>,
                PRIMARY KEY (user_id, provider)
            )
        """)

        # Create user_integrations table
        print("Creating user_integrations table...")
        session.execute("""
            CREATE TABLE IF NOT EXISTS user_integrations (
                user_id text,
                provider text,
                org_id text,
                status text,
                last_sync timestamp,
                settings map<text, text>,
                PRIMARY KEY (user_id, provider)
            )
        """)

        # Create integration_items table
        print("Creating integration_items table...")
        session.execute("""
            CREATE TABLE IF NOT EXISTS integration_items (
                user_id text,
                provider text,
                item_id text,
                name text,
                item_type text,
                url text,
                creation_time timestamp,
                last_modified_time timestamp,
                parent_id text,
                metadata map<text, text>,
                PRIMARY KEY ((user_id, provider), item_id)
            )
        """)

        # Create user_profiles table
        print("Creating user_profiles table...")
        session.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                email text PRIMARY KEY,
                full_name text,
                display_name text,
                avatar_url text,
                company text,
                job_title text,
                timezone text,
                preferences map<text, text>,
                updated_at timestamp
            )
        """)

        print("Database initialization completed successfully!")

    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
    finally:
        if 'cluster' in locals():
            cluster.shutdown()

if __name__ == "__main__":
    create_keyspace_and_tables()
