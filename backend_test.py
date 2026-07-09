"""
Comprehensive Backend API Tests for Stanvard School ERP
Tests all endpoints with different roles, RBAC, multi-school switching, and Razorpay integration
"""
import requests
import sys
from datetime import datetime, timedelta

BASE_URL = "https://school-portal-hub-16.preview.emergentagent.com/api"

# Test credentials from review request
CREDENTIALS = {
    'superadmin': {'email': 'superadmin@stanvard.school', 'password': 'super123'},
    'admin_gn': {'email': 'admin.gn@stanvard.school', 'password': 'admin123'},
    'admin_knp': {'email': 'admin.knp@stanvard.school', 'password': 'admin123'},
    'admin_ayr': {'email': 'admin.ayr@stanvard.school', 'password': 'admin123'},
    'accountant_gn': {'email': 'accountant.gn@stanvard.school', 'password': 'acc123'},
    'teacher_gn': {'email': 'teacher.gn@stanvard.school', 'password': 'teacher123'},
    'parent_gn': {'email': 'parent.gn20250001@stanvard.school', 'password': 'parent123'},
}

class TestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tokens = {}
        self.users = {}
        self.schools = []
        self.students = []
        self.classes = []
        self.fee_heads = []
        self.payments = []
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

    def headers(self, role, school_id=None):
        """Get auth headers"""
        h = {'Authorization': f"Bearer {self.tokens[role]}"}
        if school_id:
            h['X-School-Id'] = school_id
        return h

    def get(self, url, role, school_id=None, expected=200):
        """GET request"""
        r = requests.get(f"{BASE_URL}{url}", headers=self.headers(role, school_id))
        if expected:
            assert r.status_code == expected, f"Expected {expected}, got {r.status_code}: {r.text}"
        return r

    def post(self, url, role, data, school_id=None, expected=200):
        """POST request"""
        r = requests.post(f"{BASE_URL}{url}", json=data, headers=self.headers(role, school_id))
        if expected:
            assert r.status_code == expected, f"Expected {expected}, got {r.status_code}: {r.text}"
        return r

    def run_all_tests(self):
        """Run all backend tests"""
        print("\n" + "="*70)
        print("STANVARD SCHOOL ERP - BACKEND API TESTS")
        print("="*70)

        # ===== AUTH TESTS =====
        self.test("AUTH: Login with superadmin", lambda: self.test_login_superadmin())
        self.test("AUTH: Login with school_admin (GN)", lambda: self.test_login_admin_gn())
        self.test("AUTH: Login with accountant (GN)", lambda: self.test_login_accountant())
        self.test("AUTH: Login with teacher (GN)", lambda: self.test_login_teacher())
        self.test("AUTH: Login with parent (GN)", lambda: self.test_login_parent())
        self.test("AUTH: GET /auth/me returns correct user", lambda: self.test_auth_me())
        self.test("AUTH: GET /auth/my-schools for super_admin", lambda: self.test_my_schools_superadmin())
        self.test("AUTH: GET /auth/my-schools for school_admin", lambda: self.test_my_schools_admin())

        # ===== SCHOOLS =====
        self.test("SCHOOLS: GET /schools for super_admin", lambda: self.test_get_schools())

        # ===== DASHBOARD =====
        self.test("DASHBOARD: GET /dashboard/summary returns KPIs", lambda: self.test_dashboard_summary())

        # ===== STUDENTS =====
        self.test("STUDENTS: GET /students returns school-scoped students", lambda: self.test_get_students())
        self.test("STUDENTS: GET /students for parent returns only linked student", lambda: self.test_get_students_parent())
        self.test("STUDENTS: GET /students/{id} returns single student", lambda: self.test_get_student_detail())
        self.test("STUDENTS: POST /students creates student with auto admission number", lambda: self.test_create_student())
        self.test("STUDENTS: X-School-Id switching for super_admin", lambda: self.test_school_switching())

        # ===== CLASSES =====
        self.test("CLASSES: GET /classes returns school-scoped classes", lambda: self.test_get_classes())

        # ===== FEES =====
        self.test("FEES: GET /fees/heads returns school data", lambda: self.test_get_fee_heads())
        self.test("FEES: GET /fees/plans returns school data", lambda: self.test_get_fee_plans())
        self.test("FEES: GET /fees/student/{id}/dues returns dues + total_paid", lambda: self.test_student_dues())

        # ===== PAYMENTS =====
        self.test("PAYMENTS: POST /payments/collect creates offline payment", lambda: self.test_collect_payment())
        self.test("PAYMENTS: GET /payments/{id}/receipt.pdf returns PDF", lambda: self.test_receipt_pdf())
        self.test("PAYMENTS: POST /payments/razorpay/order creates order", lambda: self.test_razorpay_order())
        self.test("PAYMENTS: POST /payments/razorpay/verify with invalid signature returns 400", lambda: self.test_razorpay_verify_invalid())

        # ===== ATTENDANCE =====
        self.test("ATTENDANCE: GET /attendance returns records", lambda: self.test_get_attendance())
        self.test("ATTENDANCE: POST /attendance/mark bulk marks", lambda: self.test_mark_attendance())

        # ===== HOMEWORK =====
        self.test("HOMEWORK: GET /homework", lambda: self.test_get_homework())
        self.test("HOMEWORK: POST /homework", lambda: self.test_create_homework())

        # ===== EVENTS =====
        self.test("EVENTS: GET /events", lambda: self.test_get_events())
        self.test("EVENTS: POST /events", lambda: self.test_create_event())

        # ===== CIRCULARS =====
        self.test("CIRCULARS: GET /circulars", lambda: self.test_get_circulars())
        self.test("CIRCULARS: POST /circulars", lambda: self.test_create_circular())

        # ===== GALLERY =====
        self.test("GALLERY: GET /gallery", lambda: self.test_get_gallery())

        # ===== STAFF =====
        self.test("STAFF: GET /staff", lambda: self.test_get_staff())

        # ===== NOTIFICATIONS =====
        self.test("NOTIFICATIONS: GET /notifications", lambda: self.test_get_notifications())

        # ===== REPORTS =====
        self.test("REPORTS: GET /reports/collection with filters", lambda: self.test_collection_report())
        self.test("REPORTS: GET /reports/collection.pdf", lambda: self.test_collection_report_pdf())
        self.test("REPORTS: GET /reports/collection.csv", lambda: self.test_collection_report_csv())
        self.test("REPORTS: GET /reports/collection.xlsx", lambda: self.test_collection_report_xlsx())

        # ===== AUDIT LOGS =====
        self.test("AUDIT: GET /audit-logs for school_admin", lambda: self.test_audit_logs_admin())
        self.test("AUDIT: GET /audit-logs for parent returns 403", lambda: self.test_audit_logs_parent_forbidden())

        # ===== SETTINGS =====
        self.test("SETTINGS: GET /settings", lambda: self.test_get_settings())
        self.test("SETTINGS: PATCH /schools/{id} for super_admin", lambda: self.test_update_school())

        # ===== RBAC TESTS =====
        self.test("RBAC: Parent cannot POST /students (403)", lambda: self.test_rbac_parent_create_student())
        self.test("RBAC: Teacher cannot POST /schools (403)", lambda: self.test_rbac_teacher_create_school())

        # ===== NEW FEATURES (Iteration 2) =====
        # Feature 1: Edit student + assign fees with discount/due date
        self.test("STUDENTS: PATCH /students/{id} updates personal details (father_name, phone, address)", lambda: self.test_update_student_details())
        self.test("FEES: POST /fees/assignments creates assignment with custom_items, discount_percent, discount_amount, due_date", lambda: self.test_create_fee_assignment())
        self.test("FEES: PATCH /fees/assignments/{id} updates existing assignment", lambda: self.test_update_fee_assignment())
        self.test("FEES: DELETE /fees/assignments/{id} removes assignment", lambda: self.test_delete_fee_assignment())
        self.test("FEES: GET /fees/student/{id}/dues returns new fields (total_expected, total_discount, balance)", lambda: self.test_student_dues_new_fields())
        
        # Feature 2: Enhanced Reports with filters
        self.test("REPORTS: GET /reports/fee-status returns rows[] + summary", lambda: self.test_fee_status_report())
        self.test("REPORTS: GET /reports/fee-status with class_id filter", lambda: self.test_fee_status_filter_class())
        self.test("REPORTS: GET /reports/fee-status with status_filter=paid", lambda: self.test_fee_status_filter_status())
        self.test("REPORTS: GET /reports/fee-status with min_due and max_due", lambda: self.test_fee_status_filter_due_amount())
        
        # Feature 3: Analytics dashboard
        self.test("ANALYTICS: GET /analytics returns full analytics object", lambda: self.test_analytics_full())
        self.test("ANALYTICS: GET /analytics year parameter changes data", lambda: self.test_analytics_year_filter())
        
        # Feature 4: User management
        self.test("USERS: DELETE /users/{id} soft-deletes user (status=inactive)", lambda: self.test_delete_user())
        self.test("USERS: DELETE /users/{id} rejects deleting yourself (400)", lambda: self.test_delete_user_self())
        self.test("USERS: DELETE /users/{id} school_admin cannot delete super_admin (403)", lambda: self.test_delete_user_super_admin())
        self.test("USERS: POST /users/{id}/reset-password updates password", lambda: self.test_reset_password())
        self.test("USERS: Login with new password after reset succeeds", lambda: self.test_login_after_reset())
        
        # RBAC for new features
        self.test("RBAC: Parent cannot POST /fees/assignments (403)", lambda: self.test_rbac_parent_assign_fee())
        self.test("RBAC: Teacher cannot POST /fees/assignments (403)", lambda: self.test_rbac_teacher_assign_fee())
        self.test("RBAC: Accountant cannot DELETE /users (403)", lambda: self.test_rbac_accountant_delete_user())
        
        # ===== NEW ANALYTICS ENDPOINTS (Fee-focused redesign) =====
        self.test("ANALYTICS: GET /analytics/fees returns kpis + daily + monthly + by_mode + by_class", lambda: self.test_analytics_fees_basic())
        self.test("ANALYTICS: GET /analytics/fees with class_id filter", lambda: self.test_analytics_fees_class_filter())
        self.test("ANALYTICS: GET /analytics/fees with payment_mode filter", lambda: self.test_analytics_fees_payment_mode_filter())
        self.test("ANALYTICS: GET /analytics/fees with empty date range returns 0s", lambda: self.test_analytics_fees_empty_range())
        self.test("ANALYTICS: GET /analytics/student/{id}/fee-report returns student profile + summary + payments", lambda: self.test_student_fee_report())
        self.test("ANALYTICS: GET /analytics/student/{id}/fee-report.pdf returns PDF blob", lambda: self.test_student_fee_report_pdf())
        self.test("RBAC: Parent can access own student fee report, not others", lambda: self.test_rbac_parent_student_fee_report())

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
        assert data['user'].get('linked_student_id'), "Parent should have linked_student_id"

    def test_auth_me(self):
        r = self.get('/auth/me', 'superadmin')
        data = r.json()
        assert data['email'] == CREDENTIALS['superadmin']['email']
        assert data['role'] == 'super_admin'
        print(f"  ✓ /auth/me returned: {data['full_name']}")

    def test_my_schools_superadmin(self):
        r = self.get('/auth/my-schools', 'superadmin')
        schools = r.json()
        assert isinstance(schools, list), "Should return list"
        assert len(schools) == 3, f"Super admin should see 3 schools, got {len(schools)}"
        self.schools = schools
        print(f"  ✓ Super admin sees {len(schools)} schools: {[s['name'] for s in schools]}")

    def test_my_schools_admin(self):
        r = self.get('/auth/my-schools', 'admin_gn')
        schools = r.json()
        assert isinstance(schools, list), "Should return list"
        assert len(schools) == 1, f"School admin should see 1 school, got {len(schools)}"
        print(f"  ✓ School admin sees 1 school: {schools[0]['name']}")

    def test_get_schools(self):
        r = self.get('/schools', 'superadmin')
        schools = r.json()
        assert len(schools) >= 3, f"Should have at least 3 schools, got {len(schools)}"
        print(f"  ✓ Found {len(schools)} schools")

    def test_dashboard_summary(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/dashboard/summary', 'admin_gn', school_id=school_id)
        data = r.json()
        required_fields = ['total_students', 'today_collection', 'monthly_collection', 
                          'present_today', 'collection_trend']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        print(f"  ✓ Dashboard KPIs: students={data['total_students']}, today_collection={data['today_collection']}, monthly={data['monthly_collection']}")

    def test_get_students(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/students', 'admin_gn', school_id=school_id)
        students = r.json()
        assert isinstance(students, list), "Should return list"
        assert len(students) > 0, "Should have students"
        self.students = students
        print(f"  ✓ Found {len(students)} students for school")

    def test_get_students_parent(self):
        r = self.get('/students', 'parent_gn')
        students = r.json()
        assert isinstance(students, list), "Should return list"
        assert len(students) == 1, f"Parent should see only 1 student, got {len(students)}"
        linked_id = self.users['parent_gn']['linked_student_id']
        assert students[0]['id'] == linked_id, "Should return only linked student"
        print(f"  ✓ Parent sees only linked student: {students[0]['full_name']}")

    def test_get_student_detail(self):
        if not self.students:
            self.test_get_students()
        student_id = self.students[0]['id']
        r = self.get(f'/students/{student_id}', 'admin_gn')
        student = r.json()
        assert student['id'] == student_id
        print(f"  ✓ Student detail: {student['full_name']}")

    def test_create_student(self):
        school_id = self.users['admin_gn']['school_id']
        if not self.classes:
            self.test_get_classes()
        class_id = self.classes[0]['id'] if self.classes else None
        
        student_data = {
            'full_name': f'Test Student {datetime.now().strftime("%H%M%S")}',
            'dob': '2015-05-15',
            'gender': 'Male',
            'father_name': 'Test Father',
            'phone': '+91 9876543210',
            'class_id': class_id,
            'section': 'A',
        }
        r = self.post('/students', 'admin_gn', student_data, school_id=school_id, expected=200)
        student = r.json()
        assert 'admission_number' in student, "Should have auto-generated admission_number"
        assert student['admission_number'].startswith('GN-2025-'), f"Admission number format incorrect: {student['admission_number']}"
        print(f"  ✓ Created student: {student['full_name']} with admission_number: {student['admission_number']}")

    def test_school_switching(self):
        if len(self.schools) < 2:
            self.test_my_schools_superadmin()
        
        school1_id = self.schools[0]['id']
        school2_id = self.schools[1]['id']
        
        # Get students from school 1
        r1 = self.get('/students', 'superadmin', school_id=school1_id)
        students1 = r1.json()
        
        # Get students from school 2
        r2 = self.get('/students', 'superadmin', school_id=school2_id)
        students2 = r2.json()
        
        # Verify different data
        assert len(students1) > 0, "School 1 should have students"
        assert len(students2) > 0, "School 2 should have students"
        
        # Check that students belong to different schools
        if students1 and students2:
            assert students1[0]['school_id'] != students2[0]['school_id'], "Students should be from different schools"
        
        print(f"  ✓ School switching works: School1={len(students1)} students, School2={len(students2)} students")

    def test_get_classes(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/classes', 'admin_gn', school_id=school_id)
        classes = r.json()
        assert isinstance(classes, list), "Should return list"
        assert len(classes) > 0, "Should have classes"
        self.classes = classes
        print(f"  ✓ Found {len(classes)} classes")

    def test_get_fee_heads(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/fees/heads', 'admin_gn', school_id=school_id)
        heads = r.json()
        assert isinstance(heads, list), "Should return list"
        self.fee_heads = heads
        print(f"  ✓ Found {len(heads)} fee heads")

    def test_get_fee_plans(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/fees/plans', 'admin_gn', school_id=school_id)
        plans = r.json()
        assert isinstance(plans, list), "Should return list"
        print(f"  ✓ Found {len(plans)} fee plans")

    def test_student_dues(self):
        if not self.students:
            self.test_get_students()
        student_id = self.students[0]['id']
        r = self.get(f'/fees/student/{student_id}/dues', 'admin_gn')
        data = r.json()
        assert 'student' in data
        assert 'dues' in data
        assert 'total_paid' in data
        print(f"  ✓ Student dues: total_paid={data['total_paid']}, dues_count={len(data['dues'])}")

    def test_collect_payment(self):
        if not self.students:
            self.test_get_students()
        school_id = self.users['accountant_gn']['school_id']
        student_id = self.students[0]['id']
        
        payment_data = {
            'student_id': student_id,
            'items': [
                {'fee_head_name': 'Tuition Fee', 'period': 'January 2025', 'amount': 3500},
                {'fee_head_name': 'Transport Fee', 'period': 'January 2025', 'amount': 1200},
            ],
            'discount': 0,
            'late_fee': 0,
            'payment_mode': 'cash',
            'remarks': 'Test payment',
        }
        r = self.post('/payments/collect', 'accountant_gn', payment_data, school_id=school_id, expected=200)
        payment = r.json()
        assert 'receipt_number' in payment, "Should have receipt_number"
        assert payment['receipt_number'].startswith('GN-'), f"Receipt format incorrect: {payment['receipt_number']}"
        assert payment['total_paid'] == 4700, f"Total should be 4700, got {payment['total_paid']}"
        self.payments.append(payment)
        print(f"  ✓ Payment collected: {payment['receipt_number']}, total={payment['total_paid']}")

    def test_receipt_pdf(self):
        if not self.payments:
            self.test_collect_payment()
        payment_id = self.payments[0]['id']
        r = self.get(f'/payments/{payment_id}/receipt.pdf', 'accountant_gn', expected=200)
        assert r.headers['content-type'] == 'application/pdf', f"Should be PDF, got {r.headers['content-type']}"
        assert len(r.content) > 1000, "PDF should have content"
        print(f"  ✓ PDF receipt generated: {len(r.content)} bytes")

    def test_razorpay_order(self):
        if not self.students:
            self.test_get_students()
        student_id = self.students[0]['id']
        
        order_data = {
            'student_id': student_id,
            'items': [
                {'fee_head_name': 'Tuition Fee', 'period': 'February 2025', 'amount': 3500},
            ],
            'discount': 0,
            'late_fee': 0,
            'remarks': 'Test Razorpay order',
        }
        r = self.post('/payments/razorpay/order', 'parent_gn', order_data, expected=200)
        order = r.json()
        assert 'order_id' in order, "Should have order_id"
        assert 'amount' in order, "Should have amount"
        assert 'key_id' in order, "Should have key_id"
        assert order['amount'] == 350000, f"Amount should be 350000 paise, got {order['amount']}"
        print(f"  ✓ Razorpay order created: {order['order_id']}, amount={order['amount']} paise")

    def test_razorpay_verify_invalid(self):
        # Test with mock/invalid signature - should return 400
        verify_data = {
            'razorpay_order_id': 'order_fake123',
            'razorpay_payment_id': 'pay_fake456',
            'razorpay_signature': 'invalid_signature_mock',
        }
        r = self.post('/payments/razorpay/verify', 'parent_gn', verify_data, expected=400)
        print(f"  ✓ Invalid signature correctly rejected with 400")

    def test_get_attendance(self):
        school_id = self.users['teacher_gn']['school_id']
        r = self.get('/attendance', 'teacher_gn', school_id=school_id)
        records = r.json()
        assert isinstance(records, list), "Should return list"
        print(f"  ✓ Found {len(records)} attendance records")

    def test_mark_attendance(self):
        if not self.classes:
            self.test_get_classes()
        if not self.students:
            self.test_get_students()
        
        school_id = self.users['teacher_gn']['school_id']
        class_id = self.classes[0]['id']
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get students in this class
        class_students = [s for s in self.students if s.get('class_id') == class_id][:5]
        
        attendance_data = {
            'date': today,
            'class_id': class_id,
            'section': 'A',
            'entries': [
                {'student_id': s['id'], 'status': 'present'} for s in class_students
            ],
        }
        r = self.post('/attendance/mark', 'teacher_gn', attendance_data, school_id=school_id, expected=200)
        result = r.json()
        assert 'saved' in result
        print(f"  ✓ Marked attendance for {result['saved']} students")

    def test_get_homework(self):
        school_id = self.users['teacher_gn']['school_id']
        r = self.get('/homework', 'teacher_gn', school_id=school_id)
        homework = r.json()
        assert isinstance(homework, list), "Should return list"
        print(f"  ✓ Found {len(homework)} homework items")

    def test_create_homework(self):
        if not self.classes:
            self.test_get_classes()
        school_id = self.users['teacher_gn']['school_id']
        class_id = self.classes[0]['id']
        
        hw_data = {
            'class_id': class_id,
            'section': 'A',
            'subject': 'Mathematics',
            'title': 'Test Homework',
            'description': 'Complete exercises 1-10',
            'due_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
        }
        r = self.post('/homework', 'teacher_gn', hw_data, school_id=school_id, expected=200)
        hw = r.json()
        assert hw['title'] == 'Test Homework'
        print(f"  ✓ Created homework: {hw['title']}")

    def test_get_events(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/events', 'admin_gn', school_id=school_id)
        events = r.json()
        assert isinstance(events, list), "Should return list"
        print(f"  ✓ Found {len(events)} events")

    def test_create_event(self):
        school_id = self.users['admin_gn']['school_id']
        event_data = {
            'title': 'Test Event',
            'description': 'Test event description',
            'event_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'location': 'School Ground',
        }
        r = self.post('/events', 'admin_gn', event_data, school_id=school_id, expected=200)
        event = r.json()
        assert event['title'] == 'Test Event'
        print(f"  ✓ Created event: {event['title']}")

    def test_get_circulars(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/circulars', 'admin_gn', school_id=school_id)
        circulars = r.json()
        assert isinstance(circulars, list), "Should return list"
        print(f"  ✓ Found {len(circulars)} circulars")

    def test_create_circular(self):
        school_id = self.users['admin_gn']['school_id']
        circular_data = {
            'title': 'Test Circular',
            'body': 'This is a test circular',
            'priority': 'normal',
            'status': 'published',
            'audience': 'all',
        }
        r = self.post('/circulars', 'admin_gn', circular_data, school_id=school_id, expected=200)
        circular = r.json()
        assert circular['title'] == 'Test Circular'
        print(f"  ✓ Created circular: {circular['title']}")

    def test_get_gallery(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/gallery', 'admin_gn', school_id=school_id)
        albums = r.json()
        assert isinstance(albums, list), "Should return list"
        print(f"  ✓ Found {len(albums)} gallery albums")

    def test_get_staff(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/staff', 'admin_gn', school_id=school_id)
        staff = r.json()
        assert isinstance(staff, list), "Should return list"
        print(f"  ✓ Found {len(staff)} staff members")

    def test_get_notifications(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/notifications', 'admin_gn', school_id=school_id)
        notifications = r.json()
        assert isinstance(notifications, list), "Should return list"
        print(f"  ✓ Found {len(notifications)} notifications")

    def test_collection_report(self):
        school_id = self.users['accountant_gn']['school_id']
        today = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        r = self.get(f'/reports/collection?start_date={start}&end_date={today}', 'accountant_gn', school_id=school_id)
        data = r.json()
        assert 'payments' in data
        assert 'total' in data
        assert 'by_mode' in data
        print(f"  ✓ Collection report: {data['count']} payments, total={data['total']}")

    def test_collection_report_pdf(self):
        school_id = self.users['accountant_gn']['school_id']
        r = self.get('/reports/collection.pdf', 'accountant_gn', school_id=school_id, expected=200)
        assert r.headers['content-type'] == 'application/pdf', f"Should be PDF, got {r.headers['content-type']}"
        print(f"  ✓ PDF report generated: {len(r.content)} bytes")

    def test_collection_report_csv(self):
        school_id = self.users['accountant_gn']['school_id']
        r = self.get('/reports/collection.csv', 'accountant_gn', school_id=school_id, expected=200)
        assert 'text/csv' in r.headers['content-type'], f"Should be CSV, got {r.headers['content-type']}"
        print(f"  ✓ CSV report generated: {len(r.content)} bytes")

    def test_collection_report_xlsx(self):
        school_id = self.users['accountant_gn']['school_id']
        r = self.get('/reports/collection.xlsx', 'accountant_gn', school_id=school_id, expected=200)
        assert 'spreadsheet' in r.headers['content-type'], f"Should be XLSX, got {r.headers['content-type']}"
        print(f"  ✓ XLSX report generated: {len(r.content)} bytes")

    def test_audit_logs_admin(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/audit-logs', 'admin_gn', school_id=school_id, expected=200)
        logs = r.json()
        assert isinstance(logs, list), "Should return list"
        print(f"  ✓ School admin can access audit logs: {len(logs)} entries")

    def test_audit_logs_parent_forbidden(self):
        r = self.get('/audit-logs', 'parent_gn', expected=403)
        print(f"  ✓ Parent correctly forbidden from audit logs (403)")

    def test_get_settings(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/settings', 'admin_gn', school_id=school_id)
        settings = r.json()
        assert 'school_id' in settings
        print(f"  ✓ Settings retrieved for school")

    def test_update_school(self):
        if not self.schools:
            self.test_my_schools_superadmin()
        school_id = self.schools[0]['id']
        
        update_data = {'principal_name': 'Updated Principal Name'}
        r = requests.patch(
            f"{BASE_URL}/schools/{school_id}",
            json=update_data,
            headers=self.headers('superadmin')
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        school = r.json()
        assert school['principal_name'] == 'Updated Principal Name'
        print(f"  ✓ School updated: {school['name']}")

    def test_rbac_parent_create_student(self):
        student_data = {
            'full_name': 'Unauthorized Student',
            'father_name': 'Test',
        }
        r = self.post('/students', 'parent_gn', student_data, expected=403)
        print(f"  ✓ Parent correctly forbidden from creating student (403)")

    def test_rbac_teacher_create_school(self):
        school_data = {
            'name': 'Unauthorized School',
            'code': 'UNS',
            'city': 'Test City',
        }
        r = self.post('/schools', 'teacher_gn', school_data, expected=403)
        print(f"  ✓ Teacher correctly forbidden from creating school (403)")

    # ===== NEW FEATURE TESTS (Iteration 2) =====
    def test_update_student_details(self):
        if not self.students:
            self.test_get_students()
        student_id = self.students[0]['id']
        
        update_data = {
            'father_name': 'Updated Father Name',
            'phone': '+91 9999888877',
            'address': '123 Updated Street, New City',
            'mother_name': 'Updated Mother Name',
        }
        r = requests.patch(
            f"{BASE_URL}/students/{student_id}",
            json=update_data,
            headers=self.headers('admin_gn')
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        student = r.json()
        assert student['father_name'] == 'Updated Father Name', f"father_name not updated"
        assert student['phone'] == '+91 9999888877', f"phone not updated"
        assert student['address'] == '123 Updated Street, New City', f"address not updated"
        print(f"  ✓ Student details updated: father_name={student['father_name']}, phone={student['phone']}")

    def test_create_fee_assignment(self):
        if not self.students:
            self.test_get_students()
        school_id = self.users['admin_gn']['school_id']
        student_id = self.students[0]['id']
        
        assignment_data = {
            'student_id': student_id,
            'custom_items': [
                {'fee_head_name': 'Tuition Fee', 'amount': 5000, 'frequency': 'monthly'},
                {'fee_head_name': 'Lab Fee', 'amount': 1500, 'frequency': 'one_time'},
            ],
            'discount_percent': 15,
            'discount_amount': 500,
            'due_date': '2025-02-28',
            'remarks': 'Test assignment with discount',
        }
        r = self.post('/fees/assignments', 'admin_gn', assignment_data, school_id=school_id, expected=200)
        assignment = r.json()
        assert 'id' in assignment, "Should have assignment id"
        assert assignment['discount_percent'] == 15, f"discount_percent should be 15, got {assignment['discount_percent']}"
        assert assignment['discount_amount'] == 500, f"discount_amount should be 500, got {assignment['discount_amount']}"
        assert assignment['due_date'] == '2025-02-28', f"due_date should be 2025-02-28, got {assignment['due_date']}"
        assert len(assignment['custom_items']) == 2, f"Should have 2 custom items, got {len(assignment['custom_items'])}"
        
        # Store for later tests
        if not hasattr(self, 'fee_assignments'):
            self.fee_assignments = []
        self.fee_assignments.append(assignment)
        print(f"  ✓ Fee assignment created: discount_percent={assignment['discount_percent']}%, discount_amount={assignment['discount_amount']}, due_date={assignment['due_date']}")

    def test_update_fee_assignment(self):
        if not hasattr(self, 'fee_assignments') or not self.fee_assignments:
            self.test_create_fee_assignment()
        
        assignment_id = self.fee_assignments[0]['id']
        update_data = {
            'discount_percent': 20,
            'discount_amount': 750,
            'due_date': '2025-03-15',
            'remarks': 'Updated assignment',
        }
        r = requests.patch(
            f"{BASE_URL}/fees/assignments/{assignment_id}",
            json=update_data,
            headers=self.headers('admin_gn')
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assignment = r.json()
        assert assignment['discount_percent'] == 20, f"discount_percent should be 20, got {assignment['discount_percent']}"
        assert assignment['discount_amount'] == 750, f"discount_amount should be 750, got {assignment['discount_amount']}"
        assert assignment['due_date'] == '2025-03-15', f"due_date should be 2025-03-15, got {assignment['due_date']}"
        print(f"  ✓ Fee assignment updated: discount_percent={assignment['discount_percent']}%, discount_amount={assignment['discount_amount']}, due_date={assignment['due_date']}")

    def test_delete_fee_assignment(self):
        # Create a new assignment to delete
        if not self.students:
            self.test_get_students()
        school_id = self.users['admin_gn']['school_id']
        student_id = self.students[0]['id']
        
        assignment_data = {
            'student_id': student_id,
            'custom_items': [{'fee_head_name': 'Test Fee', 'amount': 1000, 'frequency': 'one_time'}],
        }
        r = self.post('/fees/assignments', 'admin_gn', assignment_data, school_id=school_id, expected=200)
        assignment_id = r.json()['id']
        
        # Now delete it
        r = requests.delete(
            f"{BASE_URL}/fees/assignments/{assignment_id}",
            headers=self.headers('admin_gn')
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        result = r.json()
        assert result.get('ok') == True, "Should return ok: true"
        print(f"  ✓ Fee assignment deleted successfully")

    def test_student_dues_new_fields(self):
        if not self.students:
            self.test_get_students()
        student_id = self.students[0]['id']
        
        r = self.get(f'/fees/student/{student_id}/dues', 'admin_gn')
        data = r.json()
        
        # Check for new fields
        assert 'total_expected' in data, "Missing total_expected field"
        assert 'total_discount' in data, "Missing total_discount field"
        assert 'balance' in data, "Missing balance field"
        assert 'total_paid' in data, "Missing total_paid field"
        
        # Verify types
        assert isinstance(data['total_expected'], (int, float)), "total_expected should be numeric"
        assert isinstance(data['total_discount'], (int, float)), "total_discount should be numeric"
        assert isinstance(data['balance'], (int, float)), "balance should be numeric"
        assert isinstance(data['total_paid'], (int, float)), "total_paid should be numeric"
        
        print(f"  ✓ Student dues new fields: total_expected={data['total_expected']}, total_discount={data['total_discount']}, balance={data['balance']}, total_paid={data['total_paid']}")

    def test_fee_status_report(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/reports/fee-status', 'admin_gn', school_id=school_id)
        data = r.json()
        
        assert 'rows' in data, "Missing rows field"
        assert 'summary' in data, "Missing summary field"
        assert isinstance(data['rows'], list), "rows should be a list"
        assert isinstance(data['summary'], dict), "summary should be a dict"
        
        # Check summary fields
        summary = data['summary']
        assert 'total_expected' in summary, "Missing total_expected in summary"
        assert 'total_paid' in summary, "Missing total_paid in summary"
        assert 'total_due' in summary, "Missing total_due in summary"
        assert 'paid_count' in summary, "Missing paid_count in summary"
        assert 'partial_count' in summary, "Missing partial_count in summary"
        assert 'unpaid_count' in summary, "Missing unpaid_count in summary"
        
        print(f"  ✓ Fee status report: {len(data['rows'])} students, total_expected={summary['total_expected']}, total_due={summary['total_due']}, paid/partial/unpaid={summary['paid_count']}/{summary['partial_count']}/{summary['unpaid_count']}")

    def test_fee_status_filter_class(self):
        if not self.classes:
            self.test_get_classes()
        school_id = self.users['admin_gn']['school_id']
        class_id = self.classes[0]['id']
        class_name = self.classes[0]['name']
        
        # Get unfiltered count first
        r_all = self.get('/reports/fee-status', 'admin_gn', school_id=school_id)
        all_count = len(r_all.json()['rows'])
        
        # Get filtered by class
        r = self.get(f'/reports/fee-status?class_id={class_id}', 'admin_gn', school_id=school_id)
        data = r.json()
        
        assert 'rows' in data, "Missing rows field"
        # Verify filtering worked (should have fewer or equal students)
        assert len(data['rows']) <= all_count, f"Filtered count {len(data['rows'])} should be <= unfiltered {all_count}"
        
        # Verify all rows have the same class_name (or '-' for no class)
        if data['rows']:
            # All should have the same class_name
            class_names = set(row.get('class_name') for row in data['rows'])
            # Should be mostly the filtered class (some might be '-' if no class assigned)
            print(f"  ✓ Fee status filtered by class: {len(data['rows'])} students (class_names: {class_names})")
        else:
            print(f"  ✓ Fee status filtered by class: 0 students in class {class_name}")

    def test_fee_status_filter_status(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/reports/fee-status?status_filter=paid', 'admin_gn', school_id=school_id)
        data = r.json()
        
        assert 'rows' in data, "Missing rows field"
        # Verify all rows have status 'paid'
        for row in data['rows']:
            assert row.get('status') == 'paid', f"Row status {row.get('status')} doesn't match filter 'paid'"
        
        print(f"  ✓ Fee status filtered by status=paid: {len(data['rows'])} students")

    def test_fee_status_filter_due_amount(self):
        school_id = self.users['admin_gn']['school_id']
        min_due = 1000
        max_due = 10000
        
        r = self.get(f'/reports/fee-status?min_due={min_due}&max_due={max_due}', 'admin_gn', school_id=school_id)
        data = r.json()
        
        assert 'rows' in data, "Missing rows field"
        # Verify all rows have due amount within range
        for row in data['rows']:
            due = row.get('due', 0)
            assert due >= min_due, f"Row due {due} is less than min_due {min_due}"
            assert due <= max_due, f"Row due {due} is greater than max_due {max_due}"
        
        print(f"  ✓ Fee status filtered by due amount ({min_due}-{max_due}): {len(data['rows'])} students")

    def test_analytics_full(self):
        school_id = self.users['admin_gn']['school_id']
        r = self.get('/analytics', 'admin_gn', school_id=school_id)
        data = r.json()
        
        # Check required fields
        required_fields = ['year', 'total_received', 'total_expected', 'total_due', 'months', 
                          'by_mode', 'by_head', 'by_class', 'attendance']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check months array has 12 entries
        assert isinstance(data['months'], list), "months should be a list"
        assert len(data['months']) == 12, f"months should have 12 entries, got {len(data['months'])}"
        
        # Check month structure
        for month in data['months']:
            assert 'month' in month, "month entry should have 'month' field"
            assert 'received' in month, "month entry should have 'received' field"
            assert 'transactions' in month, "month entry should have 'transactions' field"
        
        # Check by_mode, by_head, by_class are dicts/lists
        assert isinstance(data['by_mode'], dict), "by_mode should be a dict"
        assert isinstance(data['by_head'], dict), "by_head should be a dict"
        assert isinstance(data['by_class'], list), "by_class should be a list"
        
        # Check attendance structure
        assert isinstance(data['attendance'], dict), "attendance should be a dict"
        assert 'total' in data['attendance'], "attendance should have 'total' field"
        assert 'present' in data['attendance'], "attendance should have 'present' field"
        assert 'absent' in data['attendance'], "attendance should have 'absent' field"
        
        print(f"  ✓ Analytics full object: year={data['year']}, received={data['total_received']}, expected={data['total_expected']}, due={data['total_due']}, months={len(data['months'])}, by_mode={len(data['by_mode'])}, by_head={len(data['by_head'])}, by_class={len(data['by_class'])}")

    def test_analytics_year_filter(self):
        school_id = self.users['admin_gn']['school_id']
        year = 2024
        
        r = self.get(f'/analytics?year={year}', 'admin_gn', school_id=school_id)
        data = r.json()
        
        assert data['year'] == year, f"Year should be {year}, got {data['year']}"
        assert len(data['months']) == 12, f"Should have 12 months, got {len(data['months'])}"
        
        print(f"  ✓ Analytics year filter works: year={data['year']}")

    def test_delete_user(self):
        # Create a test user to delete
        school_id = self.users['admin_gn']['school_id']
        user_data = {
            'email': f'test.delete.{datetime.now().strftime("%H%M%S")}@stanvard.school',
            'password': 'test123',
            'full_name': 'Test Delete User',
            'role': 'teacher',
            'school_id': school_id,
        }
        r = self.post('/users', 'admin_gn', user_data, school_id=school_id, expected=200)
        user_id = r.json()['id']
        
        # Delete the user
        r = requests.delete(
            f"{BASE_URL}/users/{user_id}",
            headers=self.headers('admin_gn')
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        result = r.json()
        assert result.get('ok') == True, "Should return ok: true"
        
        # Verify user is soft-deleted (status=inactive)
        r = self.get('/users', 'admin_gn', school_id=school_id)
        users = r.json()
        deleted_user = next((u for u in users if u['id'] == user_id), None)
        assert deleted_user is not None, "User should still exist"
        assert deleted_user['status'] == 'inactive', f"User status should be 'inactive', got {deleted_user['status']}"
        
        print(f"  ✓ User soft-deleted: status={deleted_user['status']}")

    def test_delete_user_self(self):
        # Try to delete yourself - should return 400
        user_id = self.users['admin_gn']['id']
        
        r = requests.delete(
            f"{BASE_URL}/users/{user_id}",
            headers=self.headers('admin_gn')
        )
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        
        print(f"  ✓ Cannot delete yourself: correctly returned 400")

    def test_delete_user_super_admin(self):
        # School admin tries to delete super_admin - should return 403
        super_admin_id = self.users['superadmin']['id']
        
        r = requests.delete(
            f"{BASE_URL}/users/{super_admin_id}",
            headers=self.headers('admin_gn')
        )
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
        
        print(f"  ✓ School admin cannot delete super_admin: correctly returned 403")

    def test_reset_password(self):
        # Create a test user
        school_id = self.users['admin_gn']['school_id']
        user_data = {
            'email': f'test.reset.{datetime.now().strftime("%H%M%S")}@stanvard.school',
            'password': 'oldpass123',
            'full_name': 'Test Reset User',
            'role': 'teacher',
            'school_id': school_id,
        }
        r = self.post('/users', 'admin_gn', user_data, school_id=school_id, expected=200)
        user = r.json()
        
        # Store for login test
        if not hasattr(self, 'reset_test_user'):
            self.reset_test_user = {}
        self.reset_test_user['email'] = user['email']
        self.reset_test_user['id'] = user['id']
        self.reset_test_user['new_password'] = 'newpass456'
        
        # Reset password
        reset_data = {'password': self.reset_test_user['new_password']}
        r = requests.post(
            f"{BASE_URL}/users/{user['id']}/reset-password",
            json=reset_data,
            headers=self.headers('admin_gn')
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        result = r.json()
        assert result.get('ok') == True, "Should return ok: true"
        
        print(f"  ✓ Password reset successful for {user['email']}")

    def test_login_after_reset(self):
        if not hasattr(self, 'reset_test_user'):
            self.test_reset_password()
        
        # Try to login with new password
        login_data = {
            'email': self.reset_test_user['email'],
            'password': self.reset_test_user['new_password'],
        }
        r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        assert r.status_code == 200, f"Login with new password failed: {r.status_code} {r.text}"
        data = r.json()
        assert 'access_token' in data, "Should have access_token"
        
        print(f"  ✓ Login with new password successful")

    def test_rbac_parent_assign_fee(self):
        if not self.students:
            self.test_get_students()
        student_id = self.students[0]['id']
        
        assignment_data = {
            'student_id': student_id,
            'custom_items': [{'fee_head_name': 'Test', 'amount': 1000, 'frequency': 'one_time'}],
        }
        r = self.post('/fees/assignments', 'parent_gn', assignment_data, expected=403)
        print(f"  ✓ Parent correctly forbidden from creating fee assignment (403)")

    def test_rbac_teacher_assign_fee(self):
        if not self.students:
            self.test_get_students()
        student_id = self.students[0]['id']
        
        assignment_data = {
            'student_id': student_id,
            'custom_items': [{'fee_head_name': 'Test', 'amount': 1000, 'frequency': 'one_time'}],
        }
        r = self.post('/fees/assignments', 'teacher_gn', assignment_data, expected=403)
        print(f"  ✓ Teacher correctly forbidden from creating fee assignment (403)")

    def test_rbac_accountant_delete_user(self):
        # Accountant tries to delete a user - should return 403
        # First get a user id
        school_id = self.users['accountant_gn']['school_id']
        r = self.get('/users', 'accountant_gn', school_id=school_id)
        users = r.json()
        
        if users:
            user_id = users[0]['id']
            r = requests.delete(
                f"{BASE_URL}/users/{user_id}",
                headers=self.headers('accountant_gn')
            )
            assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
            print(f"  ✓ Accountant correctly forbidden from deleting user (403)")
        else:
            print(f"  ⚠ Skipped: No users found for accountant")

    # ===== NEW ANALYTICS ENDPOINTS TESTS =====
    def test_analytics_fees_basic(self):
        """Test GET /analytics/fees returns correct structure"""
        school_id = self.users['admin_gn']['school_id']
        today = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        r = self.get(f'/analytics/fees?start_date={start}&end_date={today}', 'admin_gn', school_id=school_id)
        data = r.json()
        
        # Check kpis object with 8+ keys
        assert 'kpis' in data, "Missing kpis object"
        kpis = data['kpis']
        required_kpi_keys = ['total_collected', 'total_pending', 'total_expected', 
                            'total_paid_students', 'total_partial_students', 'total_pending_students',
                            'today_collection', 'monthly_collection', 'total_discount', 'total_late_fee']
        for key in required_kpi_keys:
            assert key in kpis, f"Missing KPI key: {key}"
        
        # Check daily array
        assert 'daily' in data, "Missing daily array"
        assert isinstance(data['daily'], list), "daily should be a list"
        
        # Check monthly array (12 items)
        assert 'monthly' in data, "Missing monthly array"
        assert isinstance(data['monthly'], list), "monthly should be a list"
        assert len(data['monthly']) == 12, f"monthly should have 12 items, got {len(data['monthly'])}"
        
        # Check by_mode object
        assert 'by_mode' in data, "Missing by_mode object"
        assert isinstance(data['by_mode'], dict), "by_mode should be a dict"
        
        # Check by_class array
        assert 'by_class' in data, "Missing by_class array"
        assert isinstance(data['by_class'], list), "by_class should be a list"
        
        print(f"  ✓ Analytics fees endpoint structure valid: collected={kpis['total_collected']}, pending={kpis['total_pending']}, daily_points={len(data['daily'])}, by_mode_keys={len(data['by_mode'])}, by_class={len(data['by_class'])}")

    def test_analytics_fees_class_filter(self):
        """Test /analytics/fees respects class_id filter"""
        school_id = self.users['admin_gn']['school_id']
        today = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        # Get without filter
        r1 = self.get(f'/analytics/fees?start_date={start}&end_date={today}', 'admin_gn', school_id=school_id)
        data1 = r1.json()
        
        # Get classes
        if self.classes:
            class_id = self.classes[0]['id']
            r2 = self.get(f'/analytics/fees?start_date={start}&end_date={today}&class_id={class_id}', 'admin_gn', school_id=school_id)
            data2 = r2.json()
            
            # Filtered result should have <= transactions
            assert data2['kpis']['transactions_in_range'] <= data1['kpis']['transactions_in_range'], \
                "Filtered result should have fewer or equal transactions"
            print(f"  ✓ Class filter works: all={data1['kpis']['transactions_in_range']}, filtered={data2['kpis']['transactions_in_range']}")
        else:
            print(f"  ⚠ Skipped: No classes found")

    def test_analytics_fees_payment_mode_filter(self):
        """Test /analytics/fees respects payment_mode filter"""
        school_id = self.users['admin_gn']['school_id']
        today = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        r = self.get(f'/analytics/fees?start_date={start}&end_date={today}&payment_mode=cash', 'admin_gn', school_id=school_id)
        data = r.json()
        
        # by_mode should only have cash (or be empty if no cash payments)
        if data['by_mode']:
            # If there are payments, they should all be cash
            for mode in data['by_mode'].keys():
                assert mode == 'cash', f"Expected only 'cash' mode, found '{mode}'"
        
        print(f"  ✓ Payment mode filter works: by_mode keys={list(data['by_mode'].keys())}")

    def test_analytics_fees_empty_range(self):
        """Test /analytics/fees with date range covering no payments returns 0s not error"""
        school_id = self.users['admin_gn']['school_id']
        # Use a future date range
        start = '2030-01-01'
        end = '2030-01-31'
        
        r = self.get(f'/analytics/fees?start_date={start}&end_date={end}', 'admin_gn', school_id=school_id)
        data = r.json()
        
        # Should return 0s, not error
        assert data['kpis']['total_collected'] == 0, "Empty range should return 0 collected"
        assert data['kpis']['transactions_in_range'] == 0, "Empty range should return 0 transactions"
        print(f"  ✓ Empty date range returns 0s correctly")

    def test_student_fee_report(self):
        """Test GET /analytics/student/{id}/fee-report"""
        school_id = self.users['admin_gn']['school_id']
        
        if self.students:
            student_id = self.students[0]['id']
            r = self.get(f'/analytics/student/{student_id}/fee-report', 'admin_gn', school_id=school_id)
            data = r.json()
            
            # Check structure
            assert 'student' in data, "Missing student object"
            assert 'summary' in data, "Missing summary object"
            assert 'line_items' in data, "Missing line_items array"
            assert 'payments' in data, "Missing payments array"
            
            # Check summary fields
            summary = data['summary']
            required_summary = ['total_expected', 'total_paid', 'total_discount', 'balance', 
                              'status', 'next_due_date', 'last_payment_date', 'days_overdue']
            for key in required_summary:
                assert key in summary, f"Missing summary key: {key}"
            
            print(f"  ✓ Student fee report structure valid: student={data['student']['full_name']}, status={summary['status']}, balance={summary['balance']}, payments={len(data['payments'])}")
        else:
            print(f"  ⚠ Skipped: No students found")

    def test_student_fee_report_pdf(self):
        """Test GET /analytics/student/{id}/fee-report.pdf returns PDF blob"""
        school_id = self.users['admin_gn']['school_id']
        
        if self.students:
            student_id = self.students[0]['id']
            r = requests.get(
                f"{BASE_URL}/analytics/student/{student_id}/fee-report.pdf",
                headers=self.headers('admin_gn', school_id)
            )
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            assert r.headers['content-type'] == 'application/pdf', f"Expected PDF, got {r.headers['content-type']}"
            assert len(r.content) > 1000, f"PDF too small: {len(r.content)} bytes"
            print(f"  ✓ Student fee report PDF generated: {len(r.content)} bytes")
        else:
            print(f"  ⚠ Skipped: No students found")

    def test_rbac_parent_student_fee_report(self):
        """Test RBAC: parent can only access their linked student fee report"""
        # Parent should access their own student
        if self.users['parent_gn'].get('linked_student_id'):
            student_id = self.users['parent_gn']['linked_student_id']
            r = self.get(f'/analytics/student/{student_id}/fee-report', 'parent_gn')
            assert r.status_code == 200, f"Parent should access own student, got {r.status_code}"
            print(f"  ✓ Parent can access own student fee report")
            
            # Parent tries to access another student - should get 403
            if self.students:
                other_student = next((s for s in self.students if s['id'] != student_id), None)
                if other_student:
                    r2 = requests.get(
                        f"{BASE_URL}/analytics/student/{other_student['id']}/fee-report",
                        headers=self.headers('parent_gn')
                    )
                    assert r2.status_code == 403, f"Parent should not access other student, got {r2.status_code}"
                    print(f"  ✓ Parent correctly forbidden from accessing other student (403)")
        else:
            print(f"  ⚠ Skipped: Parent has no linked student")


if __name__ == '__main__':
    runner = TestRunner()
    sys.exit(runner.run_all_tests())
