#!/usr/bin/env python3
"""
Quick script to check if the API is running and test basic connectivity.
"""

import requests
import subprocess
import os
import time

def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running and healthy!")
            return True
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API - it may not be running")
        return False
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False

def start_docker_services():
    """Start Docker services."""
    print("🚀 Starting Docker services...")
    try:
        # Change to backend directory
        os.chdir("/Users/niro/dev/playground/intergalactic-teacher/backend")
        
        # Run docker-compose command
        result = subprocess.run(
            ["docker-compose", "up", "--build", "-d", "api"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for build
        )
        
        if result.returncode == 0:
            print("✅ Docker services started successfully!")
            print("📋 Docker output:")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("❌ Failed to start Docker services")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker build/start timed out")
        return False
    except Exception as e:
        print(f"❌ Error starting Docker: {e}")
        return False

def wait_for_api_ready(max_wait_time=60):
    """Wait for API to be ready."""
    print(f"⏳ Waiting for API to be ready (max {max_wait_time} seconds)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if check_api_health():
            return True
        time.sleep(3)
    
    print(f"❌ API not ready after {max_wait_time} seconds")
    return False

if __name__ == "__main__":
    print("API Health Check and Docker Startup")
    print("=" * 50)
    
    # First check if API is already running
    if check_api_health():
        print("API is already running! Skipping Docker startup.")
    else:
        # Try to start Docker services
        if start_docker_services():
            # Wait for API to be ready
            if wait_for_api_ready():
                print("\n🎉 API is ready for testing!")
            else:
                print("\n💥 API failed to start properly")
        else:
            print("\n💥 Failed to start Docker services")