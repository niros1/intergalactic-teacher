// Simple integration test for frontend-backend connection
async function testIntegration() {
  console.log('🧪 Testing Frontend-Backend Integration...');
  
  try {
    // Test 1: Test API connectivity from frontend's perspective
    console.log('📡 Testing API connectivity...');
    
    const response = await fetch('http://localhost:8001/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:5173'
      },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'testpassword'
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('✅ Backend API accessible:', data);
    
    // Test 2: Test CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
      'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
      'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
    };
    console.log('✅ CORS Headers:', corsHeaders);
    
    // Test 3: Test health endpoint
    const healthResponse = await fetch('http://localhost:8001/health');
    const healthData = await healthResponse.json();
    console.log('✅ Health Check:', healthData);
    
    console.log('🎉 Integration Test Passed!');
    return { success: true, data, corsHeaders, healthData };
    
  } catch (error) {
    console.error('❌ Integration Test Failed:', error.message);
    return { success: false, error: error.message };
  }
}

// Run the test
testIntegration().then(result => {
  console.log('🔍 Final Result:', result);
  process.exit(result.success ? 0 : 1);
});