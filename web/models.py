from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class RateQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    procedure_code = db.Column(db.String(20), nullable=False)
    query_date = db.Column(db.DateTime, default=datetime.utcnow)
    result_count = db.Column(db.Integer)
    cache_hit = db.Column(db.Boolean, default=False)
    
    # Index for faster lookups and analytics
    __table_args__ = (
        db.Index('idx_query_state_procedure', 'state', 'procedure_code'),
        db.Index('idx_query_date', 'query_date'),
    )

class CachedRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(2), nullable=False)
    procedure_code = db.Column(db.String(20), nullable=False)
    provider = db.Column(db.String(200))
    rate = db.Column(db.Numeric(10, 2))
    effective_date = db.Column(db.Date)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite indexes for faster lookups
    __table_args__ = (
        db.Index('idx_cache_state_procedure', 'state', 'procedure_code'),
        db.Index('idx_cache_access', 'access_count', 'last_accessed'),
    )

    def increment_access(self):
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        db.session.add(self)
        db.session.commit() 