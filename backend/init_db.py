from cassandra.cluster import Cluster, NoHostAvailable
from cassandra.auth import PlainTextAuthProvider
import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def create_keyspace_and_tables():
    """Initialize Cassandra keyspace and tables"""
    # Get Cassandra configuration from environment variables
    host = os.getenv('CASSANDRA_HOST', 'localhost')
    port = int(os.getenv('CASSANDRA_PORT', '9042'))
    keyspace = os.getenv('CASSANDRA_KEYSPACE', 'vectorshift')
    user = os.getenv('CASSANDRA_USER')
    password = os.getenv('CASSANDRA_PASSWORD')

    cluster = None
    try:
        # Connect to Cassandra
        auth_provider = None
        if user and password:
            auth_provider = PlainTextAuthProvider(username=user, password=password)

        logger.info(f"Connecting to Cassandra at {host}:{port}...")
        cluster = Cluster([host], port=port, auth_provider=auth_provider)
        session = cluster.connect()

        # Create keyspace
        logger.info(f"Creating keyspace {keyspace} if it doesn't exist...")
        session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {keyspace}
            WITH REPLICATION = {{
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }}
        """)

        # Switch to the keyspace
        session.set_keyspace(keyspace)

        # Define tables with their creation queries
        tables = {
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    email text PRIMARY KEY,
                    password_hash text,
                    auth_provider text,
                    google_id text,
                    created_at timestamp,
                    last_login timestamp
                )
            """,
            "password_reset_tokens": """
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    user_email text,
                    reset_token text,
                    created_at timestamp,
                    PRIMARY KEY (user_email, reset_token)
                )
            """,
            "user_credentials": """
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
            """,
            "user_integrations": """
                CREATE TABLE IF NOT EXISTS user_integrations (
                    user_id text,
                    provider text,
                    org_id text,
                    status text,
                    last_sync timestamp,
                    settings map<text, text>,
                    PRIMARY KEY (user_id, provider)
                )
            """,
            "integration_items": """
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
            """,
            "user_profiles": """
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
            """
        }

        # Create tables
        for table_name, query in tables.items():
            try:
                logger.info(f"Creating {table_name} table...")
                session.execute(query)
                logger.info(f"{table_name} table created successfully.")
            except Exception as e:
                logger.error(f"Error creating {table_name} table: {str(e)}")
                raise

        # Verify tables were created
        keyspace_tables = session.execute("""
            SELECT table_name FROM system_schema.tables
            WHERE keyspace_name = %s
        """, [keyspace])
        
        created_tables = {row.table_name for row in keyspace_tables}
        expected_tables = set(tables.keys())
        
        if not expected_tables.issubset(created_tables):
            missing_tables = expected_tables - created_tables
            raise Exception(f"Failed to create tables: {', '.join(missing_tables)}")

        logger.info("Database initialization completed successfully!")
        return True

    except NoHostAvailable as e:
        logger.error(f"Could not connect to Cassandra: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False
    finally:
        if cluster:
            logger.info("Closing Cassandra connection...")
            cluster.shutdown()

if __name__ == "__main__":
    import asyncio
    
    # Run the initialization
    success = asyncio.run(create_keyspace_and_tables())
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
