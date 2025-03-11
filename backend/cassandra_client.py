from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import os
import uuid
import bcrypt
from datetime import datetime, timedelta
import jwt
import logging
from cassandra.policies import DCAwareRoundRobinPolicy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CassandraClient:
    def __init__(self):
        try:
            # Get configuration from environment
            username = os.getenv('CASSANDRA_USER', 'cassandra')
            password = os.getenv('CASSANDRA_PASSWORD', 'cassandra')
            host = os.getenv('CASSANDRA_HOST', '127.0.0.1')
            port = int(os.getenv('CASSANDRA_PORT', 9042))
            
            logger.info(f"Connecting to Cassandra at {host}:{port}")
            
            # Connection parameters
            cluster_params = {
                'contact_points': [host],
                'port': port,
                'protocol_version': 4  # More compatible version
            }
            
            # Only add auth_provider if we're not connecting to the local development Cassandra
            # which might not have authentication enabled
            if host != '127.0.0.1' or os.getenv('CASSANDRA_AUTH_REQUIRED', 'false').lower() == 'true':
                auth_provider = PlainTextAuthProvider(username=username, password=password)
                cluster_params['auth_provider'] = auth_provider
                
            self.cluster = Cluster(**cluster_params)
            self.session = self.cluster.connect()
            
            # Create keyspace if it doesn't exist
            self.session.execute("""
                CREATE KEYSPACE IF NOT EXISTS vectorshift
                WITH replication = {
                    'class': 'SimpleStrategy',
                    'replication_factor': 1
                }
            """)
            
            self.session.set_keyspace('vectorshift')
            
            # Create tables if they don't exist
            self.session.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id uuid PRIMARY KEY,
                    email text,
                    password_hash text,
                    created_at timestamp,
                    updated_at timestamp
                )
            """)
            
            self.session.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    reset_token text PRIMARY KEY,
                    user_id uuid,
                    expires_at timestamp
                )
            """)
            
            logger.info("Cassandra connection established and tables verified.")
        except Exception as e:
            logger.error(f"Error connecting to Cassandra: {e}")
            raise

    def create_user(self, email: str, password: str) -> uuid.UUID:
        try:
            # Check if user already exists
            rows = self.session.execute("SELECT id FROM users WHERE email = %s ALLOW FILTERING", (email,))
            if rows.one():
                raise ValueError("User already exists")

            # Hash password
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # Create user
            user_id = uuid.uuid4()
            now = datetime.utcnow()
            
            self.session.execute(
                """
                INSERT INTO users (id, email, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, email, password_hash, now, now)
            )
            logger.info(f"User {email} created successfully.")
            return user_id
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    def verify_user(self, email: str, password: str) -> dict:
        try:
            rows = self.session.execute("SELECT id, password_hash FROM users WHERE email = %s ALLOW FILTERING", (email,))
            user = rows.one()
            
            if not user:
                raise ValueError("User not found")
                
            if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                raise ValueError("Invalid password")
                
            token = jwt.encode(
                {
                    'user_id': str(user.id),
                    'exp': datetime.utcnow() + timedelta(days=1)
                },
                os.getenv('JWT_SECRET', 'your-secret-key'),
                algorithm='HS256'
            )
            
            return {'user_id': str(user.id), 'token': token}
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            raise

    def create_password_reset_token(self, email: str) -> str:
        try:
            rows = self.session.execute("SELECT id FROM users WHERE email = %s ALLOW FILTERING", (email,))
            user = rows.one()
            
            if not user:
                raise ValueError("User not found")
                
            token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            self.session.execute(
                """
                INSERT INTO password_resets (reset_token, user_id, expires_at)
                VALUES (%s, %s, %s)
                """,
                (token, user.id, expires_at)
            )
            
            logger.info(f"Password reset token generated for {email}.")
            return token
        except Exception as e:
            logger.error(f"Error generating password reset token: {e}")
            raise

    def reset_password(self, token: str, new_password: str) -> bool:
        try:
            rows = self.session.execute("SELECT user_id, expires_at FROM password_resets WHERE reset_token = %s", (token,))
            reset_token = rows.one()
            
            if not reset_token or reset_token.expires_at < datetime.utcnow():
                raise ValueError("Invalid or expired token")
                
            password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            
            self.session.execute(
                """
                UPDATE users
                SET password_hash = %s, updated_at = %s
                WHERE id = %s
                """,
                (password_hash, datetime.utcnow(), reset_token.user_id)
            )
            
            self.session.execute("DELETE FROM password_resets WHERE reset_token = %s", (token,))
            
            logger.info("Password reset successful.")
            return True
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            raise

    def close(self):
        self.cluster.shutdown()
        logger.info("Cassandra connection closed.")