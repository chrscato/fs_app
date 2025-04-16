from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, RateQuery, CachedRate
import boto3
import pandas as pd
import io
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# AWS S3 Configuration
s3_client = boto3.client(
    's3',
    region_name=app.config['AWS_REGION'],
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
)

def update_cache_from_s3(state, procedure_code):
    """Update cache from S3 if data is older than 24 hours"""
    try:
        s3_key = f'rates/{state}/{procedure_code}.parquet'
        response = s3_client.get_object(
            Bucket=app.config['S3_BUCKET'],
            Key=s3_key
        )
        parquet_data = response['Body'].read()
        df = pd.read_parquet(io.BytesIO(parquet_data))
        
        # Delete old cache entries
        CachedRate.query.filter_by(
            state=state,
            procedure_code=procedure_code
        ).delete()
        
        # Add new entries
        for _, row in df.iterrows():
            cached_rate = CachedRate(
                state=state,
                procedure_code=procedure_code,
                provider=row.get('provider'),
                rate=row.get('rate'),
                effective_date=row.get('date')
            )
            db.session.add(cached_rate)
        
        db.session.commit()
        return True
    except Exception as e:
        app.logger.error(f"Error updating cache from S3: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/rates/<state>/<procedure_code>')
def get_rates(state, procedure_code):
    try:
        # Check if we need to update cache
        last_update = CachedRate.query.filter_by(
            state=state,
            procedure_code=procedure_code
        ).order_by(CachedRate.last_updated.desc()).first()
        
        if not last_update or (datetime.utcnow() - last_update.last_updated) > timedelta(hours=24):
            update_cache_from_s3(state, procedure_code)
        
        # Get rates from cache
        cached_rates = CachedRate.query.filter_by(
            state=state,
            procedure_code=procedure_code
        ).all()
        
        # Increment access count for each rate
        for rate in cached_rates:
            rate.increment_access()
        
        # Log the query
        query = RateQuery(
            state=state,
            procedure_code=procedure_code,
            result_count=len(cached_rates),
            cache_hit=True
        )
        db.session.add(query)
        db.session.commit()
        
        return jsonify([{
            'provider': rate.provider,
            'rate': float(rate.rate),
            'date': rate.effective_date.isoformat()
        } for rate in cached_rates])
            
    except Exception as e:
        app.logger.error(f"Error in get_rates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    try:
        # Get most frequently accessed rates
        popular_rates = db.session.query(
            CachedRate.state,
            CachedRate.procedure_code,
            db.func.sum(CachedRate.access_count).label('total_accesses')
        ).group_by(
            CachedRate.state,
            CachedRate.procedure_code
        ).order_by(
            db.func.sum(CachedRate.access_count).desc()
        ).limit(10).all()
        
        # Get cache hit rate
        total_queries = RateQuery.query.count()
        cache_hits = RateQuery.query.filter_by(cache_hit=True).count()
        hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0
        
        return jsonify({
            'popular_rates': [{
                'state': rate.state,
                'procedure_code': rate.procedure_code,
                'accesses': rate.total_accesses
            } for rate in popular_rates],
            'cache_stats': {
                'total_queries': total_queries,
                'cache_hits': cache_hits,
                'hit_rate': round(hit_rate, 2)
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 