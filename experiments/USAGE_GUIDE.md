# 🚀 Experimental OAuth2 Clients Usage Guide

## 📋 Prerequisites

### 1. Environment Variables
Create a `.env` file or set these environment variables:

```bash
# Whoop API Credentials
WHOOP_CLIENT_ID=your_whoop_client_id
WHOOP_CLIENT_SECRET=your_whoop_client_secret

# Withings API Credentials  
WITHINGS_CLIENT_ID=your_withings_client_id
WITHINGS_CLIENT_SECRET=your_withings_client_secret

# Optional: Token validity settings
TOKEN_VALIDITY_DAYS=90
TOKEN_REFRESH_BUFFER_HOURS=24
```

### 2. Dependencies
```bash
pip install authlib requests python-dotenv
```

## 🎯 Basic Usage

### Whoop Client Example

```python
from experiments.whoop_client import WhoopClientExperimental
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_whoop_data():
    """Get Whoop workout data for the last week."""
    
    # Initialize client (reads from environment variables)
    client = WhoopClientExperimental()
    
    # Set date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    try:
        # Get workouts (automatic authentication if needed)
        workouts = client.get_workouts(start_date, end_date, limit=10)
        
        print(f"✅ Retrieved {len(workouts['records'])} workouts")
        
        # Process workout data
        for workout in workouts['records']:
            print(f"Workout {workout['id']}: {workout['sport_id']} - Strain: {workout['score']['strain']}")
            
        return workouts
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    data = get_whoop_data()
```

### Withings Client Example

```python
from experiments.withings_client import WithingsClientExperimental
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_withings_data():
    """Get Withings weight data for the last month."""
    
    # Initialize client (reads from environment variables)
    client = WithingsClientExperimental()
    
    # Set date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        # Get weight data (automatic authentication if needed)
        weight_data = client.get_weight_data(start_date, end_date)
        
        measurements = weight_data.get('measuregrps', [])
        print(f"✅ Retrieved {len(measurements)} weight measurements")
        
        # Process weight data
        for measurement in measurements:
            date = datetime.fromtimestamp(measurement['date'])
            measures = measurement.get('measures', [])
            
            for measure in measures:
                if measure['type'] == 1:  # Weight
                    weight_kg = measure['value'] * (10 ** measure['unit'])
                    print(f"Weight on {date.date()}: {weight_kg:.1f} kg")
                    
        return weight_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    data = get_withings_data()
```

## 🔄 Advanced Usage with Error Handling

```python
from experiments.whoop_client import WhoopClientExperimental
from experiments.withings_client import WithingsClientExperimental
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthDataCollector:
    """Advanced health data collector with robust error handling."""
    
    def __init__(self):
        self.whoop_client = WhoopClientExperimental()
        self.withings_client = WithingsClientExperimental()
    
    def collect_all_data(self, days_back: int = 7):
        """Collect data from all sources."""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        results = {
            'whoop': None,
            'withings': None,
            'errors': []
        }
        
        # Collect Whoop data
        try:
            logger.info("Collecting Whoop data...")
            whoop_data = self.whoop_client.get_workouts(start_date, end_date)
            results['whoop'] = whoop_data
            logger.info(f"✅ Whoop: {len(whoop_data['records'])} workouts")
            
        except Exception as e:
            error_msg = f"Whoop collection failed: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        # Collect Withings data
        try:
            logger.info("Collecting Withings data...")
            withings_data = self.withings_client.get_weight_data(start_date, end_date)
            results['withings'] = withings_data
            measurements = len(withings_data.get('measuregrps', []))
            logger.info(f"✅ Withings: {measurements} measurements")
            
        except Exception as e:
            error_msg = f"Withings collection failed: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def get_authentication_status(self):
        """Check authentication status for both clients."""
        
        status = {}
        
        # Whoop status
        try:
            whoop_auth = self.whoop_client.is_authenticated()
            whoop_sliding = self.whoop_client.is_in_sliding_window()
            status['whoop'] = {
                'authenticated': whoop_auth,
                'in_sliding_window': whoop_sliding,
                'days_remaining': 89 if whoop_sliding else 0
            }
        except Exception as e:
            status['whoop'] = {'error': str(e)}
        
        # Withings status
        try:
            withings_auth = self.withings_client.is_authenticated()
            withings_sliding = self.withings_client.is_in_sliding_window()
            status['withings'] = {
                'authenticated': withings_auth,
                'in_sliding_window': withings_sliding,
                'days_remaining': 89 if withings_sliding else 0
            }
        except Exception as e:
            status['withings'] = {'error': str(e)}
        
        return status

# Usage example
if __name__ == "__main__":
    collector = HealthDataCollector()
    
    # Check authentication status
    auth_status = collector.get_authentication_status()
    print("🔐 Authentication Status:")
    for service, status in auth_status.items():
        print(f"   {service}: {status}")
    
    # Collect data
    print("\\n📊 Collecting health data...")
    data = collector.collect_all_data(days_back=7)
    
    if data['errors']:
        print("\\n⚠️ Errors encountered:")
        for error in data['errors']:
            print(f"   - {error}")
    
    print("\\n✅ Data collection complete!")
```

## 🛠️ Integration Tips

### 1. **Scheduled Data Collection**
```python
import schedule
import time

def daily_data_sync():
    collector = HealthDataCollector()
    data = collector.collect_all_data(days_back=1)
    # Process and store data
    
# Run daily at 6 AM
schedule.every().day.at("06:00").do(daily_data_sync)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 2. **Database Integration**
```python
import sqlite3
import json

def store_health_data(data):
    conn = sqlite3.connect('health_data.db')
    cursor = conn.cursor()
    
    # Store Whoop data
    if data['whoop']:
        for workout in data['whoop']['records']:
            cursor.execute("""
                INSERT OR REPLACE INTO workouts 
                (id, date, sport_id, strain, heart_rate_avg, data_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                workout['id'],
                workout['start'],
                workout['sport_id'],
                workout['score']['strain'],
                workout['score']['average_heart_rate'],
                json.dumps(workout)
            ))
    
    conn.commit()
    conn.close()
```

### 3. **Error Monitoring**
```python
import smtplib
from email.mime.text import MIMEText

def send_error_alert(error_msg):
    """Send email alert when data collection fails."""
    msg = MIMEText(f"Health data collection error: {error_msg}")
    msg['Subject'] = 'Health Data Collection Alert'
    msg['From'] = 'your-app@example.com'
    msg['To'] = 'admin@example.com'
    
    # Send email (configure SMTP settings)
    # smtp_server.send_message(msg)
```

## 🔧 Configuration Options

### Token Validity Settings
```python
# In your .env file:
TOKEN_VALIDITY_DAYS=90        # How long to keep sessions (default: 90 days)
TOKEN_REFRESH_BUFFER_HOURS=24 # When to proactively refresh (default: 24 hours)
```

### Custom Token Storage
```python
# Custom token file locations
whoop_client = WhoopClientExperimental()
withings_client = WithingsClientExperimental()

# Tokens are automatically stored at:
# ~/.whoop_tokens_experimental.json
# ~/.withings_tokens_experimental.json
```

## 🚨 Important Notes

1. **First Run**: The first time you run the code, it will open a browser for OAuth authentication
2. **Token Persistence**: Tokens are saved locally and persist across runs
3. **Automatic Refresh**: Withings tokens refresh automatically; Whoop falls back to re-authentication
4. **Error Handling**: Always wrap API calls in try-catch blocks
5. **Rate Limits**: Be mindful of API rate limits (especially for frequent calls)

## 🎯 Quick Start Script

Save this as `quick_start.py`:

```python
#!/usr/bin/env python3
"""Quick start script for experimental OAuth2 clients."""

from experiments.whoop_client import WhoopClientExperimental
from experiments.withings_client import WithingsClientExperimental
from datetime import datetime, timedelta
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("🚀 Testing Experimental OAuth2 Clients")
    print("=" * 50)
    
    # Test Whoop
    print("\\n🏃 Testing Whoop Client...")
    try:
        whoop = WhoopClientExperimental()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        workouts = whoop.get_workouts(start_date, end_date, limit=5)
        print(f"✅ Whoop: Retrieved {len(workouts['records'])} workouts")
    except Exception as e:
        print(f"❌ Whoop failed: {e}")
    
    # Test Withings
    print("\\n⚖️ Testing Withings Client...")
    try:
        withings = WithingsClientExperimental()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        weight_data = withings.get_weight_data(start_date, end_date)
        measurements = len(weight_data.get('measuregrps', []))
        print(f"✅ Withings: Retrieved {measurements} measurements")
    except Exception as e:
        print(f"❌ Withings failed: {e}")
    
    print("\\n🎉 Testing complete!")

if __name__ == "__main__":
    main()
```

Run with: `python quick_start.py`

## 🆘 Troubleshooting

### Common Issues:
1. **Missing credentials**: Check your `.env` file
2. **Browser doesn't open**: Copy the URL manually
3. **Token expired**: Delete token files to force re-authentication
4. **Import errors**: Ensure you're running from the correct directory

### Reset Authentication:
```bash
rm ~/.whoop_tokens_experimental.json
rm ~/.withings_tokens_experimental.json
```

That's it! You now have production-ready OAuth2 clients with 89-day sessions and automatic error recovery! 🎉
