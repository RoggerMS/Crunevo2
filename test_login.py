#!/usr/bin/env python3
import requests
import sys

# Test login for user 'estudiante'
url = 'http://localhost:5000/login'
data = {
    'username': 'estudiante',
    'password': 'test'  # Correct password provided by user
}

print("Testing login for user 'estudiante'...")
print(f"URL: {url}")
print(f"Data: {data}")
print("-" * 50)

try:
    # First get the login page to get CSRF token
    session = requests.Session()
    response = session.get(url)
    print(f"GET {url} - Status: {response.status_code}")
    
    if response.status_code == 200:
        # Try to extract CSRF token from the form
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        
        if csrf_token:
            data['csrf_token'] = csrf_token.get('value')
            print(f"CSRF token found: {data['csrf_token'][:20]}...")
        else:
            print("No CSRF token found in form")
    
    # Now try to login
    response = session.post(url, data=data)
    print(f"POST {url} - Status: {response.status_code}")
    
    if response.status_code == 500:
        print("\n🚨 ERROR 500 DETECTED!")
        print("Response content:")
        print(response.text[:1000])  # First 1000 chars
    elif response.status_code == 200:
        if 'login' in response.url.lower():
            print("\n❌ Login failed - redirected back to login page")
        else:
            print("\n✅ Login successful")
    elif response.status_code == 302:
        print(f"\n↗️ Redirected to: {response.headers.get('Location', 'Unknown')}")
    else:
        print(f"\n⚠️ Unexpected status code: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server. Make sure Flask is running on localhost:5000")
except Exception as e:
    print(f"❌ Error: {e}")