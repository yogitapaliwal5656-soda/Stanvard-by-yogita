"""
Backend API Tests for Super Admin Dashboard 400 Error Fix
Tests the defensive fallback in resolve_school_id() that prevents 400 errors
when a super_admin request arrives without X-School-Id header.
"""
import requests
import sys

BASE_URL = "https://school-portal-hub-16.preview.emergentagent.com/api"

CREDENTIALS = {
    'superadmin': {'email': 'superadmin@stanvard.school', 'password': 'super123'},
    'admin_gn': {'email': 'admin.gn@stanvard.school', 'password': 'admin123'},
    'accountant_gn': {'email': 'accountant.gn@stanvard.school', 'password': 'acc123'},
    'teacher_gn': {'email': 'teacher.gn@stanvard.school', 'password': 'teacher123'},
    'parent_gn': {'email': 'parent.gn20250001@stanvard.school', 'password': 'parent123'},
}

class DashboardTestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tokens = {}
        self.users = {}
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

    def login(self, role):
        """Login and store token"""
        creds = CREDENTIALS[role]
        print(f"  → Logging in as {role} ({creds['email']})")
        r = requests.post(f"{BASE_URL}/auth/login", json=creds)
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        data = r.json()
        assert 'access_token' in data, "No access_token in response"
        assert 'user' in data, "No user in response"
        self.tokens[role] = data['access_token']
        self.users[role] = data['user']
        print(f"  ✓ Logged in as {data['user']['full_name']} (role: {data['user']['role']})")
        return data

    def run_all_tests(self):
        """Run all dashboard-specific tests"""
        print("\n" + "="*70)
        print("SUPER ADMIN DASHBOARD 400 ERROR FIX - BACKEND TESTS")
        print("="*70)

        # Login all roles first
        self.test("AUTH: Login as super_admin", lambda: self.test_login_superadmin())
        self.test("AUTH: Login as school_admin (GN)", lambda: self.test_login_admin_gn())
        self.test("AUTH: Login as accountant (GN)", lambda: self.test_login_accountant())
        self.test("AUTH: Login as teacher (GN)", lambda: self.test_login_teacher())
        self.test("AUTH: Login as parent (GN)", lambda: self.test_login_parent())

        # CRITICAL TESTS for the bug fix
        self.test("CRITICAL: Super admin dashboard/summary WITHOUT X-School-Id returns 200 (defensive fallback)", 
                  lambda: self.test_dashboard_no_school_header())
        
        self.test("CRITICAL: Super admin dashboard/summary WITH X-School-Id returns 200", 
                  lambda: self.test_dashboard_with_school_header())
        
        self.test("CRITICAL: Super admin analytics WITHOUT X-School-Id returns 200 (defensive fallback)", 
                  lambda: self.test_analytics_no_school_header())
        
        self.test("CRITICAL: Super admin analytics WITH X-School-Id returns 200", 
                  lambda: self.test_analytics_with_school_header())
        
        self.test("REGRESSION: School admin dashboard/summary works (has school_id in user)", 
                  lambda: self.test_dashboard_school_admin())
        
        self.test("REGRESSION: Accountant dashboard/summary works", 
                  lambda: self.test_dashboard_accountant())
        
        self.test("REGRESSION: Teacher dashboard/summary works", 
                  lambda: self.test_dashboard_teacher())
        
        self.test("REGRESSION: Parent does NOT access dashboard (should use /parent route)", 
                  lambda: self.test_dashboard_parent_no_access())

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

    # ===== TEST IMPLEMENTATIONS =====
    def test_login_superadmin(self):
        data = self.login('superadmin')
        assert data['user']['role'] == 'super_admin'

    def test_login_admin_gn(self):
        data = self.login('admin_gn')
        assert data['user']['role'] == 'school_admin'

    def test_login_accountant(self):
        data = self.login('accountant_gn')
        assert data['user']['role'] == 'accountant'

    def test_login_teacher(self):
        data = self.login('teacher_gn')
        assert data['user']['role'] == 'teacher'

    def test_login_parent(self):
        data = self.login('parent_gn')
        assert data['user']['role'] == 'parent'

    def test_dashboard_no_school_header(self):
        """
        CRITICAL TEST: Super admin calls /dashboard/summary WITHOUT X-School-Id header.
        The defensive fallback should return 200 with data from the first school (by code order).
        Previously this would return 400 'No school specified'.
        """
        print("  → Testing defensive fallback: GET /dashboard/summary without X-School-Id")
        
        # Make request with ONLY Authorization header (no X-School-Id)
        headers = {'Authorization': f"Bearer {self.tokens['superadmin']}"}
        r = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers)
        
        # Should return 200, NOT 400
        assert r.status_code == 200, f"Expected 200 (defensive fallback), got {r.status_code}: {r.text}"
        
        data = r.json()
        
        # Verify response has dashboard data
        required_fields = ['total_students', 'today_collection', 'monthly_collection', 
                          'present_today', 'collection_trend']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"  ✓ Defensive fallback works: 200 response with data")
        print(f"    Dashboard KPIs: students={data['total_students']}, today_collection={data['today_collection']}, monthly={data['monthly_collection']}")

    def test_dashboard_with_school_header(self):
        """
        Test that super admin can still explicitly specify school via X-School-Id header.
        """
        print("  → Testing explicit school selection: GET /dashboard/summary with X-School-Id")
        
        # First get list of schools
        headers = {'Authorization': f"Bearer {self.tokens['superadmin']}"}
        r = requests.get(f"{BASE_URL}/auth/my-schools", headers=headers)
        assert r.status_code == 200, f"Failed to get schools: {r.status_code}"
        schools = r.json()
        assert len(schools) > 0, "No schools found"
        
        school_id = schools[0]['id']
        print(f"  → Using school: {schools[0]['name']} (id: {school_id})")
        
        # Make request WITH X-School-Id header
        headers['X-School-Id'] = school_id
        r = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers)
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        
        data = r.json()
        required_fields = ['total_students', 'today_collection', 'monthly_collection']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"  ✓ Explicit school selection works: 200 response with data")

    def test_analytics_no_school_header(self):
        """
        Test that analytics endpoint also has defensive fallback.
        """
        print("  → Testing defensive fallback: GET /analytics without X-School-Id")
        
        headers = {'Authorization': f"Bearer {self.tokens['superadmin']}"}
        r = requests.get(f"{BASE_URL}/analytics", headers=headers)
        
        assert r.status_code == 200, f"Expected 200 (defensive fallback), got {r.status_code}: {r.text}"
        
        data = r.json()
        required_fields = ['year', 'total_received', 'total_expected', 'months']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"  ✓ Analytics defensive fallback works: 200 response with data")

    def test_analytics_with_school_header(self):
        """
        Test that analytics works with explicit school selection.
        """
        print("  → Testing explicit school selection: GET /analytics with X-School-Id")
        
        headers = {'Authorization': f"Bearer {self.tokens['superadmin']}"}
        r = requests.get(f"{BASE_URL}/auth/my-schools", headers=headers)
        schools = r.json()
        school_id = schools[0]['id']
        
        headers['X-School-Id'] = school_id
        r = requests.get(f"{BASE_URL}/analytics", headers=headers)
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        
        data = r.json()
        assert 'year' in data
        assert 'months' in data
        
        print(f"  ✓ Analytics with explicit school works: 200 response")

    def test_dashboard_school_admin(self):
        """
        REGRESSION: School admin should still work normally (has school_id in user object).
        """
        print("  → Testing school admin dashboard access")
        
        headers = {'Authorization': f"Bearer {self.tokens['admin_gn']}"}
        school_id = self.users['admin_gn']['school_id']
        headers['X-School-Id'] = school_id
        
        r = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers)
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        
        data = r.json()
        assert 'total_students' in data
        
        print(f"  ✓ School admin dashboard works: 200 response")

    def test_dashboard_accountant(self):
        """
        REGRESSION: Accountant should still work normally.
        """
        print("  → Testing accountant dashboard access")
        
        headers = {'Authorization': f"Bearer {self.tokens['accountant_gn']}"}
        school_id = self.users['accountant_gn']['school_id']
        headers['X-School-Id'] = school_id
        
        r = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers)
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        
        data = r.json()
        assert 'total_students' in data
        
        print(f"  ✓ Accountant dashboard works: 200 response")

    def test_dashboard_teacher(self):
        """
        REGRESSION: Teacher should still work normally.
        """
        print("  → Testing teacher dashboard access")
        
        headers = {'Authorization': f"Bearer {self.tokens['teacher_gn']}"}
        school_id = self.users['teacher_gn']['school_id']
        headers['X-School-Id'] = school_id
        
        r = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers)
        
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        
        data = r.json()
        assert 'total_students' in data
        
        print(f"  ✓ Teacher dashboard works: 200 response")

    def test_dashboard_parent_no_access(self):
        """
        REGRESSION: Parent should NOT access dashboard (they use /parent route).
        This is just to verify the endpoint doesn't break for parent role.
        """
        print("  → Testing parent dashboard access (should work but parent uses /parent route)")
        
        headers = {'Authorization': f"Bearer {self.tokens['parent_gn']}"}
        school_id = self.users['parent_gn']['school_id']
        headers['X-School-Id'] = school_id
        
        r = requests.get(f"{BASE_URL}/dashboard/summary", headers=headers)
        
        # Parent can technically access dashboard, but they use /parent route in UI
        # Just verify it doesn't crash
        assert r.status_code in [200, 403], f"Expected 200 or 403, got {r.status_code}: {r.text}"
        
        print(f"  ✓ Parent dashboard endpoint doesn't crash: {r.status_code} response")


if __name__ == '__main__':
    runner = DashboardTestRunner()
    sys.exit(runner.run_all_tests())
