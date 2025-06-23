# Data Sources TODO List

This document captures planned improvements for the health data clients to further enhance code consistency, reduce duplication, and improve maintainability.

## 1. Oura Client Improvements

- [ ] Refactor to fully leverage the base class authentication flow
- [ ] Move personal access token handling to a separate method
- [ ] Standardize method naming with other clients (e.g., `get_token` vs `exchange_code_for_token`)
- [ ] Improve error handling for API-specific error codes
- [ ] Create helper methods for common parameter patterns

## 2. Withings Client Improvements

- [ ] Standardize parameter naming with other clients (`start_date`/`end_date` vs `startdate`/`enddate`)
- [ ] Improve error handling for API-specific error codes
- [ ] Standardize method naming (`_get_auth_url` vs `get_auth_url`)
- [ ] Extract common OAuth URL generation code to reuse base class methods
- [ ] Consolidate duplicate code in data retrieval methods

## 3. Whoop Client Improvements

- [ ] Consolidate duplicate code in data retrieval methods
- [ ] Create helper methods for common parameter patterns
- [ ] Standardize date format handling (ISO vs timestamps)
- [ ] Improve error handling for API-specific error codes
- [ ] Extract common OAuth URL generation code to reuse base class methods

## 4. OneDrive Client Improvements

- [ ] Align method naming with other clients (`_get_token` vs `get_token`)
- [ ] Extract MSAL-specific code to separate helper methods
- [ ] Standardize error handling with other clients
- [ ] Improve documentation for MSAL-specific authentication flow
- [ ] Create helper methods for file operations

## 5. Base Class Improvements

- [ ] Add more extension points for client-specific behavior
- [ ] Create a configuration class for common settings
- [ ] Add utility methods for consistent date formatting
- [ ] Create a more robust base `OAuthCallbackHandler` with customization points
- [ ] Standardize error message formats across all clients

## General Improvements

- [ ] Create a standard `OAuthConfig` class to hold OAuth-specific parameters
- [ ] Standardize docstring format and required sections
- [ ] Standardize on snake_case for all variable names
- [ ] Create helper methods for common response transformations
- [ ] Standardize logging approach across all clients

## Future Improvements

- [ ] **Caching**: Implement response caching to reduce API calls
- [ ] **Offline Mode**: Add support for working with cached data when APIs are unavailable
- [ ] **Additional Data Sources**: Extend to support more health data providers
- [ ] **Advanced Analytics**: Enhance data analysis capabilities

### Others
- [ ] Why does oura need to import token manager