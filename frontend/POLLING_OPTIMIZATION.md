# Polling Optimization - Fix for Excessive API Requests

## Problem

The frontend was making excessive API requests because:
1. **Multiple polling instances** running simultaneously (from Home page AND JobDetail page)
2. **No request deduplication** - same requests fired multiple times
3. **Too frequent polling** - 2 second intervals causing server overload
4. **No request cancellation** - old requests not cancelled when new ones start

## Solution Implemented

### 1. Request Deduplication
- Added unique keys to polling instances
- Prevents duplicate polling for the same resource
- Automatically stops old poller when new one starts

### 2. Increased Polling Intervals
- **Default interval:** 2s → 3s
- **Maximum interval:** 5s → 10s
- **Minimum interval:** Enforced 3s minimum

### 3. Request Cancellation
- Added AbortController support in axios client
- Cancels previous request when new one starts for same endpoint
- Prevents duplicate in-flight requests

### 4. Single Polling Source
- Removed polling from `useJobManagement` (only used on submit)
- JobDetail page handles all polling when viewing a job
- Prevents double-polling when navigating from Home to JobDetail

### 5. Better Error Handling
- Polling continues on error with exponential backoff
- Proper cleanup on component unmount
- Stops polling when job completes

## Changes Made

### `utils/polling.ts`
- Added `key` parameter to prevent duplicate polling
- Tracks active pollers globally
- Stops old poller when new one with same key starts

### `services/api/client.ts`
- Added AbortController support
- Tracks pending requests
- Cancels duplicate requests automatically

### `composables/useJobManagement.ts`
- Removed polling from submit (let JobDetail handle it)
- Simplified to just submit job

### `composables/useLogStreaming.ts`
- Added polling key based on jobId
- Increased minimum interval to 3s
- Disabled immediate polling

### `views/JobDetail.vue`
- Added polling key to prevent duplicates
- Increased interval to 3s minimum
- Proper cleanup on unmount

### `stores/session.ts`
- Changed default refresh interval from 2000ms to 3000ms

## Expected Results

**Before:**
- 8+ requests per 2 seconds (4 polling instances × 2 endpoints)
- Server overload
- Duplicate requests

**After:**
- 2 requests per 3 seconds (1 status poll + 1 log poll)
- ~67% reduction in request frequency
- No duplicate requests
- Automatic cancellation of old requests

## Testing

1. Submit a job from Home page
2. Navigate to JobDetail page
3. Check browser Network tab
4. Should see:
   - Requests every 3 seconds (not 2)
   - Only 2 requests per cycle (status + logs)
   - No duplicate requests
   - Old requests cancelled when new ones start

## Further Optimization (Optional)

If still too many requests, you can:
1. Increase default interval to 5 seconds
2. Add request debouncing
3. Implement Server-Sent Events (SSE) instead of polling
4. Add request batching

