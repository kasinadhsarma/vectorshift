from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
from cassandra.auth import PlainTextAuthProvider
import os
from dotenv import load_dotenv

load_dotenv()

class CassandraClient:
    def __init__(self):
        self.host = os.getenv('CASSANDRA_HOST', 'localhost')
        self.port = int(os.getenv('CASSANDRA_PORT', '9042'))
        self.keyspace = os.getenv('CASSANDRA_KEYSPACE', 'vectorshift')
        
        # Configure execution profile
        profile = ExecutionProfile(
            load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy()),
            request_timeout=60
        )
        
        # Initialize cluster
        self.cluster = Cluster(
            contact_points=[self.host],
            port=self.port,
            execution_profiles={EXEC_PROFILE_DEFAULT: profile},
            protocol_version=4
        )
        
        # Create session
        self.session = self.cluster.connect()
        
        # Create keyspace if it doesn't exist
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
            WITH replication = {{
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }}
        """)
        
        # Set keyspace
        self.session.set_keyspace(self.keyspace)
        
        # Initialize tables
        self._init_tables()
    
    def _init_tables(self):
        """Initialize required tables."""
        # Users table
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id text PRIMARY KEY,
                email text,
                password_hash text,
                created_at timestamp,
                updated_at timestamp
            )
        """)
        
        # User profiles table
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id text PRIMARY KEY,
                full_name text,
                avatar_url text,
                company text,
                job_title text,
                timezone text,
                preferences map<text, text>,
                updated_at timestamp
            )
        """)
        
        # User integrations table
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS user_integrations (
                user_id text,
                provider text,
                org_id text,
                status text,
                last_sync timestamp,
                PRIMARY KEY ((user_id, provider))
            )
        """)
    
    def execute(self, query, values=None):
        """Execute a CQL query."""
        try:
            if values:
                return self.session.execute(query, values)
            return self.session.execute(query)
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            raise
    
    def close(self):
        """Close cluster connection."""
        if self.cluster:
            self.cluster.shutdown()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()
