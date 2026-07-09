"""
Focused Backend Login Tests for Stanvard School ERP
Tests the specific login bug fixes from iteration 4
"""
import requests
import sys

BASE_URL = "https://school-portal-hub-16.preview.emergentagent.com/api"

# Test credentials
CREDENTIALS = {
    'superadmin': {'email': 'superadmin@stanvard.school', 'password': 'super123'},
    'admin_gn': {'email': 'admin.gn@stanvard.school', 'password': 'admin123'},
    'accountant_gn': {'email': 'accountant.gn@stanvard.school', 'password': 'acc123'},
    'teacher_gn': {'email': 'teacher.gn@stanvard.school', 'password': 'teacher123'},
    'parent_gn': {'email': 'parent.gn20250001@stanvard.school', 'password': 'parent123'},
}

class LoginTestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []

    def test(self, name, func):
        """Run a single test"""
        self.tests_run += 1
        print(f"\n{'='*70}")
        print(f"TEST {self.tests_run}: {name}")
        print('='*70)
        try:
            func()
            self.tests_passed += 1
            print(f"✅ PASSED")
            return True
        except AssertionError as e:
            self.tests_failed += 1
            self.failed_tests.append({'test': name, 'error': str(e)})
            print(f"❌ FAILED: {e}")
            return False
        except Exception as e:
            self.tests_failed += 1
            self.failed_tests.append({'test': name, 'error': str(e)})
            print(f"❌ ERROR: {e}")
            return False

    def run_all_tests(self):
        """Run all login-focused backend tests"""
        print("\n" + "="*70)
        print("STANVARD SCHOOL ERP - LOGIN BACKEND TESTS")
        print("="*70)

        # Test 1: Login with each role succeeds
        self.test("LOGIN: Super admin login succeeds", lambda: self.test_login_role('superadmin', 'super_admin'))
        self.test("LOGIN: School admin login succeeds", lambda: self.test_login_role('admin_gn', 'school_admin'))
        self.test("LOGIN: Accountant login succeeds", lambda: self.test_login_role('accountant_gn', 'accountant'))
        self.test("LOGIN: Teacher login succeeds", lambda: self.test_login_role('teacher_gn', 'teacher'))
        self.test("LOGIN: Parent login succeeds", lambda: self.test_login_role('parent_gn', 'parent'))

        # Test 2: Wrong credentials return 401
        self.test("LOGIN: Wrong password returns 401", lambda: self.test_wrong_password())
        self.test("LOGIN: Wrong email returns 401", lambda: self.test_wrong_email())

        # Test 3: Case-insensitive and trim-safe login
        self.test("LOGIN: Case-insensitive email works", lambda: self.test_case_insensitive())
        self.test("LOGIN: Email with trailing spaces works", lambda: self.test_email_with_spaces())

        # Test 4: Response structure
        self.test("LOGIN: Response contains access_token and user", lambda: self.test_response_structure())

        # Test 5: /auth/me endpoint
        self.test("AUTH: /auth/me returns correct user", lambda: self.test_auth_me())

        # Test 6: Invalid token returns 401
        self.test("AUTH: Invalid token returns 401", lambda: self.test_invalid_token())

        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n" + "="*70)
            print("FAILED TESTS DETAILS")
            print("="*70)
            for ft in self.failed_tests:
                print(f"\n❌ {ft['test']}")
                print(f"   Error: {ft['error']}")

        return 0 if self.tests_failed == 0 else 1

    # Test implementations
    def test_login_role(self, role_key, expected_role):
        """Test login for a specific role"""
        creds = CREDENTIALS[role_key]
        print(f"  → Logging in as {role_key} ({creds['email']})")
        r = requests.post(f"{BASE_URL}/auth/login", json=creds)
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        data = r.json()
        assert 'access_token' in data, "No access_token in response"
        assert 'user' in data, "No user in response"
        assert data['user']['role'] == expected_role, f"Expected role {expected_role}, got {data['user']['role']}"
        print(f"  ✓ Logged in as {data['user']['full_name']} (role: {data['user']['role']})")

    def test_wrong_password(self):
        """Test that wrong password returns 401"""
        creds = {'email': 'admin.gn@stanvard.school', 'password': 'wrongpassword'}
        print(f"  → Attempting login with wrong password")
        r = requests.post(f"{BASE_URL}/auth/login", json=creds)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        data = r.json()
        assert 'detail' in data, "Should have detail field"
        assert 'Invalid email or password' in data['detail'], f"Expected 'Invalid email or password', got {data['detail']}"
        print(f"  ✓ Wrong password correctly returns 401 with message: {data['detail']}")

    def test_wrong_email(self):
        """Test that wrong email returns 401"""
        creds = {'email': 'nonexistent@stanvard.school', 'password': 'admin123'}
        print(f"  → Attempting login with wrong email")
        r = requests.post(f"{BASE_URL}/auth/login", json=creds)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        data = r.json()
        assert 'detail' in data, "Should have detail field"
        print(f"  ✓ Wrong email correctly returns 401 with message: {data['detail']}")

    def test_case_insensitive(self):
        """Test that email is case-insensitive"""
        creds = {'email': 'Admin.GN@stanvard.school', 'password': 'admin123'}
        print(f"  → Attempting login with mixed case email: {creds['email']}")
        r = requests.post(f"{BASE_URL}/auth/login", json=creds)
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        data = r.json()
        assert 'access_token' in data, "No access_token in response"
        print(f"  ✓ Case-insensitive login works: {data['user']['full_name']}")

    def test_email_with_spaces(self):
        """Test that email with trailing spaces works"""
        creds = {'email': '  admin.gn@stanvard.school  ', 'password': 'admin123'}
        print(f"  → Attempting login with email with spaces: '{creds['email']}'")
        r = requests.post(f"{BASE_URL}/auth/login", json=creds)
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        data = r.json()
        assert 'access_token' in data, "No access_token in response"
        print(f"  ✓ Email with spaces works: {data['user']['full_name']}")

    def test_response_structure(self):
        """Test that login response has correct structure"""
        creds = CREDENTIALS['admin_gn']
        print(f"  → Testing response structure")
        r = requests.post(f"{BASE_URL}/auth/login", json=creds)
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        data = r.json()
        
        # Check access_token
        assert 'access_token' in data, "Missing access_token"
        assert isinstance(data['access_token'], str), "access_token should be string"
        assert len(data['access_token']) > 20, "access_token seems too short"
        
        # Check user object
        assert 'user' in data, "Missing user"
        user = data['user']
        assert 'id' in user, "User missing id"
        assert 'email' in user, "User missing email"
        assert 'full_name' in user, "User missing full_name"
        assert 'role' in user, "User missing role"
        assert 'password_hash' not in user, "User should not contain password_hash"
        
        print(f"  ✓ Response structure correct: access_token={len(data['access_token'])} chars, user fields={list(user.keys())[:5]}")

    def test_auth_me(self):
        """Test /auth/me endpoint"""
        # First login
        creds = CREDENTIALS['admin_gn']
        r = requests.post(f"{BASE_URL}/auth/login", json=creds)
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        token = r.json()['access_token']
        
        # Then call /auth/me
        print(f"  → Testing /auth/me with valid token")
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        assert r.status_code == 200, f"/auth/me failed: {r.status_code} {r.text}"
        user = r.json()
        assert user['email'] == creds['email'], f"Expected email {creds['email']}, got {user['email']}"
        assert user['role'] == 'school_admin', f"Expected role school_admin, got {user['role']}"
        print(f"  ✓ /auth/me returned: {user['full_name']} ({user['role']})")

    def test_invalid_token(self):
        """Test that invalid token returns 401"""
        print(f"  → Testing /auth/me with invalid token")
        headers = {'Authorization': 'Bearer invalid_token_12345'}
        r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print(f"  ✓ Invalid token correctly returns 401")


if __name__ == '__main__':
    runner = LoginTestRunner()
    sys.exit(runner.run_all_tests())
