"""
Encryptum Clone - Core Encryption Module
Handles AES-256 encryption/decryption with PBKDF2 key derivation
"""

import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

class EncryptumCrypto:
    """Core encryption handler for Encryptum clone"""
    
    def __init__(self, iterations=100000):
        self.iterations = iterations
        self.logger = logging.getLogger(__name__)
    
    def generate_key_from_password(self, password: str, salt: bytes = None) -> tuple:
        """
        Generate encryption key from password using PBKDF2
        
        Args:
            password: User password
            salt: Salt bytes (generated if None)
            
        Returns:
            tuple: (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def encrypt_file(self, file_path: str, password: str) -> dict:
        """
        Encrypt file and return encrypted data + metadata
        
        Args:
            file_path: Path to file to encrypt
            password: Encryption password
            
        Returns:
            dict: Encryption result with metadata
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Generate key and salt
            key, salt = self.generate_key_from_password(password)
            fernet = Fernet(key)
            
            # Read and encrypt file
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            if len(file_data) == 0:
                raise ValueError("Cannot encrypt empty file")
            
            encrypted_data = fernet.encrypt(file_data)
            
            # Calculate hash for verification
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            self.logger.info(f"File encrypted successfully: {os.path.basename(file_path)}")
            
            return {
                'encrypted_data': encrypted_data,
                'salt': salt,
                'original_hash': file_hash,
                'original_name': os.path.basename(file_path),
                'original_size': len(file_data),
                'encrypted_size': len(encrypted_data)
            }
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise Exception(f"Encryption failed: {str(e)}")
    
    def decrypt_file(self, encrypted_data: bytes, password: str, salt: bytes) -> bytes:
        """
        Decrypt file data
        
        Args:
            encrypted_data: Encrypted file bytes
            password: Decryption password
            salt: Salt used for key derivation
            
        Returns:
            bytes: Decrypted file data
        """
        try:
            key, _ = self.generate_key_from_password(password, salt)
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            self.logger.info("File decrypted successfully")
            return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise Exception(f"Decryption failed: {str(e)}")
    
    def verify_file_integrity(self, decrypted_data: bytes, original_hash: str) -> bool:
        """
        Verify file integrity using hash
        
        Args:
            decrypted_data: Decrypted file data
            original_hash: Original file hash
            
        Returns:
            bool: True if integrity verified
        """
        current_hash = hashlib.sha256(decrypted_data).hexdigest()
        return current_hash == original_hash
