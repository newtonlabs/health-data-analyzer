# Health Data Analyzer Architecture

This document describes the architecture of the Health Data Analyzer application, focusing on the data source clients and authentication flow.

## Overview

The Health Data Analyzer is designed to aggregate health data from multiple sources (Whoop, Oura, Withings) and optionally store results in OneDrive. The application follows a modular architecture with a focus on code reuse, consistent error handling, and efficient token management.

## Key Components

### 1. Base Classes

#### `APIClient` (base.py)

The foundation of all API clients, providing:

- **Centralized Authentication Logic**: Common methods for token management and authentication
- **Standardized Error Handling**: Unified error reporting through `APIClientError`
- **Configurable Token Management**: Extended token validity periods to reduce reauthentication frequency
- **Retry Logic**: Automatic retry with exponential backoff for failed API requests

Key methods:
- `handle_authentication()`: Manages token refresh and authentication flow
- `_get_access_token()`: Gets a valid access token for API requests
- `exchange_code_for_token()`: Handles OAuth2 code exchange
- `_make_request()`: Makes API requests with automatic token refresh and retry

#### `OAuthCallbackHandler` (base.py)

Base handler for OAuth callbacks that:
- Suppresses HTTP server logs
- Provides a foundation for client-specific callback handlers

#### `DataSource` (base.py)

Abstract base class for all data sources that:
- Manages data storage directories
- Provides utility methods for file paths

### 2. Token Management

#### `TokenManager` (token_manager.py)

Handles token storage and validation:

- **Persistent Storage**: Saves tokens to disk for reuse across sessions
- **Configurable Validity**: Tokens are considered valid for a configurable period (default: 30 days)
- **Refresh Buffer**: Configurable buffer time before expiration to trigger refresh (default: 24 hours)
- **Environment Variable Configuration**: Supports customization through environment variables

### 3. API Clients

All clients inherit from `APIClient` and implement service-specific authentication and data retrieval:

#### `WhoopClient` (whoop_client.py)

- Handles OAuth2 authentication with Whoop
- Fetches recovery, workout, and sleep data

#### `OuraClient` (oura_client.py)

- Supports both personal access tokens and OAuth2 authentication
- Fetches activity, readiness, and sleep data

#### `WithingsClient` (withings_client.py)

- Handles OAuth2 authentication with Withings
- Fetches weight and other health metrics

#### `OneDriveClient` (onedrive_client.py)

- Uses MSAL device flow authentication
- Handles file uploads and folder management

## Authentication Flow

1. **Token Acquisition**:
   - First attempt to use existing tokens
   - If expired or missing, try to refresh tokens
   - If refresh fails, initiate full authentication

2. **OAuth2 Flow**:
   - Generate authorization URL for user to visit
   - Start local HTTP server to receive callback
   - Exchange authorization code for access token
   - Store tokens for future use

3. **Token Refresh**:
   - Automatically refresh tokens before they expire
   - Use refresh tokens to obtain new access tokens without user intervention
   - Fall back to full authentication if refresh fails

## Error Handling

- **Centralized Error Class**: All errors are instances of `APIClientError`
- **Consistent Reporting**: Standardized error messages across all clients
- **Graceful Degradation**: Proper handling of authentication failures and API errors

## Configuration

- **Environment Variables**: Support for configuring client credentials and token parameters
- **Token Validity**: Configurable through `TOKEN_VALIDITY_DAYS` environment variable
- **Refresh Buffer**: Configurable through `TOKEN_REFRESH_BUFFER_HOURS` environment variable

## Design Principles

1. **DRY (Don't Repeat Yourself)**: Common functionality is centralized in base classes
2. **Consistent Interfaces**: All clients follow the same patterns for authentication and API requests
3. **Separation of Concerns**: Each class has a single responsibility
4. **Configurability**: Key parameters can be customized through environment variables
5. **Robustness**: Retry logic and error handling make the application more resilient

## Data Flow

1. User initiates data fetch through command line
2. Application authenticates with each service as needed
3. Data is retrieved from each service's API
4. Data is transformed and normalized
5. Results are saved locally and optionally uploaded to OneDrive

## Next Steps

See the _TODO.md file in this directory for a detailed list of planned improvements and future enhancements.
