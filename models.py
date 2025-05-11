from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import base64
from extensions import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to database connections
    connections = db.relationship('DatabaseConnection', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set password hash from plaintext password"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check if plaintext password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class DatabaseConnection(db.Model):
    """Model to store database connection information"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    host = db.Column(db.String(128), nullable=False)
    port = db.Column(db.Integer, default=3306)
    username = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    database_name = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add database type with MySQL as default
    db_type = db.Column(db.String(20), default='mysql', nullable=False)
    
    # Relationship to queries
    queries = db.relationship('Query', backref='connection', lazy=True)
    
    def set_password(self, password):
        """Encrypt the database password using Fernet symmetric encryption"""
        # Generate a key for encryption
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        encrypted_pw = cipher_suite.encrypt(password.encode())
        
        # Store both the key and encrypted password in the hash field
        # Format: key:encrypted_password
        self.password_hash = f"{key.decode()}:{encrypted_pw.decode()}"
    
    def get_password(self):
        """Decrypt the database password for connection using the stored key"""
        if not self.password_hash:
            return ''
            
        # If the password doesn't contain the separator, it might be an unencrypted password
        # (such as during testing or from old records)
        if ':' not in self.password_hash:
            return self.password_hash
            
        # Split the stored value to get key and encrypted password
        try:
            key_str, encrypted_pw = self.password_hash.split(':', 1)
            
            # Recreate the Fernet cipher with the stored key
            cipher_suite = Fernet(key_str.encode())
            # Decrypt the password
            decrypted_pw = cipher_suite.decrypt(encrypted_pw.encode()).decode()
            return decrypted_pw
        except Exception as e:
            # If decryption fails, return the raw password hash
            # This happens when migrating from an old system or when the encryption key is corrupted
            print(f"Error decrypting password (using raw password instead): {str(e)}")
            # For backward compatibility, return the original string which may be the plain password
            return self.password_hash
    
    @property
    def is_postgresql(self):
        """Check if this is a PostgreSQL connection"""
        return self.db_type.lower() == 'postgresql'
    
    @property 
    def is_mysql(self):
        """Check if this is a MySQL connection"""
        return self.db_type.lower() == 'mysql'
    
    def __repr__(self):
        return f'<DatabaseConnection {self.name} ({self.db_type})>'

class Query(db.Model):
    """Model to store natural language queries and SQL translations"""
    id = db.Column(db.Integer, primary_key=True)
    natural_language = db.Column(db.Text, nullable=False)
    sql_query = db.Column(db.Text, nullable=True)
    result = db.Column(db.Text, nullable=True)
    natural_language_result = db.Column(db.Text, nullable=True)
    connection_id = db.Column(db.Integer, db.ForeignKey('database_connection.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Query {self.id}>'
