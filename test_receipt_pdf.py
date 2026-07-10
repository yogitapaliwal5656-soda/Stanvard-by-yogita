#!/usr/bin/env python3
"""
Test script for fee receipt PDF endpoint - GET /api/payments/{payment_id}/receipt.pdf
"""
import requests
import sys
import os

# Use the correct backend URL from frontend/.env
BASE_URL = "https://71aa4d2f-b0f2-4b07-a7e7-f4ffa1bc65e1.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
SUPER_ADMIN = {"email": "superadmin@stanvard.school", "password": "Stanvard@2026"}
ACCOUNTANT = {"email": "accountant@stanvard.school", "password": "Accountant@2026"}

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
    test_results.append(result)
    print(result)

def login(creds):
    """Login and return access token"""
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json=creds, timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token")
        else:
            print(f"Login failed: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_receipt_pdf_existing_payment():
    """Test downloading receipt PDF for an existing payment"""
    print("\n" + "="*80)
    print("TEST 1: Download Receipt PDF for Existing Payment")
    print("="*80)
    
    # Step 1: Login as super_admin
    token = login(SUPER_ADMIN)
    log_test("Login as super_admin", token is not None)
    if not token:
        return False
    
    # Step 2: Get school id
    try:
        r = requests.get(f"{BASE_URL}/schools", headers=get_headers(token), timeout=10)
        log_test("GET /api/schools returns 200", r.status_code == 200, f"Got {r.status_code}")
        if r.status_code != 200:
            return False
        
        schools = r.json()
        log_test("Schools list not empty", len(schools) > 0, f"Found {len(schools)} schools")
        if len(schools) == 0:
            return False
        
        # Pick first Stanvard school
        school_id = schools[0]['id']
        school_name = schools[0].get('name', 'Unknown')
        print(f"   Using school: {school_name} (id: {school_id})")
        
    except Exception as e:
        log_test("Get schools", False, f"Error: {e}")
        return False
    
    # Step 3: Get payments with receipt_number
    try:
        r = requests.get(f"{BASE_URL}/payments?school_id={school_id}", 
                        headers=get_headers(token), timeout=10)
        log_test("GET /api/payments returns 200", r.status_code == 200, f"Got {r.status_code}")
        if r.status_code != 200:
            return False
        
        payments = r.json()
        log_test("Payments list not empty", len(payments) > 0, f"Found {len(payments)} payments")
        if len(payments) == 0:
            print("   No payments found to test receipt download")
            return False
        
        # Find payment with receipt_number
        payment_with_receipt = None
        for p in payments:
            if p.get('receipt_number'):
                payment_with_receipt = p
                break
        
        log_test("Found payment with receipt_number", payment_with_receipt is not None)
        if not payment_with_receipt:
            print("   No payment with receipt_number found")
            return False
        
        payment_id = payment_with_receipt['id']
        receipt_number = payment_with_receipt['receipt_number']
        print(f"   Using payment: {payment_id} (receipt: {receipt_number})")
        
    except Exception as e:
        log_test("Get payments", False, f"Error: {e}")
        return False
    
    # Step 4: Download receipt PDF
    try:
        r = requests.get(f"{BASE_URL}/payments/{payment_id}/receipt.pdf", 
                        headers=get_headers(token), timeout=15)
        
        # Check HTTP 200
        log_test("Receipt PDF returns 200", r.status_code == 200, f"Got {r.status_code}")
        if r.status_code != 200:
            print(f"   Response: {r.text[:200]}")
            return False
        
        # Check Content-Type
        content_type = r.headers.get('Content-Type', '')
        log_test("Content-Type is application/pdf", 
                content_type == 'application/pdf', 
                f"Got '{content_type}'")
        
        # Check Content-Length
        content_length = len(r.content)
        log_test("Content-Length > 2000 bytes", 
                content_length > 2000, 
                f"Got {content_length} bytes")
        
        # Check PDF signature
        pdf_signature = r.content[:5] == b'%PDF-'
        log_test("Body starts with %PDF- signature", 
                pdf_signature, 
                f"First 10 bytes: {r.content[:10]}")
        
        # Save the file
        output_file = f"/tmp/receipt_{receipt_number}.pdf"
        with open(output_file, 'wb') as f:
            f.write(r.content)
        log_test("PDF file saved successfully", True, f"Saved to {output_file}")
        
        # Verify file can be opened
        file_size = os.path.getsize(output_file)
        log_test("Saved file size matches", 
                file_size == content_length, 
                f"File: {file_size} bytes, Response: {content_length} bytes")
        
        print(f"   ✓ Receipt PDF downloaded successfully: {output_file}")
        return True
        
    except Exception as e:
        log_test("Download receipt PDF", False, f"Error: {e}")
        return False

def test_receipt_pdf_new_payment():
    """Test creating a new payment and downloading its receipt"""
    print("\n" + "="*80)
    print("TEST 2: Create New Payment and Download Receipt")
    print("="*80)
    
    # Step 1: Login as super_admin
    token = login(SUPER_ADMIN)
    log_test("Login as super_admin", token is not None)
    if not token:
        return False
    
    # Step 2: Get school id
    try:
        r = requests.get(f"{BASE_URL}/schools", headers=get_headers(token), timeout=10)
        if r.status_code != 200:
            log_test("Get schools", False, f"Got {r.status_code}")
            return False
        schools = r.json()
        school_id = schools[0]['id']
        
    except Exception as e:
        log_test("Get schools", False, f"Error: {e}")
        return False
    
    # Step 3: Get a student
    try:
        r = requests.get(f"{BASE_URL}/students?school_id={school_id}&limit=1", 
                        headers=get_headers(token), timeout=10)
        log_test("GET /api/students returns 200", r.status_code == 200, f"Got {r.status_code}")
        if r.status_code != 200:
            return False
        
        students = r.json()
        log_test("Students list not empty", len(students) > 0)
        if len(students) == 0:
            return False
        
        student = students[0]
        student_id = student['id']
        student_name = student.get('full_name', 'Unknown')
        print(f"   Using student: {student_name} (id: {student_id})")
        
    except Exception as e:
        log_test("Get students", False, f"Error: {e}")
        return False
    
    # Step 4: Create a new payment
    try:
        payment_data = {
            "school_id": school_id,
            "student_id": student_id,
            "payment_mode": "cash",
            "items": [
                {
                    "fee_head_name": "Test Fee",
                    "amount": 500.0,
                    "period": "Test Period"
                }
            ],
            "subtotal": 500.0,
            "discount": 0.0,
            "late_fee": 0.0,
            "total_paid": 500.0,
            "remarks": "Test payment for receipt PDF verification"
        }
        
        r = requests.post(f"{BASE_URL}/payments/collect", 
                         json=payment_data,
                         headers=get_headers(token), 
                         timeout=10)
        
        log_test("POST /api/payments/collect returns 200", 
                r.status_code == 200, 
                f"Got {r.status_code}")
        if r.status_code != 200:
            print(f"   Response: {r.text[:200]}")
            return False
        
        payment = r.json()
        payment_id = payment['id']
        receipt_number = payment.get('receipt_number')
        log_test("New payment has receipt_number", 
                receipt_number is not None, 
                f"Receipt: {receipt_number}")
        print(f"   Created payment: {payment_id} (receipt: {receipt_number})")
        
    except Exception as e:
        log_test("Create payment", False, f"Error: {e}")
        return False
    
    # Step 5: Download receipt PDF for new payment
    try:
        r = requests.get(f"{BASE_URL}/payments/{payment_id}/receipt.pdf", 
                        headers=get_headers(token), timeout=15)
        
        log_test("New payment receipt PDF returns 200", 
                r.status_code == 200, 
                f"Got {r.status_code}")
        if r.status_code != 200:
            print(f"   Response: {r.text[:200]}")
            return False
        
        # Check Content-Type
        content_type = r.headers.get('Content-Type', '')
        log_test("Content-Type is application/pdf", 
                content_type == 'application/pdf', 
                f"Got '{content_type}'")
        
        # Check Content-Length
        content_length = len(r.content)
        log_test("Content-Length > 2000 bytes", 
                content_length > 2000, 
                f"Got {content_length} bytes")
        
        # Check PDF signature
        pdf_signature = r.content[:5] == b'%PDF-'
        log_test("Body starts with %PDF- signature", 
                pdf_signature, 
                f"First 10 bytes: {r.content[:10]}")
        
        # Save the file
        output_file = f"/tmp/receipt_new_{receipt_number}.pdf"
        with open(output_file, 'wb') as f:
            f.write(r.content)
        log_test("PDF file saved successfully", True, f"Saved to {output_file}")
        
        print(f"   ✓ New payment receipt PDF downloaded successfully: {output_file}")
        return True
        
    except Exception as e:
        log_test("Download new payment receipt PDF", False, f"Error: {e}")
        return False

def test_regression_endpoints():
    """Test that existing endpoints still work"""
    print("\n" + "="*80)
    print("TEST 3: Regression - Verify Existing Endpoints Still Work")
    print("="*80)
    
    # Login
    token = login(SUPER_ADMIN)
    log_test("Login as super_admin", token is not None)
    if not token:
        return False
    
    # Get school id
    try:
        r = requests.get(f"{BASE_URL}/schools", headers=get_headers(token), timeout=10)
        if r.status_code != 200:
            return False
        schools = r.json()
        school_id = schools[0]['id']
    except Exception as e:
        return False
    
    # Test 1: GET /api/students
    try:
        r = requests.get(f"{BASE_URL}/students?school_id={school_id}&limit=5", 
                        headers=get_headers(token), timeout=10)
        log_test("GET /api/students?school_id=... works", 
                r.status_code == 200, 
                f"Got {r.status_code}")
        if r.status_code == 200:
            students = r.json()
            print(f"   Found {len(students)} students")
    except Exception as e:
        log_test("GET /api/students", False, f"Error: {e}")
    
    # Get a student for further tests
    try:
        r = requests.get(f"{BASE_URL}/students?school_id={school_id}&limit=1", 
                        headers=get_headers(token), timeout=10)
        if r.status_code == 200:
            students = r.json()
            if len(students) > 0:
                student_id = students[0]['id']
                
                # Test 2: GET /api/fees/student/{sid}/dues
                try:
                    r = requests.get(f"{BASE_URL}/fees/student/{student_id}/dues", 
                                    headers=get_headers(token), timeout=10)
                    log_test("GET /api/fees/student/{sid}/dues works", 
                            r.status_code == 200, 
                            f"Got {r.status_code}")
                except Exception as e:
                    log_test("GET /api/fees/student/{sid}/dues", False, f"Error: {e}")
                
                # Test 3: GET /api/fees/student/{sid}/fee-schedule
                try:
                    r = requests.get(f"{BASE_URL}/fees/student/{student_id}/fee-schedule", 
                                    headers=get_headers(token), timeout=10)
                    log_test("GET /api/fees/student/{sid}/fee-schedule works", 
                            r.status_code == 200, 
                            f"Got {r.status_code}")
                    if r.status_code == 200:
                        schedule = r.json()
                        has_schedule = 'schedule' in schedule and len(schedule['schedule']) == 12
                        log_test("Fee schedule has 12 months", 
                                has_schedule, 
                                f"Found {len(schedule.get('schedule', []))} months")
                except Exception as e:
                    log_test("GET /api/fees/student/{sid}/fee-schedule", False, f"Error: {e}")
    except Exception as e:
        print(f"   Could not get student for regression tests: {e}")
    
    return True

def main():
    print("="*80)
    print("FEE RECEIPT PDF ENDPOINT TESTING")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    print()
    
    # Run all tests
    test_receipt_pdf_existing_payment()
    test_receipt_pdf_new_payment()
    test_regression_endpoints()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print("="*80)
    
    if failed_tests > 0:
        print("\n❌ FAILED TESTS:")
        for result in test_results:
            if "❌" in result:
                print(f"  {result}")
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
