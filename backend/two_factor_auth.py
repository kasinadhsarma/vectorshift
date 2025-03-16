import base64
import os
import time
import hmac
import hashlib
import secrets
import qrcode
import io
from typing import Optional, Tuple
from fastapi import HTTPException

# TOTP (Time-based One-Time Password) implementation
class TOTP:
    def __init__(self, secret: Optional[str] = None, digits: int = 6, interval: int = 30, algorithm: str = 'sha1'):
        self.digits = digits
        self.interval = interval
        self.algorithm = algorithm
        self.secret = secret or self.generate_secret()
    
    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """Generate a random secret key."""
        return base64.b32encode(secrets.token_bytes(length)).decode('utf-8')
    
    def generate_totp(self, timestamp: Optional[int] = None) -> str:
        """Generate a TOTP code."""
        if timestamp is None:
            timestamp = int(time.time())
        
        # Calculate the counter value (number of time intervals since epoch)
        counter = int(timestamp / self.interval)
        counter_bytes = counter.to_bytes(8, byteorder='big')
        
        # Compute HMAC
        secret_bytes = base64.b32decode(self.secret)
        hmac_hash = hmac.new(secret_bytes, counter_bytes, getattr(hashlib, self.algorithm)).digest()
        
        # Dynamic truncation
        offset = hmac_hash[-1] & 0xf
        code = ((hmac_hash[offset] & 0x7f) << 24 |
                (hmac_hash[offset + 1] & 0xff) << 16 |
                (hmac_hash[offset + 2] & 0xff) << 8 |
                (hmac_hash[offset + 3] & 0xff))
        
        # Modulo and padding
        code = str(code % 10**self.digits).zfill(self.digits)
        return code
    
    def verify_totp(self, code: str, timestamp: Optional[int] = None, window: int = 1) -> bool:
        """Verify a TOTP code with a window for clock skew."""
        if timestamp is None:
            timestamp = int(time.time())
        
        for i in range(-window, window + 1):
            if self.generate_totp(timestamp + (i * self.interval)) == code:
                return True
        return False
    
    def get_provisioning_uri(self, account_name: str, issuer: str = 'VectorShift') -> str:
        """Generate an otpauth URI for QR codes."""
        return (f"otpauth://totp/{issuer}:{account_name}?"
                f"secret={self.secret}&issuer={issuer}"
                f"&algorithm={self.algorithm.upper()}&digits={self.digits}"
                f"&period={self.interval}")
    
    def generate_qr_code(self, account_name: str, issuer: str = 'VectorShift') -> bytes:
        """Generate a QR code for the TOTP."""
        uri = self.get_provisioning_uri(account_name, issuer)
        img = qrcode.make(uri)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()

# Function to setup 2FA for a user
async def setup_2fa(user_id: str, cassandra_client) -> Tuple[str, bytes]:
    """Set up 2FA for a user and return the secret and QR code."""
    # Generate a new TOTP object with a random secret
    totp = TOTP()
    
    # Store the secret in the database
    try:
        await cassandra_client.store_2fa_secret(user_id, totp.secret)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store 2FA secret: {str(e)}")
    
    # Get user email for the QR code
    user = await cassandra_client.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate QR code
    qr_code = totp.generate_qr_code(user.get('email', f"user_{user_id}"))
    
    return totp.secret, qr_code

# Function to verify 2FA code
async def verify_2fa(user_id: str, code: str, cassandra_client) -> bool:
    """Verify a 2FA code for a user."""
    try:
        # Get the user's secret from the database
        secret = await cassandra_client.get_2fa_secret(user_id)
        if not secret:
            raise HTTPException(status_code=404, detail="2FA not set up for this user")
        
        # Create a TOTP object with the stored secret
        totp = TOTP(secret=secret)
        
        # Verify the code
        return totp.verify_totp(code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify 2FA code: {str(e)}")

# Function to check if 2FA is enabled for a user
async def is_2fa_enabled(user_id: str, cassandra_client) -> bool:
    """Check if 2FA is enabled for a user."""
    try:
        secret = await cassandra_client.get_2fa_secret(user_id)
        return bool(secret)
    except Exception:
        return False

# Function to disable 2FA for a user
async def disable_2fa(user_id: str, cassandra_client) -> bool:
    """Disable 2FA for a user."""
    try:
        return await cassandra_client.remove_2fa_secret(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable 2FA: {str(e)}")
