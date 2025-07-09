# Local HealthKit

Production-ready Python clients and services for health data APIs including Whoop, Oura, Withings, Hevy, and OneDrive.

## Features

- **🔐 OAuth2 Authentication**: 90-day sliding window with automatic token refresh
- **🔑 API Key Support**: Simple API key authentication for supported services
- **🔄 Automatic Retry Logic**: Exponential backoff with configurable retry attempts
- **📊 Multiple Health APIs**: Whoop, Oura, Withings, Hevy workout tracking
- **☁️ Cloud Storage**: OneDrive integration for data backup
- **🏗️ Clean Architecture**: Separate client and service layers
- **🧪 Production Tested**: Validated with real API calls and comprehensive test suite

## Supported APIs

| Service | Authentication | Data Types |
|---------|---------------|------------|
| **Whoop** | OAuth2 | Workouts, Recovery, Sleep, Cycles |
| **Oura** | API Key | Activity, Resilience, Workouts |
| **Withings** | OAuth2 | Weight, Body Composition |
| **Hevy** | API Key | Workouts, Exercises |
| **OneDrive** | OAuth2 | File Storage, Folder Management |

## Installation

```bash
pip install local-healthkit
```

### Development Installation

```bash
git clone https://github.com/yourusername/local-healthkit.git
cd local-healthkit
pip install -e ".[dev]"
```

## Quick Start

### Using Clients (Low-level API access)

```python
from local_healthkit.clients import WhoopClient, OuraClient

# Whoop OAuth2 client
whoop = WhoopClient()
if not whoop.is_authenticated():
    whoop.authenticate()

workouts = whoop.get_workouts_data(start_date, end_date)

# Oura API key client  
oura = OuraClient()
activity = oura.get_activity_data(start_date, end_date)
```

### Using Services (High-level business logic)

```python
from local_healthkit.services import WhoopService, OuraService
from datetime import datetime, timedelta

# Initialize services
whoop_service = WhoopService()
oura_service = OuraService()

# Fetch data with automatic date handling
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

# Get all Whoop data types
whoop_data = whoop_service.fetch_data(start_date, end_date)
print(f"Fetched {len(whoop_data)} Whoop records")

# Get Oura activity data
oura_data = oura_service.fetch_data(start_date, end_date)
print(f"Fetched {len(oura_data)} Oura records")
```

## Configuration

### Environment Variables

Create a `.env` file with your API credentials:

```bash
# Whoop OAuth2
WHOOP_CLIENT_ID=your_whoop_client_id
WHOOP_CLIENT_SECRET=your_whoop_client_secret

# Oura API Key
OURA_API_KEY=your_oura_api_key

# Withings OAuth2
WITHINGS_CLIENT_ID=your_withings_client_id
WITHINGS_CLIENT_SECRET=your_withings_client_secret

# Hevy API Key
HEVY_API_KEY=your_hevy_api_key

# OneDrive OAuth2
ONEDRIVE_CLIENT_ID=your_onedrive_client_id
ONEDRIVE_CLIENT_SECRET=your_onedrive_client_secret

# Optional: Customize token validity and retry settings
TOKEN_VALIDITY_DAYS=90
TOKEN_REFRESH_BUFFER_HOURS=24
API_MAX_RETRIES=3
API_TIMEOUT=30
```

### Programmatic Configuration

```python
from local_healthkit.clients.base.config import ClientConfig

# Customize client behavior
config = ClientConfig(
    validity_days=90,
    refresh_buffer_hours=24,
    max_retries=3,
    timeout=30
)
```

## Advanced Usage

### Custom Authentication Handling

```python
from local_healthkit.clients import WhoopClient

client = WhoopClient()

# Check authentication status
if not client.is_authenticated():
    print("Authentication required")
    client.authenticate()  # Opens browser for OAuth2 flow

# Force re-authentication
client.clear_tokens()
client.authenticate()
```

### Error Handling

```python
from local_healthkit.clients import OuraClient
from local_healthkit.exceptions import APIClientError

try:
    client = OuraClient()
    data = client.get_activity_data(start_date, end_date)
except APIClientError as e:
    print(f"API Error: {e}")
    # Handle authentication, rate limiting, etc.
```

### Batch Data Processing

```python
from local_healthkit.services import WhoopService, OuraService
from datetime import datetime, timedelta

# Process multiple months of data
services = [WhoopService(), OuraService()]
all_data = {}

for month in range(6):  # Last 6 months
    end_date = datetime.now() - timedelta(days=30 * month)
    start_date = end_date - timedelta(days=30)
    
    for service in services:
        service_name = service.__class__.__name__
        if service_name not in all_data:
            all_data[service_name] = []
            
        monthly_data = service.fetch_data(start_date, end_date)
        all_data[service_name].extend(monthly_data)

print(f"Total records: {sum(len(data) for data in all_data.values())}")
```

## Architecture

### Client Layer
- **Low-level API access**: Direct HTTP requests to health APIs
- **Authentication management**: OAuth2 flows and API key handling
- **Error handling**: Retry logic and exception management
- **Token persistence**: Automatic token storage and refresh

### Service Layer  
- **Business logic**: Data aggregation and processing
- **Date handling**: Automatic date range conversion
- **Multi-source support**: Unified interface across different APIs
- **Logging integration**: Comprehensive request and error logging

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=local_healthkit

# Run linting
black local_healthkit/
isort local_healthkit/
flake8 local_healthkit/
mypy local_healthkit/
```

### Building the Package

```bash
# Build distribution packages
python -m build

# Install locally
pip install -e .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0
- Initial release with Whoop, Oura, Withings, Hevy, and OneDrive support
- OAuth2 authentication with 90-day sliding window
- Comprehensive client and service layers
- Production-ready error handling and retry logic
