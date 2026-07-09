"""
Backend API Tests for Stanvard School ERP - New Fee Management Endpoints
Tests PATCH/DELETE fee heads, DELETE fee plans, and GET fee-schedule
"""
import requests
import sys
from datetime import datetime

# Get BASE_URL from frontend/.env
BASE_URL = "https://data-pull-6.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
CREDENTIALS = {
    'superadmin': {'email': 'superadmin@stanvard.school', 'password': 'Stanvard@2026'},
    'accountant': {'email': 'accountant@stanvard.school', 'password': 'Accountant@2026'},
    'parent': {'username': '9079111899', 'password': '111899'},  # Linked to Disha Gadri (KNP-984)
}

class TestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tokens = {}
        self.users = {}
        self.failed_tests = []
        self.kanpur_school_id = None
        self.test_fee_head_id = None
        self.test_fee_plan_id = None
        self.disha_student_id = None

    def test(self, name, func):
        """Run a single test"""
        self.tests_run += 1
        print(f"\n{'='*80}")
        print(f"TEST {self.tests_run}: {name}")
        print('='*80)
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
        # Parent uses username field, others use email
        if role == 'parent':
            login_data = {'email': creds['username'], 'password': creds['password']}
        else:
            login_data = creds
        
        print(f"  → Logging in as {role}")
        r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
        data = r.json()
        assert 'access_token' in data, "No access_token in response"
        assert 'user' in data, "No user in response"
        self.tokens[role] = data['access_token']
        self.users[role] = data['user']
        print(f"  ✓ Logged in as {data['user']['full_name']} (role: {data['user']['role']})")
        return data

    def headers(self, role, school_id=None):
        """Get auth headers"""
        h = {'Authorization': f"Bearer {self.tokens[role]}"}
        if school_id:
            h['X-School-Id'] = school_id
        return h

    def get(self, url, role, school_id=None, expected=None):
        """GET request"""
        r = requests.get(f"{BASE_URL}{url}", headers=self.headers(role, school_id))
        if expected is not None:
            assert r.status_code == expected, f"Expected {expected}, got {r.status_code}: {r.text}"
        return r

    def post(self, url, role, data, school_id=None, expected=None):
        """POST request"""
        r = requests.post(f"{BASE_URL}{url}", json=data, headers=self.headers(role, school_id))
        if expected is not None:
            assert r.status_code == expected, f"Expected {expected}, got {r.status_code}: {r.text}"
        return r

    def patch(self, url, role, data, school_id=None, expected=None):
        """PATCH request"""
        r = requests.patch(f"{BASE_URL}{url}", json=data, headers=self.headers(role, school_id))
        if expected is not None:
            assert r.status_code == expected, f"Expected {expected}, got {r.status_code}: {r.text}"
        return r

    def delete(self, url, role, school_id=None, expected=None):
        """DELETE request"""
        r = requests.delete(f"{BASE_URL}{url}", headers=self.headers(role, school_id))
        if expected is not None:
            assert r.status_code == expected, f"Expected {expected}, got {r.status_code}: {r.text}"
        return r

    def run_all_tests(self):
        """Run all backend tests"""
        print("\n" + "="*80)
        print("STANVARD SCHOOL ERP - NEW FEE MANAGEMENT ENDPOINTS TESTS")
        print("="*80)

        # ===== SETUP & AUTH TESTS =====
        self.test("AUTH: Login with superadmin", lambda: self.test_login_superadmin())
        self.test("AUTH: Login with accountant", lambda: self.test_login_accountant())
        self.test("AUTH: Login with parent (9079111899)", lambda: self.test_login_parent())
        
        # ===== SETUP: Get Kanpur school and student data =====
        self.test("SETUP: Get Kanpur school ID", lambda: self.test_get_kanpur_school())
        self.test("SETUP: Find Disha Gadri student ID", lambda: self.test_find_disha_student())
        
        # ===== REGRESSION TESTS (light-touch) =====
        self.test("REGRESSION: GET /fees/plans returns 13 plans", lambda: self.test_get_fee_plans())
        self.test("REGRESSION: GET /fees/heads returns at least 1 head", lambda: self.test_get_fee_heads())
        self.test("REGRESSION: POST /fees/heads still works", lambda: self.test_create_fee_head())
        self.test("REGRESSION: POST /fees/plans still works", lambda: self.test_create_fee_plan())
        
        # ===== NEW ENDPOINT TESTS =====
        # 1. PATCH /api/fees/heads/{head_id}
        self.test("FEE HEAD EDIT: PATCH as super_admin updates name and category → 200", 
                  lambda: self.test_patch_fee_head_superadmin())
        self.test("FEE HEAD EDIT: PATCH as accountant → 403", 
                  lambda: self.test_patch_fee_head_accountant_forbidden())
        
        # 2. DELETE /api/fees/heads/{head_id}
        self.test("FEE HEAD DELETE: DELETE unreferenced head as super_admin → 200", 
                  lambda: self.test_delete_unreferenced_fee_head())
        self.test("FEE HEAD DELETE: DELETE referenced head (Tuition Fee) → 400 with detail", 
                  lambda: self.test_delete_referenced_fee_head())
        self.test("FEE HEAD DELETE: DELETE as accountant → 403", 
                  lambda: self.test_delete_fee_head_accountant_forbidden())
        
        # 3. DELETE /api/fees/plans/{plan_id}
        self.test("FEE PLAN DELETE: DELETE plan used by assignments → 400 with detail", 
                  lambda: self.test_delete_used_fee_plan())
        self.test("FEE PLAN DELETE: DELETE fresh unused plan → 200", 
                  lambda: self.test_delete_unused_fee_plan())
        self.test("FEE PLAN DELETE: DELETE as accountant → 403", 
                  lambda: self.test_delete_fee_plan_accountant_forbidden())
        
        # 4. GET /api/fees/student/{student_id}/fee-schedule
        self.test("FEE SCHEDULE: GET as super_admin returns correct structure", 
                  lambda: self.test_fee_schedule_superadmin())
        self.test("FEE SCHEDULE: GET as accountant returns correct structure", 
                  lambda: self.test_fee_schedule_accountant())
        self.test("FEE SCHEDULE: Verify schedule has 12 months Apr-Mar", 
                  lambda: self.test_fee_schedule_12_months())
        self.test("FEE SCHEDULE: Verify monthly_amount ≈ net_annual/12", 
                  lambda: self.test_fee_schedule_monthly_calculation())
        self.test("FEE SCHEDULE: Verify sum of schedule amounts ≈ 12 * monthly_amount", 
                  lambda: self.test_fee_schedule_sum_validation())
        self.test("FEE SCHEDULE: Verify payable_full = remaining - discount", 
                  lambda: self.test_fee_schedule_payable_full())
        self.test("FEE SCHEDULE: Verify paid months reflected (Divyansh Dangi)", 
                  lambda: self.test_fee_schedule_paid_months())
        self.test("FEE SCHEDULE: Parent can access own child (Disha Gadri) → 200", 
                  lambda: self.test_fee_schedule_parent_own_child())
        self.test("FEE SCHEDULE: Parent cannot access other student → 403", 
                  lambda: self.test_fee_schedule_parent_other_child())

        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n" + "="*80)
            print("FAILED TESTS DETAILS")
            print("="*80)
            for ft in self.failed_tests:
                print(f"\n❌ {ft['test']}")
                print(f"   Error: {ft['error']}")

        return 0 if self.tests_failed == 0 else 1

    # ===== TEST IMPLEMENTATIONS =====
    
    def test_login_superadmin(self):
        data = self.login('superadmin')
        assert data['user']['role'] == 'super_admin'

    def test_login_accountant(self):
        data = self.login('accountant')
        assert data['user']['role'] == 'accountant'

    def test_login_parent(self):
        data = self.login('parent')
        assert data['user']['role'] == 'parent'
        assert 'linked_student_ids' in data['user'] or 'linked_student_id' in data['user'], \
            "Parent should have linked student"

    def test_get_kanpur_school(self):
        """Get Kanpur school ID (The Stanvard Sec. School, Girwa, Udaipur)"""
        r = self.get('/schools', 'superadmin', expected=200)
        schools = r.json()
        # Find Kanpur school (code KNP or name contains Kanpur/Girwa/Udaipur)
        kanpur = next((s for s in schools if 'KNP' in s.get('code', '') or 
                      'Kanpur' in s.get('name', '') or 'Girwa' in s.get('name', '') or
                      'Udaipur' in s.get('name', '')), None)
        assert kanpur is not None, "Kanpur school not found"
        self.kanpur_school_id = kanpur['id']
        print(f"  ✓ Found Kanpur school: {kanpur['name']} (ID: {self.kanpur_school_id})")

    def test_find_disha_student(self):
        """Find Disha Gadri student (KNP-984)"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        r = self.get('/students', 'superadmin', school_id=self.kanpur_school_id, expected=200)
        students = r.json()
        # Find Disha Gadri by name or admission number
        disha = next((s for s in students if 'Disha' in s.get('full_name', '') and 
                     'Gadri' in s.get('full_name', '')), None)
        if not disha:
            # Try by admission number
            disha = next((s for s in students if s.get('admission_number') == 'KNP-984'), None)
        
        assert disha is not None, "Disha Gadri student not found"
        self.disha_student_id = disha['id']
        print(f"  ✓ Found Disha Gadri: {disha['full_name']} (ID: {self.disha_student_id}, Admission: {disha.get('admission_number')})")

    def test_get_fee_plans(self):
        """Regression: GET /fees/plans returns 13 plans"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        r = self.get('/fees/plans', 'superadmin', school_id=self.kanpur_school_id, expected=200)
        plans = r.json()
        assert isinstance(plans, list), "Should return list"
        assert len(plans) == 13, f"Expected 13 plans, got {len(plans)}"
        print(f"  ✓ Found {len(plans)} fee plans")

    def test_get_fee_heads(self):
        """Regression: GET /fees/heads returns at least 1 head"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        r = self.get('/fees/heads', 'superadmin', school_id=self.kanpur_school_id, expected=200)
        heads = r.json()
        assert isinstance(heads, list), "Should return list"
        assert len(heads) >= 1, f"Expected at least 1 fee head, got {len(heads)}"
        print(f"  ✓ Found {len(heads)} fee heads")

    def test_create_fee_head(self):
        """Regression: POST /fees/heads still works"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        head_data = {
            'school_id': self.kanpur_school_id,
            'name': f'Test Fee Head {datetime.now().strftime("%H%M%S")}',
            'category': 'academic',
            'description': 'Test fee head for regression'
        }
        r = self.post('/fees/heads', 'superadmin', head_data, school_id=self.kanpur_school_id, expected=200)
        head = r.json()
        assert 'id' in head, "Should have id"
        assert head['name'] == head_data['name'], "Name should match"
        self.test_fee_head_id = head['id']
        print(f"  ✓ Created fee head: {head['name']} (ID: {head['id']})")

    def test_create_fee_plan(self):
        """Regression: POST /fees/plans still works"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        if not self.test_fee_head_id:
            self.test_create_fee_head()
        
        plan_data = {
            'school_id': self.kanpur_school_id,
            'name': f'Test Fee Plan {datetime.now().strftime("%H%M%S")}',
            'academic_session': '2026-27',
            'class_id': None,
            'items': [
                {'fee_head_id': self.test_fee_head_id, 'fee_head_name': 'Test Fee', 'amount': 5000, 'frequency': 'annual'}
            ],
            'annual_discount_percent': 5.0,
            'late_fee_amount': 100,
            'late_fee_after_day': 10
        }
        r = self.post('/fees/plans', 'superadmin', plan_data, school_id=self.kanpur_school_id, expected=200)
        plan = r.json()
        assert 'id' in plan, "Should have id"
        assert plan['name'] == plan_data['name'], "Name should match"
        self.test_fee_plan_id = plan['id']
        print(f"  ✓ Created fee plan: {plan['name']} (ID: {plan['id']})")

    def test_patch_fee_head_superadmin(self):
        """PATCH /fees/heads/{head_id} as super_admin updates name and category → 200"""
        if not self.test_fee_head_id:
            self.test_create_fee_head()
        
        update_data = {
            'name': f'Updated Fee Head {datetime.now().strftime("%H%M%S")}',
            'category': 'transport'
        }
        r = self.patch(f'/fees/heads/{self.test_fee_head_id}', 'superadmin', update_data, expected=200)
        head = r.json()
        assert head['name'] == update_data['name'], f"Name should be updated to {update_data['name']}"
        assert head['category'] == update_data['category'], f"Category should be updated to {update_data['category']}"
        print(f"  ✓ Updated fee head: name={head['name']}, category={head['category']}")

    def test_patch_fee_head_accountant_forbidden(self):
        """PATCH /fees/heads/{head_id} as accountant → 403"""
        if not self.test_fee_head_id:
            self.test_create_fee_head()
        
        update_data = {'name': 'Should Not Update'}
        r = self.patch(f'/fees/heads/{self.test_fee_head_id}', 'accountant', update_data, expected=403)
        print(f"  ✓ Accountant correctly forbidden from updating fee head (403)")

    def test_delete_unreferenced_fee_head(self):
        """DELETE /fees/heads/{head_id} unreferenced head as super_admin → 200"""
        # Create a new fee head that's not referenced
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        head_data = {
            'school_id': self.kanpur_school_id,
            'name': f'Delete Me {datetime.now().strftime("%H%M%S")}',
            'category': 'other'
        }
        r = self.post('/fees/heads', 'superadmin', head_data, school_id=self.kanpur_school_id, expected=200)
        head_id = r.json()['id']
        
        # Now delete it
        r = self.delete(f'/fees/heads/{head_id}', 'superadmin', expected=200)
        result = r.json()
        assert result.get('ok') == True, "Should return ok: true"
        print(f"  ✓ Deleted unreferenced fee head successfully")

    def test_delete_referenced_fee_head(self):
        """DELETE /fees/heads/{head_id} referenced head (Tuition Fee) → 400 with detail"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        # Get existing fee heads and find "Tuition Fee"
        r = self.get('/fees/heads', 'superadmin', school_id=self.kanpur_school_id, expected=200)
        heads = r.json()
        tuition_head = next((h for h in heads if 'Tuition' in h.get('name', '')), None)
        assert tuition_head is not None, "Tuition Fee head not found"
        
        # Try to delete it - should fail with 400
        r = self.delete(f'/fees/heads/{tuition_head["id"]}', 'superadmin', expected=400)
        error_detail = r.json().get('detail', '')
        assert 'used in' in error_detail.lower() and 'plan' in error_detail.lower(), \
            f"Error detail should mention usage in plans: {error_detail}"
        print(f"  ✓ Delete referenced fee head correctly blocked: {error_detail}")

    def test_delete_fee_head_accountant_forbidden(self):
        """DELETE /fees/heads/{head_id} as accountant → 403"""
        if not self.test_fee_head_id:
            self.test_create_fee_head()
        
        r = self.delete(f'/fees/heads/{self.test_fee_head_id}', 'accountant', expected=403)
        print(f"  ✓ Accountant correctly forbidden from deleting fee head (403)")

    def test_delete_used_fee_plan(self):
        """DELETE /fees/plans/{plan_id} used by assignments → 400 with detail"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        # Get existing fee plans - any of the 13 seeded plans should be used by 375 assignments
        r = self.get('/fees/plans', 'superadmin', school_id=self.kanpur_school_id, expected=200)
        plans = r.json()
        assert len(plans) > 0, "Should have at least one plan"
        
        # Try to delete the first plan - should fail with 400
        plan_id = plans[0]['id']
        r = self.delete(f'/fees/plans/{plan_id}', 'superadmin', expected=400)
        error_detail = r.json().get('detail', '')
        assert 'used in' in error_detail.lower() and 'assignment' in error_detail.lower(), \
            f"Error detail should mention usage in assignments: {error_detail}"
        print(f"  ✓ Delete used fee plan correctly blocked: {error_detail}")

    def test_delete_unused_fee_plan(self):
        """DELETE /fees/plans/{plan_id} fresh unused plan → 200"""
        if not self.test_fee_plan_id:
            self.test_create_fee_plan()
        
        # Delete the test plan we created (not assigned to any student)
        r = self.delete(f'/fees/plans/{self.test_fee_plan_id}', 'superadmin', expected=200)
        result = r.json()
        assert result.get('ok') == True, "Should return ok: true"
        print(f"  ✓ Deleted unused fee plan successfully")

    def test_delete_fee_plan_accountant_forbidden(self):
        """DELETE /fees/plans/{plan_id} as accountant → 403"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        # Get any plan
        r = self.get('/fees/plans', 'superadmin', school_id=self.kanpur_school_id, expected=200)
        plans = r.json()
        assert len(plans) > 0, "Should have at least one plan"
        
        r = self.delete(f'/fees/plans/{plans[0]["id"]}', 'accountant', expected=403)
        print(f"  ✓ Accountant correctly forbidden from deleting fee plan (403)")

    def test_fee_schedule_superadmin(self):
        """GET /fees/student/{student_id}/fee-schedule as super_admin returns correct structure"""
        if not self.disha_student_id:
            self.test_find_disha_student()
        
        r = self.get(f'/fees/student/{self.disha_student_id}/fee-schedule', 'superadmin', expected=200)
        data = r.json()
        
        # Verify structure
        required_fields = ['student', 'academic_session', 'annual_total', 'concession', 
                          'net_annual', 'monthly_amount', 'total_paid', 'remaining_balance',
                          'annual_discount_percent', 'full_payment_discount', 'payable_full',
                          'schedule', 'fee_head_names']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify types
        assert isinstance(data['student'], dict), "student should be dict"
        assert isinstance(data['academic_session'], str), "academic_session should be string"
        assert isinstance(data['annual_total'], (int, float)), "annual_total should be number"
        assert data['annual_total'] > 0, "annual_total should be > 0"
        assert isinstance(data['schedule'], list), "schedule should be list"
        assert isinstance(data['fee_head_names'], list), "fee_head_names should be list"
        
        print(f"  ✓ Fee schedule structure valid: student={data['student']['full_name']}, " +
              f"annual_total={data['annual_total']}, net_annual={data['net_annual']}, " +
              f"monthly_amount={data['monthly_amount']}, total_paid={data['total_paid']}")

    def test_fee_schedule_accountant(self):
        """GET /fees/student/{student_id}/fee-schedule as accountant returns correct structure"""
        if not self.disha_student_id:
            self.test_find_disha_student()
        
        r = self.get(f'/fees/student/{self.disha_student_id}/fee-schedule', 'accountant', expected=200)
        data = r.json()
        assert 'student' in data and 'schedule' in data, "Should have student and schedule"
        print(f"  ✓ Accountant can access fee schedule")

    def test_fee_schedule_12_months(self):
        """Verify schedule has 12 months Apr-Mar"""
        if not self.disha_student_id:
            self.test_find_disha_student()
        
        r = self.get(f'/fees/student/{self.disha_student_id}/fee-schedule', 'superadmin', expected=200)
        data = r.json()
        schedule = data['schedule']
        
        assert len(schedule) == 12, f"Schedule should have 12 months, got {len(schedule)}"
        
        # Verify structure of each month
        for i, month in enumerate(schedule):
            assert month['index'] == i, f"Month index should be {i}, got {month['index']}"
            assert 'label' in month, f"Month {i} missing label"
            assert 'month' in month, f"Month {i} missing month"
            assert 'year' in month, f"Month {i} missing year"
            assert 'amount' in month, f"Month {i} missing amount"
            assert 'paid_amount' in month, f"Month {i} missing paid_amount"
            assert 'status' in month, f"Month {i} missing status"
            assert month['status'] in ['paid', 'partial', 'overdue', 'pending'], \
                f"Month {i} has invalid status: {month['status']}"
        
        # Verify first month is April
        assert 'April' in schedule[0]['label'], f"First month should be April, got {schedule[0]['label']}"
        
        print(f"  ✓ Schedule has 12 months: {schedule[0]['label']} to {schedule[11]['label']}")

    def test_fee_schedule_monthly_calculation(self):
        """Verify monthly_amount ≈ net_annual/12"""
        if not self.disha_student_id:
            self.test_find_disha_student()
        
        r = self.get(f'/fees/student/{self.disha_student_id}/fee-schedule', 'superadmin', expected=200)
        data = r.json()
        
        net_annual = data['net_annual']
        monthly_amount = data['monthly_amount']
        expected_monthly = round(net_annual / 12.0, 2)
        
        assert monthly_amount == expected_monthly, \
            f"monthly_amount {monthly_amount} should equal round(net_annual/12, 2) = {expected_monthly}"
        
        print(f"  ✓ Monthly calculation correct: {net_annual}/12 = {monthly_amount}")

    def test_fee_schedule_sum_validation(self):
        """Verify sum of schedule amounts ≈ 12 * monthly_amount"""
        if not self.disha_student_id:
            self.test_find_disha_student()
        
        r = self.get(f'/fees/student/{self.disha_student_id}/fee-schedule', 'superadmin', expected=200)
        data = r.json()
        
        schedule = data['schedule']
        monthly_amount = data['monthly_amount']
        
        total_schedule_amount = sum(month['amount'] for month in schedule)
        expected_total = 12 * monthly_amount
        
        # Allow small rounding difference (within 1 rupee)
        diff = abs(total_schedule_amount - expected_total)
        assert diff <= 1.0, \
            f"Sum of schedule amounts {total_schedule_amount} should ≈ 12 * monthly_amount {expected_total} (diff: {diff})"
        
        print(f"  ✓ Schedule sum validation: {total_schedule_amount} ≈ 12 * {monthly_amount} = {expected_total}")

    def test_fee_schedule_payable_full(self):
        """Verify payable_full = remaining_balance - full_payment_discount"""
        if not self.disha_student_id:
            self.test_find_disha_student()
        
        r = self.get(f'/fees/student/{self.disha_student_id}/fee-schedule', 'superadmin', expected=200)
        data = r.json()
        
        remaining_balance = data['remaining_balance']
        full_payment_discount = data['full_payment_discount']
        payable_full = data['payable_full']
        
        expected_payable = round(max(remaining_balance - full_payment_discount, 0.0), 2)
        
        assert payable_full == expected_payable, \
            f"payable_full {payable_full} should equal remaining_balance {remaining_balance} - full_payment_discount {full_payment_discount} = {expected_payable}"
        
        print(f"  ✓ Payable full calculation: {remaining_balance} - {full_payment_discount} = {payable_full}")

    def test_fee_schedule_paid_months(self):
        """Verify paid months reflected (Divyansh Dangi with opening balance ₹1390)"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        
        # Find Divyansh Dangi
        r = self.get('/students', 'superadmin', school_id=self.kanpur_school_id, expected=200)
        students = r.json()
        divyansh = next((s for s in students if 'Divyansh' in s.get('full_name', '') and 
                        'Dangi' in s.get('full_name', '')), None)
        
        if not divyansh:
            print(f"  ⚠ Skipped: Divyansh Dangi not found")
            return
        
        r = self.get(f'/fees/student/{divyansh["id"]}/fee-schedule', 'superadmin', expected=200)
        data = r.json()
        
        # Verify total_paid > 0
        assert data['total_paid'] > 0, f"Divyansh should have paid amount > 0, got {data['total_paid']}"
        
        # Verify at least one month is paid or partial
        schedule = data['schedule']
        paid_or_partial = [m for m in schedule if m['status'] in ['paid', 'partial']]
        assert len(paid_or_partial) > 0, "At least one month should be paid or partial"
        
        print(f"  ✓ Paid months reflected: total_paid={data['total_paid']}, " +
              f"{len(paid_or_partial)} months paid/partial")

    def test_fee_schedule_parent_own_child(self):
        """Parent can access own child (Disha Gadri) → 200"""
        if not self.disha_student_id:
            self.test_find_disha_student()
        
        r = self.get(f'/fees/student/{self.disha_student_id}/fee-schedule', 'parent', expected=200)
        data = r.json()
        assert 'student' in data and 'schedule' in data, "Should have student and schedule"
        print(f"  ✓ Parent can access own child's fee schedule: {data['student']['full_name']}")

    def test_fee_schedule_parent_other_child(self):
        """Parent cannot access other student → 403"""
        if not self.kanpur_school_id:
            self.test_get_kanpur_school()
        if not self.disha_student_id:
            self.test_find_disha_student()
        
        # Get another student (not Disha)
        r = self.get('/students', 'superadmin', school_id=self.kanpur_school_id, expected=200)
        students = r.json()
        other_student = next((s for s in students if s['id'] != self.disha_student_id), None)
        
        if not other_student:
            print(f"  ⚠ Skipped: No other student found")
            return
        
        r = self.get(f'/fees/student/{other_student["id"]}/fee-schedule', 'parent', expected=403)
        print(f"  ✓ Parent correctly forbidden from accessing other student (403)")


if __name__ == '__main__':
    runner = TestRunner()
    exit_code = runner.run_all_tests()
    sys.exit(exit_code)
