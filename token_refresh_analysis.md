# Token Refresh Analysis & Fixes

## 🔍 **Issues Identified**

### 1. **Token Expiration Logic Inconsistency**
**Problem**: The TokenManager has conflicting expiration checks:
- `get_tokens()` uses 1-minute buffer: `datetime.now() + timedelta(minutes=1) >= self.token_expiry`
- `is_token_expired()` uses 1-hour buffer: `current_time + buffer >= self.token_expiry`

**Impact**: Tokens may be considered valid by `get_tokens()` but expired by `is_token_expired()`

### 2. **Automatic Refresh Not Triggered**
**Problem**: The `_get_access_token()` method only checks if `self.access_token` exists, not if it's expired:
```python
# Current logic - WRONG
if self.access_token:
    return self.access_token  # Returns even if expired!
```

**Should be**:
```python
# Check if token exists AND is not expired
if self.access_token and not self.token_manager.is_token_expired():
    return self.access_token
```

### 3. **OneDrive JWT Malformation**
**Problem**: OneDrive token shows as "JWT is not well formed, there are no dots (.)"
**Cause**: Token corruption or incorrect token format being stored

### 4. **Whoop Token Shows Expired But Works**
**Problem**: Test shows "Whoop: Token found, status: EXPIRED" but API calls succeed
**Cause**: The refresh is happening automatically but the status check is using wrong logic

## 🔧 **Fixes Required**

### Fix 1: Standardize Token Expiration Logic
```python
# In TokenManager.get_tokens()
def get_tokens(self) -> Optional[dict[str, Any]]:
    if not self.tokens:
        return None
    
    # Use consistent expiration check
    if self.is_token_expired():
        self.logger.debug(f"[TokenManager] Tokens expired for {self.token_file}")
        return None
    
    return self.tokens
```

### Fix 2: Fix Automatic Token Refresh
```python
# In APIClient._get_access_token()
def _get_access_token(self) -> str:
    # Check if current token is valid
    if self.access_token and not self.token_manager.is_token_expired():
        return self.access_token
    
    # Token is expired or missing, try to refresh
    if self.refresh_token and self.refresh_access_token():
        return self.access_token
    
    # If refresh failed, try full authentication
    if self.authenticate():
        if self.access_token:
            return self.access_token
    
    raise APIClientError("Failed to obtain a valid access token")
```

### Fix 3: OneDrive Token Cleanup
```python
# Clear corrupted OneDrive tokens and re-authenticate
def fix_onedrive_tokens():
    token_manager = TokenManager("~/.onedrive_tokens.json")
    token_manager.clear_tokens()
    # Force re-authentication on next use
```

### Fix 4: Proactive Token Refresh
```python
# Add to base APIClient
def ensure_valid_token(self) -> None:
    """Ensure we have a valid token, refreshing if necessary."""
    if self.token_manager.is_token_expired():
        self.logger.info("Token expired, attempting refresh...")
        if not self.refresh_access_token():
            self.logger.warning("Token refresh failed, may need re-authentication")
```

## 🎯 **90-Day Rolling Refresh Implementation**

The current implementation has the right idea but needs fixes:

### Current Logic (Correct Concept):
1. **Initial Auth**: Set `created_at` and `last_refresh_time`
2. **Token Refresh**: Update `last_refresh_time`, keep `created_at`
3. **Expiration Check**: If `last_refresh_time` > 90 days ago, expire token

### Issues to Fix:
1. **Inconsistent buffer times** (1 min vs 1 hour)
2. **Automatic refresh not triggered** before API calls
3. **Token status reporting** doesn't match actual behavior

## 🚀 **Recommended Implementation Plan**

### Phase 1: Fix Core Logic
1. Standardize expiration buffer to 1 hour across all methods
2. Fix `_get_access_token()` to check expiration before returning token
3. Add proactive refresh before API calls

### Phase 2: Clean Up Corrupted Tokens
1. Clear OneDrive tokens and force re-auth
2. Validate all existing tokens for proper format

### Phase 3: Enhanced Monitoring
1. Add token health checks to test script
2. Log token refresh events with timestamps
3. Add metrics for token refresh success/failure rates

## 📊 **Current Token Status**
- **Whoop**: Expired but auto-refreshing (working)
- **Oura**: Valid (working)
- **Withings**: Valid (working)
- **Hevy**: API key (no expiration)
- **OneDrive**: Corrupted JWT (needs cleanup)

## ✅ **Success Criteria**
1. No authentication prompts for 90 days after initial setup
2. Automatic token refresh before expiration
3. Consistent token status reporting
4. All services working without manual intervention
