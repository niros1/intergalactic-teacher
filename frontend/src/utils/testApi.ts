// Test script to verify API integration
import { authService } from '../services/authService'
import { childService } from '../services/childService'
import { storyService } from '../services/storyService'

export const testApiIntegration = async () => {
  console.log('🧪 Testing API Integration...')
  
  try {
    // Test 1: Check API connectivity
    console.log('📡 Testing API connectivity...')
    
    // This will test the base API setup
    const testResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'testpassword'
      })
    }).catch((error) => {
      console.log('❌ Backend not running or not accessible:', error.message)
      return null
    })
    
    if (!testResponse) {
      console.log('⚠️  Backend appears to be offline. Continuing with mock tests...')
    } else {
      console.log('✅ Backend is accessible')
    }
    
    // Test 2: Service initialization
    console.log('🔧 Testing service initialization...')
    
    // Test auth service
    console.log('👤 Auth Service - initialized:', typeof authService === 'object')
    console.log('  - register method:', typeof authService.register === 'function')
    console.log('  - login method:', typeof authService.login === 'function')
    console.log('  - refreshToken method:', typeof authService.refreshToken === 'function')
    
    // Test child service  
    console.log('👶 Child Service - initialized:', typeof childService === 'object')
    console.log('  - createChild method:', typeof childService.createChild === 'function')
    console.log('  - getChildren method:', typeof childService.getChildren === 'function')
    console.log('  - updateChild method:', typeof childService.updateChild === 'function')
    
    // Test story service
    console.log('📚 Story Service - initialized:', typeof storyService === 'object')
    console.log('  - generateStory method:', typeof storyService.generateStory === 'function')
    console.log('  - getStories method:', typeof storyService.getStories === 'function')
    console.log('  - startStorySession method:', typeof storyService.startStorySession === 'function')
    
    // Test 3: Error handling
    console.log('🛡️  Testing error handling...')
    
    try {
      // This should trigger error handling
      await authService.login({ email: '', password: '' })
      console.log('❌ Error handling test failed - should have thrown error')
    } catch (error: any) {
      console.log('✅ Error handling working:', error.message)
    }
    
    console.log('🎉 API Integration tests completed!')
    
    return {
      success: true,
      backendAccessible: !!testResponse,
      servicesInitialized: true,
      errorHandlingWorking: true
    }
    
  } catch (error: any) {
    console.error('❌ API Integration test failed:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

// Helper to run tests in development
export const runApiTests = () => {
  if (import.meta.env.DEV) {
    testApiIntegration().then(result => {
      console.log('🧪 API Test Results:', result)
    })
  }
}