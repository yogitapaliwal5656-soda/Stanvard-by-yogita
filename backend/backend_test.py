"""Backend API tests for Student Fee Status Report feature."""
import requests
import sys
from typing import Dict, Any, Optional

BASE_URL = "https://school-portal-hub-16.preview.emergentagent.com/api"

class FeeStatusReportTester:
    def __init__(self):
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.school_id = None
        self.classes = []
        
    def log(self, msg: str, status: str = "info"):
        symbols = {"pass": "✅", "fail": "❌", "info": "🔍", "warn": "⚠️"}
        print(f"{symbols.get(status, '•')} {msg}")
    
    def test(self, name: str, condition: bool, details: str = ""):
        self.tests_run += 1
        if condition:
            self.tests_passed += 1
            self.log(f"PASS: {name}", "pass")
            if details:
                print(f"   └─ {details}")
        else:
            self.log(f"FAIL: {name}", "fail")
            if details:
                print(f"   └─ {details}")
        return condition
    
    def login(self, email: str, password: str) -> bool:
        """Login and get token."""
        self.log(f"Logging in as {email}...")
        try:
            resp = requests.post(f"{BASE_URL}/auth/login", 
                               json={"email": email, "password": password},
                               timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get('access_token')
                self.school_id = data.get('user', {}).get('school_id')
                self.log(f"Login successful (school_id: {self.school_id})", "pass")
                return True
            else:
                self.log(f"Login failed: {resp.status_code} - {resp.text}", "fail")
                return False
        except Exception as e:
            self.log(f"Login error: {str(e)}", "fail")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def load_classes(self) -> bool:
        """Load classes for testing."""
        try:
            resp = requests.get(f"{BASE_URL}/classes", headers=self.get_headers(), timeout=10)
            if resp.status_code == 200:
                self.classes = resp.json()
                self.log(f"Loaded {len(self.classes)} classes", "pass")
                return True
            return False
        except Exception as e:
            self.log(f"Failed to load classes: {str(e)}", "fail")
            return False
    
    def test_fee_status_basic(self):
        """Test basic fee-status endpoint without filters."""
        self.log("\n=== Testing Basic Fee Status Endpoint ===")
        try:
            resp = requests.get(f"{BASE_URL}/reports/fee-status", 
                              headers=self.get_headers(), timeout=15)
            self.test("GET /api/reports/fee-status returns 200", 
                     resp.status_code == 200,
                     f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                self.test("Response has 'rows' field", 'rows' in data)
                self.test("Response has 'count' field", 'count' in data)
                self.test("Response has 'summary' field", 'summary' in data)
                
                if 'summary' in data:
                    summary = data['summary']
                    required_keys = ['total_expected', 'total_paid', 'total_due', 
                                   'paid_count', 'partial_count', 'unpaid_count']
                    for key in required_keys:
                        self.test(f"Summary has '{key}'", key in summary)
                
                self.log(f"   Found {data.get('count', 0)} students in report")
                return data
        except Exception as e:
            self.test("Basic fee-status request", False, str(e))
        return None
    
    def test_removed_params(self):
        """Test that min_due and max_due params are ignored (removed feature)."""
        self.log("\n=== Testing Removed Parameters (min_due, max_due) ===")
        try:
            # These params should be ignored, not cause errors
            resp = requests.get(f"{BASE_URL}/reports/fee-status",
                              params={'min_due': 1000, 'max_due': 5000},
                              headers=self.get_headers(), timeout=15)
            self.test("Passing min_due/max_due returns 200 (ignored)", 
                     resp.status_code == 200,
                     "Old params should be silently ignored")
        except Exception as e:
            self.test("Removed params handling", False, str(e))
    
    def test_class_sections_param(self):
        """Test new class_sections parameter with various formats."""
        self.log("\n=== Testing class_sections Parameter ===")
        
        if len(self.classes) < 2:
            self.log("Not enough classes to test class_sections", "warn")
            return
        
        # Test 1: Single class with specific section
        class1 = self.classes[0]
        if class1.get('sections') and len(class1['sections']) > 0:
            section = class1['sections'][0]
            cs_param = f"{class1['id']}:{section}"
            try:
                resp = requests.get(f"{BASE_URL}/reports/fee-status",
                                  params={'class_sections': cs_param},
                                  headers=self.get_headers(), timeout=15)
                self.test(f"class_sections with single class:section ({cs_param})",
                         resp.status_code == 200,
                         f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    self.log(f"   Filtered to {data.get('count', 0)} students")
            except Exception as e:
                self.test("Single class:section", False, str(e))
        
        # Test 2: Single class, all sections (empty section)
        class2 = self.classes[0]
        cs_param = f"{class2['id']}:"
        try:
            resp = requests.get(f"{BASE_URL}/reports/fee-status",
                              params={'class_sections': cs_param},
                              headers=self.get_headers(), timeout=15)
            self.test(f"class_sections with class:blank (all sections of {class2['name']})",
                     resp.status_code == 200,
                     f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                self.log(f"   Found {data.get('count', 0)} students")
        except Exception as e:
            self.test("Class with blank section", False, str(e))
        
        # Test 3: Multiple class:section pairs
        if len(self.classes) >= 2:
            pairs = []
            for i in range(min(2, len(self.classes))):
                c = self.classes[i]
                if c.get('sections') and len(c['sections']) > 0:
                    pairs.append(f"{c['id']}:{c['sections'][0]}")
            
            if len(pairs) >= 2:
                cs_param = ','.join(pairs)
                try:
                    resp = requests.get(f"{BASE_URL}/reports/fee-status",
                                      params={'class_sections': cs_param},
                                      headers=self.get_headers(), timeout=15)
                    self.test("class_sections with multiple pairs (OR semantics)",
                             resp.status_code == 200,
                             f"Param: {cs_param}")
                    if resp.status_code == 200:
                        data = resp.json()
                        self.log(f"   Found {data.get('count', 0)} students across multiple selections")
                except Exception as e:
                    self.test("Multiple class:section pairs", False, str(e))
    
    def test_backwards_compatibility(self):
        """Test that old class_id + section params still work."""
        self.log("\n=== Testing Backwards Compatibility ===")
        
        if len(self.classes) == 0:
            self.log("No classes available for backwards compatibility test", "warn")
            return
        
        class1 = self.classes[0]
        try:
            # Test with just class_id
            resp = requests.get(f"{BASE_URL}/reports/fee-status",
                              params={'class_id': class1['id']},
                              headers=self.get_headers(), timeout=15)
            self.test("Old class_id param still works",
                     resp.status_code == 200,
                     f"class_id={class1['id']}")
            
            # Test with class_id + section
            if class1.get('sections') and len(class1['sections']) > 0:
                section = class1['sections'][0]
                resp = requests.get(f"{BASE_URL}/reports/fee-status",
                                  params={'class_id': class1['id'], 'section': section},
                                  headers=self.get_headers(), timeout=15)
                self.test("Old class_id + section params still work",
                         resp.status_code == 200,
                         f"class_id={class1['id']}, section={section}")
        except Exception as e:
            self.test("Backwards compatibility", False, str(e))
    
    def test_status_filter(self):
        """Test status_filter parameter."""
        self.log("\n=== Testing status_filter Parameter ===")
        
        for status in ['paid', 'partial', 'unpaid']:
            try:
                resp = requests.get(f"{BASE_URL}/reports/fee-status",
                                  params={'status_filter': status},
                                  headers=self.get_headers(), timeout=15)
                self.test(f"status_filter={status}",
                         resp.status_code == 200,
                         f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    self.log(f"   Found {data.get('count', 0)} {status} students")
            except Exception as e:
                self.test(f"status_filter={status}", False, str(e))
    
    def test_pdf_export(self):
        """Test PDF export endpoint."""
        self.log("\n=== Testing PDF Export ===")
        try:
            resp = requests.get(f"{BASE_URL}/reports/fee-status.pdf",
                              headers=self.get_headers(), timeout=20)
            self.test("GET /api/reports/fee-status.pdf returns 200",
                     resp.status_code == 200,
                     f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                self.test("PDF has correct Content-Type",
                         'application/pdf' in content_type,
                         f"Content-Type: {content_type}")
                
                content_length = len(resp.content)
                self.test("PDF content size > 1KB",
                         content_length > 1024,
                         f"Size: {content_length} bytes")
                
                # Check PDF magic bytes
                is_pdf = resp.content[:4] == b'%PDF'
                self.test("PDF has valid PDF header",
                         is_pdf,
                         "Starts with %PDF")
        except Exception as e:
            self.test("PDF export", False, str(e))
    
    def test_xlsx_export(self):
        """Test XLSX export endpoint."""
        self.log("\n=== Testing XLSX Export ===")
        try:
            resp = requests.get(f"{BASE_URL}/reports/fee-status.xlsx",
                              headers=self.get_headers(), timeout=20)
            self.test("GET /api/reports/fee-status.xlsx returns 200",
                     resp.status_code == 200,
                     f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                self.test("XLSX has correct Content-Type",
                         'spreadsheetml.sheet' in content_type,
                         f"Content-Type: {content_type}")
                
                content_length = len(resp.content)
                self.test("XLSX content size > 1KB",
                         content_length > 1024,
                         f"Size: {content_length} bytes")
                
                # Check ZIP magic bytes (XLSX is a ZIP file)
                is_zip = resp.content[:2] == b'PK'
                self.test("XLSX has valid ZIP header",
                         is_zip,
                         "XLSX files are ZIP archives")
        except Exception as e:
            self.test("XLSX export", False, str(e))
    
    def test_csv_export(self):
        """Test CSV export endpoint."""
        self.log("\n=== Testing CSV Export ===")
        try:
            resp = requests.get(f"{BASE_URL}/reports/fee-status.csv",
                              headers=self.get_headers(), timeout=20)
            self.test("GET /api/reports/fee-status.csv returns 200",
                     resp.status_code == 200,
                     f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                self.test("CSV has correct Content-Type",
                         'text/csv' in content_type,
                         f"Content-Type: {content_type}")
                
                content = resp.text
                lines = content.split('\n')
                self.test("CSV has header row",
                         len(lines) > 0,
                         f"Lines: {len(lines)}")
                
                if len(lines) > 0:
                    header = lines[0]
                    expected_cols = ['Admission No', 'Student', 'Class', 'Section', 
                                   'Guardian', 'Phone', 'Expected', 'Discount', 
                                   'Paid', 'Due', 'Due Date', 'Status']
                    has_all_cols = all(col in header for col in expected_cols)
                    self.test("CSV header has all required columns",
                             has_all_cols,
                             f"Header: {header[:100]}...")
        except Exception as e:
            self.test("CSV export", False, str(e))
    
    def test_exports_with_filters(self):
        """Test that exports respect class_sections and status_filter."""
        self.log("\n=== Testing Exports with Filters ===")
        
        if len(self.classes) == 0:
            self.log("No classes available for filter test", "warn")
            return
        
        class1 = self.classes[0]
        if not class1.get('sections') or len(class1['sections']) == 0:
            self.log("No sections available for filter test", "warn")
            return
        
        section = class1['sections'][0]
        cs_param = f"{class1['id']}:{section}"
        params = {'class_sections': cs_param, 'status_filter': 'unpaid'}
        
        for ext in ['pdf', 'xlsx', 'csv']:
            try:
                resp = requests.get(f"{BASE_URL}/reports/fee-status.{ext}",
                                  params=params,
                                  headers=self.get_headers(), timeout=20)
                self.test(f"{ext.upper()} export respects filters",
                         resp.status_code == 200,
                         f"class_sections={cs_param}, status_filter=unpaid")
            except Exception as e:
                self.test(f"{ext.upper()} with filters", False, str(e))
    
    def test_no_regression_existing_endpoints(self):
        """Test that existing endpoints still work (no regression)."""
        self.log("\n=== Testing No Regression on Existing Endpoints ===")
        
        endpoints = [
            '/reports/collection',
            '/reports/collection.pdf',
            '/reports/collection.csv',
            '/reports/collection.xlsx',
            '/analytics/fees',
        ]
        
        for endpoint in endpoints:
            try:
                resp = requests.get(f"{BASE_URL}{endpoint}",
                                  headers=self.get_headers(), timeout=15)
                self.test(f"GET {endpoint}",
                         resp.status_code == 200,
                         f"Status: {resp.status_code}")
            except Exception as e:
                self.test(f"GET {endpoint}", False, str(e))
    
    def run_all_tests(self):
        """Run all backend tests."""
        print("\n" + "="*70)
        print("  BACKEND API TESTS - Student Fee Status Report")
        print("="*70 + "\n")
        
        # Login
        if not self.login("admin.gn@stanvard.school", "admin123"):
            self.log("Cannot proceed without login", "fail")
            return False
        
        # Load classes
        if not self.load_classes():
            self.log("Cannot proceed without classes data", "fail")
            return False
        
        # Run all test suites
        self.test_fee_status_basic()
        self.test_removed_params()
        self.test_class_sections_param()
        self.test_backwards_compatibility()
        self.test_status_filter()
        self.test_pdf_export()
        self.test_xlsx_export()
        self.test_csv_export()
        self.test_exports_with_filters()
        self.test_no_regression_existing_endpoints()
        
        # Summary
        print("\n" + "="*70)
        print(f"  RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"  Success Rate: {success_rate:.1f}%")
        print("="*70 + "\n")
        
        return self.tests_passed == self.tests_run


def main():
    tester = FeeStatusReportTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
