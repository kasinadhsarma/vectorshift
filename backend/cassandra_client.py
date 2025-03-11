from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from datetime import datetime
import os
from typing import List, Dict, Optional, Any
import jwt
import bcrypt
from datetime import datetime, timedelta

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
        self.session = None
        self.cluster = None

    async def connect(self):
        """Connect to Cassandra database"""
        try:
            auth_provider = None
            if self.user and self.password:
                auth_provider = PlainTextAuthProvider(
                    username=self.user,
                    password=self.password
                )

            self.cluster = Cluster(
                [self.host],
                port=self.port,
                auth_provider=auth_provider
            )
            self.session = self.cluster.connect(self.keyspace)
        except Exception as e:
            print(f"Error connecting to Cassandra: {str(e)}")
            raise

    async def close(self):
        """Close the Cassandra connection"""
        if self.cluster:
            self.cluster.shutdown()

    async def get_session(self):
        """Get or create a Cassandra session"""
        if not self.session:
            await self.connect()
        return self.session

    async def get_user_integrations(self, user_id: str) -> List[Dict]:
        """Get all integrations for a specific user"""
        try:
            if not self.session:
                await self.connect()
            
            # Query to get user's integrations
            query = """
            SELECT name, status, last_sync, workspace_count, settings
            FROM user_integrations
            WHERE user_id = %s
            """
            rows = self.session.execute(query, [user_id])
            
            integrations = []
            for row in rows:
                integration = {
                    "name": row.name,
                    "status": row.status,
                    "last_sync": row.last_sync,
                    "workspace_count": row.workspace_count,
                    "settings": row.settings
                }
                integrations.append(integration)
                
            return integrations
        except Exception as e:
            print(f"Error getting user integrations: {str(e)}")
            return []

    async def update_integration_status(self, user_id: str, integration_name: str, status: str):
        """Update the status of a specific integration"""
        try:
            if not self.session:
                await self.connect()
            
            query = """
            UPDATE user_integrations
            SET status = %s, last_sync = %s
            WHERE user_id = %s AND name = %s
            """
            self.session.execute(query, [status, datetime.now(), user_id, integration_name])
            
            return True
        except Exception as e:
            print(f"Error updating integration status: {str(e)}")
            return False

    async def add_user_integration(self, user_id: str, integration_name: str, settings: Dict):
        """Add a new integration for a user"""
        try:
            if not self.session:
                await self.connect()
            
            query = """
            INSERT INTO user_integrations
            (user_id, name, status, last_sync, workspace_count, settings)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.session.execute(query, [
                user_id,
                integration_name,
                'active',
                datetime.now(),
                0,  # Initial workspace count
                settings
            ])
            
            return True
        except Exception as e:
            print(f"Error adding user integration: {str(e)}")
            return False

    async def store_user_credentials(self, user_id: str, credentials: Dict):
        """Store user credentials in the database"""
        try:
            if not self.session:
                await self.connect()
                
            query = """
            INSERT INTO user_credentials (user_id, provider, credentials, created_at)
            VALUES (%s, %s, %s, %s)
            """
            self.session.execute(query, [
                user_id,
                credentials.get('provider', 'google'),
                credentials,
                datetime.now()
            ])
            return True
        except Exception as e:
            print(f"Error storing user credentials: {str(e)}")
            return False

    async def create_user(self, email: str, password: str) -> str:
        """Create a new user"""
        try:
            if not self.session:
                await self.connect()

            # Check if user already exists
            query = "SELECT email FROM users WHERE email = %s"
            rows = self.session.execute(query, [email])
            if len(list(rows)) > 0:
                raise ValueError("User already exists")

            # Hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

            # Insert user
            query = """
            INSERT INTO users (email, password_hash, created_at)
            VALUES (%s, %s, %s)
            """
            self.session.execute(query, [
                email,
                hashed.decode('utf-8'),
                datetime.now()
            ])

            return email
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            raise

    async def verify_user(self, email: str, password: str) -> Dict[str, Any]:
        """Verify user credentials and return auth token"""
        try:
            if not self.session:
                await self.connect()

            # Get user
            query = "SELECT email, password_hash FROM users WHERE email = %s"
            rows = self.session.execute(query, [email])
            user = next(iter(rows), None)

            if not user:
                raise ValueError("Invalid email or password")

            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                raise ValueError("Invalid email or password")

            # Generate access token
            token = self._create_access_token({"sub": email})

            return {
                "access_token": token,
                "token_type": "bearer"
            }
        except Exception as e:
            print(f"Error verifying user: {str(e)}")
            raise

    async def create_password_reset_token(self, email: str) -> str:
        """Create a password reset token"""
        try:
            if not self.session:
                await self.connect()

            # Verify user exists
            query = "SELECT email FROM users WHERE email = %s"
            rows = self.session.execute(query, [email])
            if not next(iter(rows), None):
                raise ValueError("User not found")

            # Generate token
            token = self._create_access_token(
                {"sub": email, "type": "reset"},
                expires_delta=timedelta(minutes=15)
            )

            # Store token
            query = """
            INSERT INTO password_reset_tokens (email, token, created_at)
            VALUES (%s, %s, %s)
            """
            self.session.execute(query, [email, token, datetime.now()])

            return token
        except Exception as e:
            print(f"Error creating reset token: {str(e)}")
            raise

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password using reset token"""
        try:
            if not self.session:
                await self.connect()

            # Verify and decode token
            try:
                payload = jwt.decode(token, self.JWT_SECRET, algorithms=[self.JWT_ALGORITHM])
                email = payload["sub"]
                if payload.get("type") != "reset":
                    raise ValueError("Invalid token type")
            except jwt.PyJWTError:
                raise ValueError("Invalid or expired token")

            # Hash new password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt)

            # Update password
            query = """
            UPDATE users
            SET password_hash = %s
            WHERE email = %s
            """
            self.session.execute(query, [hashed.decode('utf-8'), email])

            # Delete used token
            query = "DELETE FROM password_reset_tokens WHERE token = %s"
            self.session.execute(query, [token])

            return True
        except Exception as e:
            print(f"Error resetting password: {str(e)}")
            raise

    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)

    async def get_user_credentials(self, user_id: str) -> Optional[Dict]:
        """Retrieve user credentials from the database"""
        try:
            if not self.session:
                await self.connect()
                
            query = """
            SELECT credentials
            FROM user_credentials
            WHERE user_id = %s
            LIMIT 1
            """
            rows = self.session.execute(query, [user_id])
            row = next(iter(rows), None)
            
            if row:
                return row.credentials
            return None
        except Exception as e:
            print(f"Error getting user credentials: {str(e)}")
            return None
