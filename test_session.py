import requests
from bs4 import BeautifulSoup

# Test login and session
session = requests.Session()

# Get login page
login_url = 'http://localhost:5000/login'
response = session.get(login_url)
print(f"GET {login_url} - Status: {response.status_code}")

# Extract CSRF token
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = None
csrf_input = soup.find('input', {'name': 'csrf_token'})
if csrf_input:
    csrf_token = csrf_input.get('value')
    print(f"CSRF token found: {csrf_token[:20]}...")
else:
    print("❌ No CSRF token found")
    exit(1)

# Login data
login_data = {
    'username': 'estudiante',
    'password': 'test',
    'csrf_token': csrf_token
}

# Attempt login
response = session.post(login_url, data=login_data, allow_redirects=False)
print(f"POST {login_url} - Status: {response.status_code}")

if response.status_code == 302:
    redirect_location = response.headers.get('Location')
    print(f"Redirected to: {redirect_location}")
    
    # Follow the redirect
    if redirect_location:
        if redirect_location.startswith('/'):
            redirect_url = f"http://localhost:5000{redirect_location}"
        else:
            redirect_url = redirect_location
            
        response = session.get(redirect_url, allow_redirects=False)
        print(f"GET {redirect_url} - Status: {response.status_code}")
        
        if response.status_code == 302:
            second_redirect = response.headers.get('Location')
            print(f"Second redirect to: {second_redirect}")
            
            # Check if redirected back to login
            if 'login' in second_redirect:
                print("❌ Redirected back to login - authentication failed")
                
                # Try to access the feed directly to see what happens
                feed_response = session.get('http://localhost:5000/feed/', allow_redirects=False)
                print(f"Direct feed access - Status: {feed_response.status_code}")
                if feed_response.status_code == 302:
                    print(f"Feed redirects to: {feed_response.headers.get('Location')}")
            else:
                print("✅ Login successful - redirected to feed")
        else:
            print(f"✅ Login successful - reached feed with status {response.status_code}")
else:
    print(f"❌ Login failed with status {response.status_code}")
    print(response.text[:500])