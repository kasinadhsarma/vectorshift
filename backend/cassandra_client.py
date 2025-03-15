from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider
from datetime import datetime
import os
from typing import List, Dict, Optional, Any
import jwt
import bcrypt
import hashlib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CassandraClient:
    JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    
    def __init__(self):
        self.host = os.getenv('CASSANDRA_HOST', 'localhost')
        self.port = int(os.getenv('CASSANDRA_PORT', '9042'))
        self.keyspace = os.getenv('CASSANDRA_KEYSPACE', 'vectorshift')
        self.user = os.getenv('CASSANDRA_USER')
        self.password = os.getenv('CASSANDRA_PASSWORD')
        self._session = None
        self._cluster = None
        self._connect_sync()  # Initialize connection during startup

    def hash_user_id(self, user_id: str) -> str:
        """Create a hash of the user ID for URL safety"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:12]

    def _connect_sync(self) -> None:
        """Synchronous connect method for initialization"""
        try:
            if self._session:
                return

            auth_provider = None
            if self.user and self.password:
                auth_provider = PlainTextAuthProvider(
                    username=self.user,
                    password=self.password
                )

            self._cluster = Cluster(
                [self.host],
                port=self.port,
                auth_provider=auth_provider
            )
            self._session = self._cluster.connect(self.keyspace)
            logger.info("Successfully connected to Cassandra")
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {str(e)}")
            raise

    async def connect(self) -> Session:
        """Async connect method for runtime connections"""
        if self._session:
            return self._session
        self._connect_sync()
        return self._session

    async def close(self):
        """Close the Cassandra connection"""
        if self._cluster:
            self._cluster.shutdown()
            self._cluster = None
            self._session = None

    async def get_session(self) -> Session:
        """Get or create a Cassandra session"""
        if not self._session:
            await self.connect()
        return self._session

    @property
    def session(self) -> Session:
        """Get the current session"""
        if not self._session:
            self._connect_sync()
        return self._session

    # Your existing methods remain the same...
    # (The rest of the methods remain unchanged)

# Create a global instance of CassandraClient
cassandra_client = CassandraClient()

# Export the session for use in other modules
cassandra_session = cassandra_client.session

# Log successful initialization
logger.info("CassandraClient initialized successfully")
