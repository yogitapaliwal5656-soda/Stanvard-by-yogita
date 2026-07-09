#!/usr/bin/env python3
"""
Regression test for Stanvard School ERP after frontend-only changes
Tests 12 smoke test scenarios as specified in the review request
"""
import requests
import sys
import io

BASE_URL = "https://data-pull-6.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
SUPER_ADMIN = {"email": "superadmin@stanvard.school", "password": "Stanvard@2026"}
ACCOUNTANT = {"email": "accountant@stanvard.school", "password": "Accountant@2026"}
PARENT = {"email": "9079111899", "password": "111899"}

test_results = []
total_tests = 0
passed_tests = 0
failed_tests = 0

def log_test(name, passed, msg=""):
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if passed:
        passed_tests += 1
        status = "✅"
    else:
        failed_tests += 1
        status = "❌"
    result = f"{status} {name}" + (f" - {msg}" if msg else "")
    test_results.append((passed, result))
    print(result)

def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

def main():
    print("="*80)
    print("STANVARD SCHOOL ERP - REGRESSION TEST (Frontend-only changes)")
    print("="*80)
    
    tokens = {}
    school_id = None
    
    # Test 1: POST /api/auth/login — super_admin, accountant, parent → 200 each
    print("\n" + "="*80)
    print("TEST 1: Authentication")
    print("="*80)
    
    for role, creds in [("super_admin", SUPER_ADMIN), ("accountant", ACCOUNTANT), ("parent", PARENT)]:
        try:
            r = requests.post(f"{BASE_URL}/auth/login", json=creds, timeout=10)
            log_test(f"Login {role}", r.status_code == 200, f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                tokens[role] = data.get("access_token")
                log_test(f"Login {role} returns token", bool(tokens[role]))
        except Exception as e:
            log_test(f"Login {role}", False, str(e))
    
    if "super_admin" not in tokens:
        print("❌ Cannot proceed without super_admin token")
        sys.exit(1)
    
    # Test 2: GET /api/auth/me — 200 with correct role
    print("\n" + "="*80)
    print("TEST 2: Auth /me endpoint")
    print("="*80)
    
    for role in ["super_admin", "accountant", "parent"]:
        if role not in tokens:
            continue
        try:
            r = requests.get(f"{BASE_URL}/auth/me", headers=get_headers(tokens[role]), timeout=10)
            log_test(f"/auth/me {role}", r.status_code == 200, f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                log_test(f"/auth/me {role} has role field", "role" in data, 
                        f"Role: {data.get('role', 'missing')}")
        except Exception as e:
            log_test(f"/auth/me {role}", False, str(e))
    
    # Test 3: GET /api/schools — super_admin → returns 3+ schools
    print("\n" + "="*80)
    print("TEST 3: Schools endpoint")
    print("="*80)
    
    try:
        r = requests.get(f"{BASE_URL}/schools", headers=get_headers(tokens["super_admin"]), timeout=10)
        log_test("GET /api/schools", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            schools = r.json()
            log_test("Schools returns 3+ schools", len(schools) >= 3, f"Got {len(schools)} schools")
            if schools:
                school_id = schools[0]['id']
                log_test("School has id field", bool(school_id))
    except Exception as e:
        log_test("GET /api/schools", False, str(e))
    
    if not school_id:
        print("❌ Cannot proceed without school_id")
        sys.exit(1)
    
    # Test 4: GET /api/students?limit=5 — super_admin → returns non-empty list
    print("\n" + "="*80)
    print("TEST 4: Students endpoint")
    print("="*80)
    
    try:
        r = requests.get(f"{BASE_URL}/students?school_id={school_id}&limit=5", 
                        headers=get_headers(tokens["super_admin"]), timeout=10)
        log_test("GET /api/students?limit=5", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            students = r.json()
            log_test("Students returns non-empty list", len(students) > 0, f"Got {len(students)} students")
    except Exception as e:
        log_test("GET /api/students", False, str(e))
    
    # Test 5: GET /api/classes — super_admin → 13 rows for Kanpur
    print("\n" + "="*80)
    print("TEST 5: Classes endpoint")
    print("="*80)
    
    try:
        r = requests.get(f"{BASE_URL}/classes?school_id={school_id}", 
                        headers=get_headers(tokens["super_admin"]), timeout=10)
        log_test("GET /api/classes", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            classes = r.json()
            log_test("Classes returns 13 rows", len(classes) == 13, f"Got {len(classes)} classes")
    except Exception as e:
        log_test("GET /api/classes", False, str(e))
    
    # Test 6: GET /api/fees/plans — 13 rows
    print("\n" + "="*80)
    print("TEST 6: Fee plans endpoint")
    print("="*80)
    
    try:
        r = requests.get(f"{BASE_URL}/fees/plans?school_id={school_id}", 
                        headers=get_headers(tokens["super_admin"]), timeout=10)
        log_test("GET /api/fees/plans", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            plans = r.json()
            log_test("Fee plans returns 13 rows", len(plans) == 13, f"Got {len(plans)} plans")
    except Exception as e:
        log_test("GET /api/fees/plans", False, str(e))
    
    # Test 7: GET /api/fees/heads — ≥1 row
    print("\n" + "="*80)
    print("TEST 7: Fee heads endpoint")
    print("="*80)
    
    try:
        r = requests.get(f"{BASE_URL}/fees/heads?school_id={school_id}", 
                        headers=get_headers(tokens["super_admin"]), timeout=10)
        log_test("GET /api/fees/heads", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            heads = r.json()
            log_test("Fee heads returns ≥1 row", len(heads) >= 1, f"Got {len(heads)} heads")
    except Exception as e:
        log_test("GET /api/fees/heads", False, str(e))
    
    # Test 8: Fee-schedule regression: GET /api/fees/student/{sid}/fee-schedule → 200 with 12-item schedule
    print("\n" + "="*80)
    print("TEST 8: Fee schedule endpoint")
    print("="*80)
    
    try:
        # Get a student first
        r = requests.get(f"{BASE_URL}/students?school_id={school_id}&limit=1", 
                        headers=get_headers(tokens["super_admin"]), timeout=10)
        if r.status_code == 200 and len(r.json()) > 0:
            student_id = r.json()[0]['id']
            
            r2 = requests.get(f"{BASE_URL}/fees/student/{student_id}/fee-schedule?school_id={school_id}",
                            headers=get_headers(tokens["super_admin"]), timeout=10)
            log_test("GET /api/fees/student/{sid}/fee-schedule", r2.status_code == 200, 
                    f"Status: {r2.status_code}")
            
            if r2.status_code == 200:
                data = r2.json()
                log_test("Fee schedule has 'schedule' field", "schedule" in data)
                if "schedule" in data:
                    log_test("Fee schedule has 12 items", len(data["schedule"]) == 12, 
                            f"Got {len(data['schedule'])} items")
        else:
            log_test("Fee schedule endpoint", False, "No students found")
    except Exception as e:
        log_test("GET /api/fees/student/{sid}/fee-schedule", False, str(e))
    
    # Test 9: Fee-status regression with calculation assertions
    print("\n" + "="*80)
    print("TEST 9: Fee status report with calculations")
    print("="*80)
    
    try:
        r = requests.get(f"{BASE_URL}/reports/fee-status?school_id={school_id}", 
                        headers=get_headers(tokens["super_admin"]), timeout=30)
        log_test("GET /api/reports/fee-status", r.status_code == 200, f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            log_test("Fee status has 'rows' field", "rows" in data)
            log_test("Fee status has 'by_class' field", "by_class" in data)
            log_test("Fee status has 'summary' field", "summary" in data)
            
            if "rows" in data and len(data["rows"]) > 0:
                rows = data["rows"]
                
                # Check calculation: expected == gross_expected − discount
                calc_ok = True
                for row in rows[:10]:
                    if abs(row['expected'] - (row['gross_expected'] - row['discount'])) > 0.01:
                        calc_ok = False
                        break
                log_test("Calculation: expected = gross_expected - discount", calc_ok)
                
                # Check calculation: due == max(expected − paid, 0)
                due_ok = True
                for row in rows[:10]:
                    if abs(row['due'] - max(row['expected'] - row['paid'], 0)) > 0.01:
                        due_ok = False
                        break
                log_test("Calculation: due = max(expected - paid, 0)", due_ok)
                
                # Check summary calculations
                if "summary" in data:
                    s = data["summary"]
                    total_paid = sum(r['paid'] for r in rows)
                    total_expected = sum(r['expected'] for r in rows)
                    
                    if total_expected > 0:
                        coll_calc = round((total_paid / total_expected) * 100, 1)
                        log_test("Summary: collection_percent = round(total_paid/total_expected*100, 1)", 
                                abs(s['collection_percent'] - coll_calc) <= 0.1,
                                f"Expected {coll_calc}, got {s['collection_percent']}")
    except Exception as e:
        log_test("GET /api/reports/fee-status", False, str(e))
    
    # Test 10: RBAC regression: parent → /api/reports/fee-status must return 403
    print("\n" + "="*80)
    print("TEST 10: RBAC - Parent access to fee-status")
    print("="*80)
    
    if "parent" in tokens:
        try:
            r = requests.get(f"{BASE_URL}/reports/fee-status?school_id={school_id}",
                            headers=get_headers(tokens["parent"]), timeout=30)
            log_test("Parent access to /api/reports/fee-status returns 403", r.status_code == 403,
                    f"Status: {r.status_code}")
        except Exception as e:
            log_test("Parent RBAC test", False, str(e))
    else:
        log_test("Parent RBAC test", False, "Parent token not available")
    
    # Test 11: Exports smoke: PDF, XLSX, CSV
    print("\n" + "="*80)
    print("TEST 11: Export endpoints")
    print("="*80)
    
    # PDF export
    try:
        r = requests.get(f"{BASE_URL}/reports/fee-status.pdf?school_id={school_id}&quick_view=defaulters",
                        headers=get_headers(tokens["super_admin"]), timeout=30)
        log_test("GET /api/reports/fee-status.pdf", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            log_test("PDF Content-Type is application/pdf", 
                    'application/pdf' in r.headers.get('Content-Type', ''))
    except Exception as e:
        log_test("PDF export", False, str(e))
    
    # XLSX export
    try:
        r = requests.get(f"{BASE_URL}/reports/fee-status.xlsx?school_id={school_id}&quick_view=defaulters",
                        headers=get_headers(tokens["super_admin"]), timeout=30)
        log_test("GET /api/reports/fee-status.xlsx", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            ct = r.headers.get('Content-Type', '')
            log_test("XLSX Content-Type is xlsx", 'openxmlformats' in ct or 'spreadsheetml' in ct)
    except Exception as e:
        log_test("XLSX export", False, str(e))
    
    # CSV export
    try:
        r = requests.get(f"{BASE_URL}/reports/fee-status.csv?school_id={school_id}&quick_view=defaulters",
                        headers=get_headers(tokens["super_admin"]), timeout=30)
        log_test("GET /api/reports/fee-status.csv", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            log_test("CSV Content-Type is text/csv", 'text/csv' in r.headers.get('Content-Type', ''))
    except Exception as e:
        log_test("CSV export", False, str(e))
    
    # Test 12: Fee-head/plan CRUD smoke
    print("\n" + "="*80)
    print("TEST 12: Fee-head/plan CRUD operations")
    print("="*80)
    
    # PATCH fee head
    try:
        r = requests.get(f"{BASE_URL}/fees/heads?school_id={school_id}", 
                        headers=get_headers(tokens["super_admin"]), timeout=10)
        if r.status_code == 200 and len(r.json()) > 0:
            head_id = r.json()[0]['id']
            head_name = r.json()[0]['name']
            
            r2 = requests.patch(f"{BASE_URL}/fees/heads/{head_id}?school_id={school_id}",
                              headers=get_headers(tokens["super_admin"]),
                              json={"name": head_name}, timeout=10)
            log_test("PATCH /api/fees/heads/{id} succeeds", r2.status_code == 200,
                    f"Status: {r2.status_code}")
            
            # Try to delete in-use head (should return 400)
            r3 = requests.delete(f"{BASE_URL}/fees/heads/{head_id}?school_id={school_id}",
                               headers=get_headers(tokens["super_admin"]), timeout=10)
            log_test("DELETE in-use fee head returns 400", r3.status_code == 400,
                    f"Status: {r3.status_code}")
        else:
            log_test("Fee head CRUD", False, "No fee heads found")
    except Exception as e:
        log_test("Fee head CRUD", False, str(e))
    
    # DELETE fee plan
    try:
        r = requests.get(f"{BASE_URL}/fees/plans?school_id={school_id}", 
                        headers=get_headers(tokens["super_admin"]), timeout=10)
        if r.status_code == 200 and len(r.json()) > 0:
            plan_id = r.json()[0]['id']
            
            # Try to delete in-use plan (should return 400)
            r2 = requests.delete(f"{BASE_URL}/fees/plans/{plan_id}?school_id={school_id}",
                               headers=get_headers(tokens["super_admin"]), timeout=10)
            log_test("DELETE in-use fee plan returns 400", r2.status_code == 400,
                    f"Status: {r2.status_code}")
        else:
            log_test("Fee plan CRUD", False, "No fee plans found")
    except Exception as e:
        log_test("Fee plan CRUD", False, str(e))
    
    # Summary
    print("\n" + "="*80)
    print("REGRESSION TEST SUMMARY")
    print("="*80)
    print(f"Total: {total_tests} | Passed: {passed_tests} ✅ | Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print("="*80)
    
    if failed_tests > 0:
        print("\n❌ FAILED TESTS:")
        for passed, result in test_results:
            if not passed:
                print(f"  {result}")
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
