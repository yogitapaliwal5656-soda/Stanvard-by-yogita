#!/usr/bin/env python3
"""
Comprehensive test for Super-Admin receipt EDIT / VOID / RESTORE endpoints.
Tests all endpoints, RBAC, business logic, and PDF generation.
"""
import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BASE_URL = "https://71aa4d2f-b0f2-4b07-a7e7-f4ffa1bc65e1.preview.emergentagent.com/api"

# Test credentials
SUPER_ADMIN = {"email": "superadmin@stanvard.school", "password": "Stanvard@2026"}
ACCOUNTANT = {"email": "accountant@stanvard.school", "password": "Accountant@2026"}

# Test results
passed = 0
failed = 0
failures = []

def log_pass(test_name):
    global passed
    passed += 1
    print(f"✓ {test_name}")

def log_fail(test_name, reason):
    global failed, failures
    failed += 1
    failures.append(f"{test_name}: {reason}")
    print(f"✗ {test_name}: {reason}")

def login(credentials):
    """Login and return access token."""
    resp = requests.post(f"{BASE_URL}/auth/login", json=credentials)
    if resp.status_code != 200:
        log_fail(f"Login {credentials['email']}", f"Status {resp.status_code}")
        return None
    data = resp.json()
    return data.get('access_token')

def get_headers(token):
    """Return authorization headers."""
    return {"Authorization": f"Bearer {token}"}

def create_test_payment(token, student_id, amount=1000):
    """Create a test payment and return payment object."""
    payload = {
        "student_id": student_id,
        "items": [
            {
                "fee_head_name": "Tuition",
                "period": "April 2026",
                "amount": amount
            }
        ],
        "discount": 0,
        "late_fee": 0,
        "payment_mode": "cash",
        "txn_ref": f"TEST/{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "remarks": "Test payment for edit/void/restore testing"
    }
    resp = requests.post(f"{BASE_URL}/payments/collect", json=payload, headers=get_headers(token))
    if resp.status_code != 200:
        log_fail("Create test payment", f"Status {resp.status_code}: {resp.text}")
        return None
    return resp.json()

def get_student_fee_schedule(token, student_id):
    """Get student fee schedule."""
    resp = requests.get(f"{BASE_URL}/fees/student/{student_id}/fee-schedule", headers=get_headers(token))
    if resp.status_code != 200:
        return None
    return resp.json()

def get_student_dues(token, student_id):
    """Get student dues."""
    resp = requests.get(f"{BASE_URL}/fees/student/{student_id}/dues", headers=get_headers(token))
    if resp.status_code != 200:
        return None
    return resp.json()

def get_dashboard_summary(token, school_id):
    """Get dashboard summary."""
    resp = requests.get(f"{BASE_URL}/dashboard/summary?school_id={school_id}", headers=get_headers(token))
    if resp.status_code != 200:
        return None
    return resp.json()

def main():
    print("=" * 80)
    print("SUPER-ADMIN RECEIPT EDIT/VOID/RESTORE ENDPOINT TESTING")
    print("=" * 80)
    print()

    # ========== STEP 1: Login ==========
    print("STEP 1: Authentication")
    print("-" * 80)
    
    super_admin_token = login(SUPER_ADMIN)
    if not super_admin_token:
        print("FATAL: Cannot login as super_admin")
        sys.exit(1)
    log_pass("Login as super_admin")
    
    accountant_token = login(ACCOUNTANT)
    if not accountant_token:
        print("FATAL: Cannot login as accountant")
        sys.exit(1)
    log_pass("Login as accountant")
    print()

    # ========== STEP 2: Get test student ==========
    print("STEP 2: Setup - Get test student")
    print("-" * 80)
    
    # First get schools
    resp = requests.get(f"{BASE_URL}/schools", headers=get_headers(super_admin_token))
    if resp.status_code != 200 or not resp.json():
        log_fail("Get schools", f"Status {resp.status_code}")
        sys.exit(1)
    
    school_id = resp.json()[0]['id']
    log_pass(f"Got school: {resp.json()[0]['name']} (ID: {school_id})")
    
    # Now get students for this school
    resp = requests.get(f"{BASE_URL}/students?school_id={school_id}&limit=1", headers=get_headers(super_admin_token))
    if resp.status_code != 200 or not resp.json():
        log_fail("Get test student", f"Status {resp.status_code}")
        sys.exit(1)
    
    test_student = resp.json()[0]
    student_id = test_student['id']
    log_pass(f"Got test student: {test_student.get('full_name')} (ID: {student_id})")
    print()

    # ========== STEP 3: Create test payment ==========
    print("STEP 3: Setup - Create test payment")
    print("-" * 80)
    
    test_payment = create_test_payment(super_admin_token, student_id, amount=1000)
    if not test_payment:
        print("FATAL: Cannot create test payment")
        sys.exit(1)
    
    payment_id = test_payment['id']
    receipt_number = test_payment['receipt_number']
    log_pass(f"Created test payment: {receipt_number} (ID: {payment_id}, Amount: ₹1000)")
    print()

    # ========== STEP 4: Capture baseline metrics ==========
    print("STEP 4: Capture baseline metrics (before any changes)")
    print("-" * 80)
    
    baseline_schedule = get_student_fee_schedule(super_admin_token, student_id)
    baseline_dues = get_student_dues(super_admin_token, student_id)
    baseline_dashboard = get_dashboard_summary(super_admin_token, school_id)
    
    if not baseline_schedule or not baseline_dues or not baseline_dashboard:
        log_fail("Capture baseline metrics", "Failed to fetch baseline data")
        sys.exit(1)
    
    baseline_total_paid = baseline_schedule['total_paid']
    baseline_balance = baseline_dues['balance']
    baseline_today_collection = baseline_dashboard['today_collection']
    baseline_monthly_collection = baseline_dashboard['monthly_collection']
    
    log_pass(f"Baseline total_paid: ₹{baseline_total_paid}")
    log_pass(f"Baseline balance: ₹{baseline_balance}")
    log_pass(f"Baseline today_collection: ₹{baseline_today_collection}")
    log_pass(f"Baseline monthly_collection: ₹{baseline_monthly_collection}")
    print()

    # ========== STEP 5: Test PATCH /api/payments/{payment_id} (EDIT) ==========
    print("STEP 5: Test PATCH /api/payments/{payment_id} (EDIT)")
    print("-" * 80)
    
    # Test 5.1: Edit with valid data (super_admin)
    edit_payload = {
        "items": [
            {
                "fee_head_name": "Tuition",
                "period": "April 2026",
                "amount": 700
            }
        ],
        "discount": 0,
        "late_fee": 0,
        "payment_mode": "upi",
        "txn_ref": "UPI/TEST/1",
        "remarks": "typo fix",
        "reason": "Wrong amount entered"
    }
    
    resp = requests.patch(f"{BASE_URL}/payments/{payment_id}", json=edit_payload, headers=get_headers(super_admin_token))
    if resp.status_code == 200:
        edited_payment = resp.json()
        
        # Verify receipt_number unchanged
        if edited_payment.get('receipt_number') == receipt_number:
            log_pass("Edit: receipt_number preserved")
        else:
            log_fail("Edit: receipt_number preserved", f"Expected {receipt_number}, got {edited_payment.get('receipt_number')}")
        
        # Verify updated fields
        if edited_payment.get('total_paid') == 700:
            log_pass("Edit: total_paid updated to 700")
        else:
            log_fail("Edit: total_paid updated", f"Expected 700, got {edited_payment.get('total_paid')}")
        
        if edited_payment.get('payment_mode') == 'upi':
            log_pass("Edit: payment_mode updated to upi")
        else:
            log_fail("Edit: payment_mode updated", f"Expected upi, got {edited_payment.get('payment_mode')}")
        
        if edited_payment.get('txn_ref') == 'UPI/TEST/1':
            log_pass("Edit: txn_ref updated")
        else:
            log_fail("Edit: txn_ref updated", f"Expected UPI/TEST/1, got {edited_payment.get('txn_ref')}")
        
        # Verify audit fields
        if edited_payment.get('edited_at'):
            log_pass("Edit: edited_at field present")
        else:
            log_fail("Edit: edited_at field present", "Field missing")
        
        if edited_payment.get('edited_by_id'):
            log_pass("Edit: edited_by_id field present")
        else:
            log_fail("Edit: edited_by_id field present", "Field missing")
        
        if edited_payment.get('edited_by_name'):
            log_pass("Edit: edited_by_name field present")
        else:
            log_fail("Edit: edited_by_name field present", "Field missing")
        
        if edited_payment.get('edited_reason') == 'Wrong amount entered':
            log_pass("Edit: edited_reason field correct")
        else:
            log_fail("Edit: edited_reason field", f"Expected 'Wrong amount entered', got {edited_payment.get('edited_reason')}")
        
        # Verify edit_history
        if edited_payment.get('edit_history') and len(edited_payment['edit_history']) == 1:
            log_pass("Edit: edit_history has 1 entry")
            history_entry = edited_payment['edit_history'][0]
            if history_entry.get('total_paid') == 1000:
                log_pass("Edit: edit_history contains previous total_paid (1000)")
            else:
                log_fail("Edit: edit_history previous total_paid", f"Expected 1000, got {history_entry.get('total_paid')}")
        else:
            log_fail("Edit: edit_history", f"Expected 1 entry, got {len(edited_payment.get('edit_history', []))}")
    else:
        log_fail("Edit with valid data (super_admin)", f"Status {resp.status_code}: {resp.text}")
    
    # Test 5.2: Edit without reason field
    edit_no_reason = {
        "items": [{"fee_head_name": "Tuition", "period": "April 2026", "amount": 800}],
        "discount": 0,
        "late_fee": 0
    }
    resp = requests.patch(f"{BASE_URL}/payments/{payment_id}", json=edit_no_reason, headers=get_headers(super_admin_token))
    if resp.status_code in [400, 422]:
        log_pass("Edit without reason → 400/422 error")
    else:
        log_fail("Edit without reason", f"Expected 400/422, got {resp.status_code}")
    
    # Test 5.3: Edit with accountant token (should be forbidden)
    resp = requests.patch(f"{BASE_URL}/payments/{payment_id}", json=edit_payload, headers=get_headers(accountant_token))
    if resp.status_code == 403:
        log_pass("Edit with accountant token → 403 forbidden")
    else:
        log_fail("Edit with accountant token", f"Expected 403, got {resp.status_code}")
    
    print()

    # ========== STEP 6: Verify business logic after EDIT ==========
    print("STEP 6: Verify business logic after EDIT")
    print("-" * 80)
    
    after_edit_schedule = get_student_fee_schedule(super_admin_token, student_id)
    after_edit_dues = get_student_dues(super_admin_token, student_id)
    after_edit_dashboard = get_dashboard_summary(super_admin_token, school_id)
    
    if after_edit_schedule and after_edit_dues and after_edit_dashboard:
        # After edit: total_paid should reflect new amount (700 instead of 1000)
        # So total_paid should be baseline - 1000 + 700 = baseline - 300
        expected_paid_after_edit = baseline_total_paid - 1000 + 700
        actual_paid_after_edit = after_edit_schedule['total_paid']
        
        if abs(actual_paid_after_edit - expected_paid_after_edit) < 0.01:
            log_pass(f"After edit: total_paid reflects new amount (₹{actual_paid_after_edit})")
        else:
            log_fail("After edit: total_paid", f"Expected ₹{expected_paid_after_edit}, got ₹{actual_paid_after_edit}")
        
        # Balance should increase by 300 (since we reduced payment by 300)
        expected_balance_after_edit = baseline_balance + 300
        actual_balance_after_edit = after_edit_dues['balance']
        
        if abs(actual_balance_after_edit - expected_balance_after_edit) < 0.01:
            log_pass(f"After edit: balance increased by ₹300 (now ₹{actual_balance_after_edit})")
        else:
            log_fail("After edit: balance", f"Expected ₹{expected_balance_after_edit}, got ₹{actual_balance_after_edit}")
        
        # Dashboard collection should also reflect the change
        expected_collection_after_edit = baseline_today_collection - 1000 + 700
        actual_collection_after_edit = after_edit_dashboard['today_collection']
        
        if abs(actual_collection_after_edit - expected_collection_after_edit) < 0.01:
            log_pass(f"After edit: today_collection reflects new amount (₹{actual_collection_after_edit})")
        else:
            log_fail("After edit: today_collection", f"Expected ₹{expected_collection_after_edit}, got ₹{actual_collection_after_edit}")
    else:
        log_fail("Fetch metrics after edit", "Failed to fetch data")
    
    print()

    # ========== STEP 7: Test POST /api/payments/{payment_id}/void (VOID) ==========
    print("STEP 7: Test POST /api/payments/{payment_id}/void (VOID)")
    print("-" * 80)
    
    # Test 7.1: Void with valid reason (super_admin)
    void_payload = {"reason": "Duplicate entry"}
    resp = requests.post(f"{BASE_URL}/payments/{payment_id}/void", json=void_payload, headers=get_headers(super_admin_token))
    if resp.status_code == 200:
        voided_payment = resp.json()
        
        # Verify status
        if voided_payment.get('status') == 'voided':
            log_pass("Void: status set to 'voided'")
        else:
            log_fail("Void: status", f"Expected 'voided', got {voided_payment.get('status')}")
        
        # Verify audit fields
        if voided_payment.get('voided_at'):
            log_pass("Void: voided_at field present")
        else:
            log_fail("Void: voided_at field present", "Field missing")
        
        if voided_payment.get('voided_by_id'):
            log_pass("Void: voided_by_id field present")
        else:
            log_fail("Void: voided_by_id field present", "Field missing")
        
        if voided_payment.get('voided_by_name'):
            log_pass("Void: voided_by_name field present")
        else:
            log_fail("Void: voided_by_name field present", "Field missing")
        
        if voided_payment.get('void_reason') == 'Duplicate entry':
            log_pass("Void: void_reason field correct")
        else:
            log_fail("Void: void_reason field", f"Expected 'Duplicate entry', got {voided_payment.get('void_reason')}")
    else:
        log_fail("Void with valid reason (super_admin)", f"Status {resp.status_code}: {resp.text}")
    
    # Test 7.2: Void without reason
    resp = requests.post(f"{BASE_URL}/payments/{payment_id}/void", json={}, headers=get_headers(super_admin_token))
    if resp.status_code in [400, 422]:
        log_pass("Void without reason → 400/422 error")
    else:
        log_fail("Void without reason", f"Expected 400/422, got {resp.status_code}")
    
    # Test 7.3: Void already voided payment
    resp = requests.post(f"{BASE_URL}/payments/{payment_id}/void", json=void_payload, headers=get_headers(super_admin_token))
    if resp.status_code == 400:
        log_pass("Void already voided payment → 400 error")
    else:
        log_fail("Void already voided payment", f"Expected 400, got {resp.status_code}")
    
    # Test 7.4: Void with accountant token (should be forbidden)
    # Create another test payment for this test
    test_payment_2 = create_test_payment(super_admin_token, student_id, amount=500)
    if test_payment_2:
        payment_id_2 = test_payment_2['id']
        resp = requests.post(f"{BASE_URL}/payments/{payment_id_2}/void", json=void_payload, headers=get_headers(accountant_token))
        if resp.status_code == 403:
            log_pass("Void with accountant token → 403 forbidden")
        else:
            log_fail("Void with accountant token", f"Expected 403, got {resp.status_code}")
        
        # Clean up: void this payment too
        requests.post(f"{BASE_URL}/payments/{payment_id_2}/void", json=void_payload, headers=get_headers(super_admin_token))
    
    print()

    # ========== STEP 8: Verify business logic after VOID ==========
    print("STEP 8: Verify business logic after VOID")
    print("-" * 80)
    
    after_void_schedule = get_student_fee_schedule(super_admin_token, student_id)
    after_void_dues = get_student_dues(super_admin_token, student_id)
    after_void_dashboard = get_dashboard_summary(super_admin_token, school_id)
    
    if after_void_schedule and after_void_dues and after_void_dashboard:
        # After void: total_paid should DECREASE by 700 (the voided amount)
        expected_paid_after_void = after_edit_schedule['total_paid'] - 700
        actual_paid_after_void = after_void_schedule['total_paid']
        
        if abs(actual_paid_after_void - expected_paid_after_void) < 0.01:
            log_pass(f"After void: total_paid decreased by ₹700 (now ₹{actual_paid_after_void})")
        else:
            log_fail("After void: total_paid", f"Expected ₹{expected_paid_after_void}, got ₹{actual_paid_after_void}")
        
        # Balance should INCREASE by 700
        expected_balance_after_void = after_edit_dues['balance'] + 700
        actual_balance_after_void = after_void_dues['balance']
        
        if abs(actual_balance_after_void - expected_balance_after_void) < 0.01:
            log_pass(f"After void: balance increased by ₹700 (now ₹{actual_balance_after_void})")
        else:
            log_fail("After void: balance", f"Expected ₹{expected_balance_after_void}, got ₹{actual_balance_after_void}")
        
        # Dashboard collection should DECREASE by 700
        expected_collection_after_void = after_edit_dashboard['today_collection'] - 700
        actual_collection_after_void = after_void_dashboard['today_collection']
        
        if abs(actual_collection_after_void - expected_collection_after_void) < 0.01:
            log_pass(f"After void: today_collection decreased by ₹700 (now ₹{actual_collection_after_void})")
        else:
            log_fail("After void: today_collection", f"Expected ₹{expected_collection_after_void}, got ₹{actual_collection_after_void}")
    else:
        log_fail("Fetch metrics after void", "Failed to fetch data")
    
    print()

    # ========== STEP 9: Test POST /api/payments/{payment_id}/restore (RESTORE) ==========
    print("STEP 9: Test POST /api/payments/{payment_id}/restore (RESTORE)")
    print("-" * 80)
    
    # Test 9.1: Restore voided payment (super_admin)
    resp = requests.post(f"{BASE_URL}/payments/{payment_id}/restore", headers=get_headers(super_admin_token))
    if resp.status_code == 200:
        restored_payment = resp.json()
        
        # Verify status
        if restored_payment.get('status') == 'success':
            log_pass("Restore: status set to 'success'")
        else:
            log_fail("Restore: status", f"Expected 'success', got {restored_payment.get('status')}")
        
        # Verify voided_* fields removed
        if not restored_payment.get('voided_at'):
            log_pass("Restore: voided_at field removed")
        else:
            log_fail("Restore: voided_at field removed", "Field still present")
        
        if not restored_payment.get('voided_by_id'):
            log_pass("Restore: voided_by_id field removed")
        else:
            log_fail("Restore: voided_by_id field removed", "Field still present")
        
        if not restored_payment.get('voided_by_name'):
            log_pass("Restore: voided_by_name field removed")
        else:
            log_fail("Restore: voided_by_name field removed", "Field still present")
        
        if not restored_payment.get('void_reason'):
            log_pass("Restore: void_reason field removed")
        else:
            log_fail("Restore: void_reason field removed", "Field still present")
    else:
        log_fail("Restore voided payment (super_admin)", f"Status {resp.status_code}: {resp.text}")
    
    # Test 9.2: Restore non-voided payment (should fail)
    resp = requests.post(f"{BASE_URL}/payments/{payment_id}/restore", headers=get_headers(super_admin_token))
    if resp.status_code == 400:
        log_pass("Restore non-voided payment → 400 error")
    else:
        log_fail("Restore non-voided payment", f"Expected 400, got {resp.status_code}")
    
    # Test 9.3: Restore with accountant token (should be forbidden)
    # Void the payment again for this test
    requests.post(f"{BASE_URL}/payments/{payment_id}/void", json=void_payload, headers=get_headers(super_admin_token))
    resp = requests.post(f"{BASE_URL}/payments/{payment_id}/restore", headers=get_headers(accountant_token))
    if resp.status_code == 403:
        log_pass("Restore with accountant token → 403 forbidden")
    else:
        log_fail("Restore with accountant token", f"Expected 403, got {resp.status_code}")
    
    # Restore again for next tests
    requests.post(f"{BASE_URL}/payments/{payment_id}/restore", headers=get_headers(super_admin_token))
    
    print()

    # ========== STEP 10: Verify business logic after RESTORE ==========
    print("STEP 10: Verify business logic after RESTORE")
    print("-" * 80)
    
    after_restore_schedule = get_student_fee_schedule(super_admin_token, student_id)
    after_restore_dues = get_student_dues(super_admin_token, student_id)
    after_restore_dashboard = get_dashboard_summary(super_admin_token, school_id)
    
    if after_restore_schedule and after_restore_dues and after_restore_dashboard:
        # After restore: should return to pre-void state (after edit state)
        expected_paid_after_restore = after_edit_schedule['total_paid']
        actual_paid_after_restore = after_restore_schedule['total_paid']
        
        if abs(actual_paid_after_restore - expected_paid_after_restore) < 0.01:
            log_pass(f"After restore: total_paid returned to pre-void value (₹{actual_paid_after_restore})")
        else:
            log_fail("After restore: total_paid", f"Expected ₹{expected_paid_after_restore}, got ₹{actual_paid_after_restore}")
        
        # Balance should return to pre-void state
        expected_balance_after_restore = after_edit_dues['balance']
        actual_balance_after_restore = after_restore_dues['balance']
        
        if abs(actual_balance_after_restore - expected_balance_after_restore) < 0.01:
            log_pass(f"After restore: balance returned to pre-void value (₹{actual_balance_after_restore})")
        else:
            log_fail("After restore: balance", f"Expected ₹{expected_balance_after_restore}, got ₹{actual_balance_after_restore}")
        
        # Dashboard collection should return to pre-void state
        expected_collection_after_restore = after_edit_dashboard['today_collection']
        actual_collection_after_restore = after_restore_dashboard['today_collection']
        
        if abs(actual_collection_after_restore - expected_collection_after_restore) < 0.01:
            log_pass(f"After restore: today_collection returned to pre-void value (₹{actual_collection_after_restore})")
        else:
            log_fail("After restore: today_collection", f"Expected ₹{expected_collection_after_restore}, got ₹{actual_collection_after_restore}")
    else:
        log_fail("Fetch metrics after restore", "Failed to fetch data")
    
    print()

    # ========== STEP 11: Test PDF generation ==========
    print("STEP 11: Test PDF generation")
    print("-" * 80)
    
    # Test 11.1: Void the payment and check PDF
    requests.post(f"{BASE_URL}/payments/{payment_id}/void", json=void_payload, headers=get_headers(super_admin_token))
    
    resp = requests.get(f"{BASE_URL}/payments/{payment_id}/receipt.pdf", headers=get_headers(super_admin_token))
    if resp.status_code == 200:
        if resp.headers.get('content-type') == 'application/pdf':
            log_pass("Voided receipt PDF: returns application/pdf")
        else:
            log_fail("Voided receipt PDF: content-type", f"Expected application/pdf, got {resp.headers.get('content-type')}")
        
        if resp.content[:4] == b'%PDF':
            log_pass("Voided receipt PDF: valid PDF signature")
        else:
            log_fail("Voided receipt PDF: valid PDF", "Invalid PDF signature")
        
        # Check for VOIDED watermark in PDF content
        pdf_content = resp.content.decode('latin-1', errors='ignore')
        if 'VOIDED' in pdf_content:
            log_pass("Voided receipt PDF: contains VOIDED watermark")
        else:
            log_fail("Voided receipt PDF: VOIDED watermark", "Watermark not found in PDF")
    else:
        log_fail("Voided receipt PDF download", f"Status {resp.status_code}")
    
    # Test 11.2: Restore and check PDF for REVISED chip
    requests.post(f"{BASE_URL}/payments/{payment_id}/restore", headers=get_headers(super_admin_token))
    
    resp = requests.get(f"{BASE_URL}/payments/{payment_id}/receipt.pdf", headers=get_headers(super_admin_token))
    if resp.status_code == 200:
        if resp.headers.get('content-type') == 'application/pdf':
            log_pass("Edited receipt PDF: returns application/pdf")
        else:
            log_fail("Edited receipt PDF: content-type", f"Expected application/pdf, got {resp.headers.get('content-type')}")
        
        if resp.content[:4] == b'%PDF':
            log_pass("Edited receipt PDF: valid PDF signature")
        else:
            log_fail("Edited receipt PDF: valid PDF", "Invalid PDF signature")
        
        # Check for REVISED chip in PDF content
        pdf_content = resp.content.decode('latin-1', errors='ignore')
        if 'REVISED' in pdf_content:
            log_pass("Edited receipt PDF: contains REVISED chip")
        else:
            log_fail("Edited receipt PDF: REVISED chip", "REVISED chip not found in PDF")
    else:
        log_fail("Edited receipt PDF download", f"Status {resp.status_code}")
    
    print()

    # ========== STEP 12: Cleanup - Void test payment ==========
    print("STEP 12: Cleanup - Void test payment")
    print("-" * 80)
    
    resp = requests.post(f"{BASE_URL}/payments/{payment_id}/void", json={"reason": "Test cleanup"}, headers=get_headers(super_admin_token))
    if resp.status_code == 200:
        log_pass("Cleanup: Test payment voided successfully")
    else:
        log_fail("Cleanup: Void test payment", f"Status {resp.status_code}")
    
    print()

    # ========== SUMMARY ==========
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed > 0:
        print("FAILURES:")
        for failure in failures:
            print(f"  ✗ {failure}")
        print()
        sys.exit(1)
    else:
        print("✅ ALL TESTS PASSED!")
        sys.exit(0)

if __name__ == "__main__":
    main()
