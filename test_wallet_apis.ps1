# Test all Wallet Page APIs
Write-Host "=== Testing FairTrip Wallet APIs ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$testUserId = "test_user_123"  # Replace with actual user ID

# Test 1: Root endpoint
Write-Host "1. Testing Root Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get
    Write-Host "   ✓ Root endpoint working" -ForegroundColor Green
    Write-Host "   Version: $($response.version)" -ForegroundColor Gray
}
catch {
    Write-Host "   ✗ Root endpoint failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: User Summary
Write-Host "2. Testing User Summary Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/expenses/user/$testUserId/summary" -Method Get
    Write-Host "   ✓ User summary endpoint exists" -ForegroundColor Green
}
catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   ⚠ User not found (expected for test user)" -ForegroundColor Yellow
    }
    else {
        Write-Host "   ✗ User summary failed: $_" -ForegroundColor Red
    }
}
Write-Host ""

# Test 3: Get Expenses
Write-Host "3. Testing Get Expenses Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/expenses/" -Method Get
    Write-Host "   ✓ Get expenses endpoint working" -ForegroundColor Green
    Write-Host "   Found $($response.Count) expenses" -ForegroundColor Gray
}
catch {
    Write-Host "   ✗ Get expenses failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Get Settlements
Write-Host "4. Testing Settlements Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/settlements/?user_id=$testUserId" -Method Get
    Write-Host "   ✓ Settlements endpoint working" -ForegroundColor Green
    Write-Host "   Found $($response.Count) settlements" -ForegroundColor Gray
}
catch {
    Write-Host "   ✗ Settlements endpoint failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Get Recurring Expenses
Write-Host "5. Testing Recurring Expenses Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/recurring-expenses/" -Method Get
    Write-Host "   ✓ Recurring expenses endpoint working" -ForegroundColor Green
    Write-Host "   Found $($response.Count) recurring expenses" -ForegroundColor Gray
}
catch {
    Write-Host "   ✗ Recurring expenses endpoint failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 6: Currency Rates
Write-Host "6. Testing Currency Rates Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/currency/rates" -Method Get
    Write-Host "   ✓ Currency rates endpoint working" -ForegroundColor Green
    Write-Host "   Found $($response.Count) currency rates" -ForegroundColor Gray
}
catch {
    Write-Host "   ✗ Currency rates endpoint failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 7: Currency Conversion
Write-Host "7. Testing Currency Conversion Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/currency/convert?amount=100&from_currency=USD&to_currency=EUR" -Method Get
    Write-Host "   ✓ Currency conversion endpoint working" -ForegroundColor Green
    Write-Host "   100 USD = $($response.converted_amount) EUR" -ForegroundColor Gray
}
catch {
    Write-Host "   ✗ Currency conversion failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 8: Notifications
Write-Host "8. Testing Notifications Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/notifications/?user_id=$testUserId" -Method Get
    Write-Host "   ✓ Notifications endpoint working" -ForegroundColor Green
    Write-Host "   Found $($response.Count) notifications" -ForegroundColor Gray
}
catch {
    Write-Host "   ✗ Notifications endpoint failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 9: Check API Documentation
Write-Host "9. Testing API Documentation..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/docs" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✓ API docs available at $baseUrl/docs" -ForegroundColor Green
    }
}
catch {
    Write-Host "   ✗ API docs not accessible" -ForegroundColor Red
}
Write-Host ""

Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "All wallet page endpoints have been tested." -ForegroundColor White
Write-Host "Check the results above for any failures." -ForegroundColor White
Write-Host ""
Write-Host "To view interactive API docs, visit: http://localhost:8000/docs" -ForegroundColor Green

