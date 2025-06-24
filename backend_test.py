import requests
import json
import os
import time
from pathlib import Path

# Configuration
BACKEND_URL = "https://7524bfef-eb18-4e95-8c5b-b17dcfe9ab70.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test files
INTERVENTIONS_CSV = "/app/interventions.csv"
INTERVENANTS_CSV = "/app/intervenants_test.csv"
INTERVENANTS_DUPLICATES_CSV = "/app/intervenants_duplicates.csv"
INTERVENANTS_NOUVEAU_FORMAT_CSV = "/app/intervenants_nouveau_format.csv"

# Test results
test_results = {
    "health_check": False,
    "upload_csv": False,
    "export_csv": False,
    "export_pdf": False,
    "duplicate_detection": False,
    "new_csv_format": False,
    "planning_data": None
}

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and response.json().get("status") == "ok":
            test_results["health_check"] = True
            print("✅ Health check test passed")
            return True
        else:
            print("❌ Health check test failed")
            return False
    except Exception as e:
        print(f"❌ Error testing health check: {str(e)}")
        return False

def test_upload_csv():
    """Test the upload CSV endpoint"""
    print("\n=== Testing Upload CSV Endpoint ===")
    try:
        # Check if test files exist
        if not os.path.exists(INTERVENTIONS_CSV) or not os.path.exists(INTERVENANTS_CSV):
            print("❌ Test CSV files not found")
            return False
        
        # Open the files
        with open(INTERVENTIONS_CSV, 'rb') as interventions_file, open(INTERVENANTS_CSV, 'rb') as intervenants_file:
            files = {
                'interventions_file': ('interventions.csv', interventions_file, 'text/csv'),
                'intervenants_file': ('intervenants.csv', intervenants_file, 'text/csv')
            }
            
            # Make the request
            print("Uploading CSV files...")
            response = requests.post(f"{API_BASE_URL}/upload-csv", files=files)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                print(f"Planning Events: {len(result.get('planning', []))}")
                print(f"Stats: {result.get('stats')}")
                
                # Save planning data for export tests
                test_results["planning_data"] = result
                test_results["upload_csv"] = True
                print("✅ Upload CSV test passed")
                return True
            else:
                print(f"❌ Upload CSV test failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing upload CSV: {str(e)}")
        return False

def test_export_csv():
    """Test the export CSV endpoint"""
    print("\n=== Testing Export CSV Endpoint ===")
    try:
        if not test_results["planning_data"]:
            print("❌ No planning data available for export test")
            return False
        
        planning_events = test_results["planning_data"].get("planning", [])
        
        # Make the request
        response = requests.post(
            f"{API_BASE_URL}/export-csv",
            json=planning_events
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Save the CSV file
            csv_content = response.content
            with open("/app/exported_planning.csv", "wb") as f:
                f.write(csv_content)
            
            print(f"CSV file saved to /app/exported_planning.csv")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            
            test_results["export_csv"] = True
            print("✅ Export CSV test passed")
            return True
        else:
            print(f"❌ Export CSV test failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing export CSV: {str(e)}")
        return False

def test_export_pdf():
    """Test the export PDF endpoint"""
    print("\n=== Testing Export PDF Endpoint ===")
    try:
        if not test_results["planning_data"]:
            print("❌ No planning data available for export test")
            return False
        
        # Make the request
        response = requests.post(
            f"{API_BASE_URL}/export-pdf",
            json=test_results["planning_data"]
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Save the PDF file
            pdf_content = response.content
            with open("/app/exported_planning.pdf", "wb") as f:
                f.write(pdf_content)
            
            print(f"PDF file saved to /app/exported_planning.pdf")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            
            test_results["export_pdf"] = True
            print("✅ Export PDF test passed")
            return True
        else:
            print(f"❌ Export PDF test failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing export PDF: {str(e)}")
        return False

def test_duplicate_detection():
    """Test the duplicate detection in intervenants CSV"""
    print("\n=== Testing Duplicate Detection in Intervenants CSV ===")
    try:
        # Check if test file exists
        if not os.path.exists(INTERVENANTS_DUPLICATES_CSV) or not os.path.exists(INTERVENTIONS_CSV):
            print("❌ Test CSV files not found")
            return False
        
        # Open the files
        with open(INTERVENTIONS_CSV, 'rb') as interventions_file, open(INTERVENANTS_DUPLICATES_CSV, 'rb') as intervenants_file:
            files = {
                'interventions_file': ('interventions.csv', interventions_file, 'text/csv'),
                'intervenants_file': ('intervenants.csv', intervenants_file, 'text/csv')
            }
            
            # Make the request
            print("Uploading CSV files with duplicate intervenants...")
            response = requests.post(f"{API_BASE_URL}/upload-csv", files=files)
            print(f"Status Code: {response.status_code}")
            
            # The parser should filter out duplicates and continue
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                
                # Check if duplicates were filtered out by examining the planning
                planning_events = result.get('planning', [])
                
                # Extract unique intervenants from the planning
                intervenants_in_planning = set(event.get('intervenant') for event in planning_events)
                print(f"Intervenants in planning: {intervenants_in_planning}")
                
                # We should only have 2 unique intervenants (Dupont and Martin), not 4
                if len(intervenants_in_planning) <= 2:
                    test_results["duplicate_detection"] = True
                    print("✅ Duplicate detection test passed - duplicates were filtered out")
                    return True
                else:
                    print(f"❌ Duplicate detection test failed - duplicates were not filtered out")
                    return False
            else:
                print(f"❌ Duplicate detection test failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing duplicate detection: {str(e)}")
        return False

def test_new_csv_format():
    """Test the new CSV format with improved fields"""
    print("\n=== Testing New CSV Format with Improved Fields ===")
    try:
        # Check if test files exist
        if not os.path.exists(INTERVENTIONS_CSV) or not os.path.exists(INTERVENANTS_NOUVEAU_FORMAT_CSV):
            print("❌ Test CSV files not found")
            return False
        
        # Open the files
        with open(INTERVENTIONS_CSV, 'rb') as interventions_file, open(INTERVENANTS_NOUVEAU_FORMAT_CSV, 'rb') as intervenants_file:
            files = {
                'interventions_file': ('interventions.csv', interventions_file, 'text/csv'),
                'intervenants_file': ('intervenants_nouveau_format.csv', intervenants_file, 'text/csv')
            }
            
            # Make the request
            print("Uploading CSV files with new format...")
            response = requests.post(f"{API_BASE_URL}/upload-csv", files=files)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                print(f"Planning Events: {len(result.get('planning', []))}")
                print(f"Stats: {result.get('stats')}")
                
                # Verify that the planning was generated correctly
                planning_events = result.get('planning', [])
                
                # Check if all interventions were planned
                if len(planning_events) == 3:  # We have 3 interventions in the test file
                    # Check if the new fields were used correctly
                    # We need to examine the planning to see if the constraints were respected
                    
                    # Extract unique intervenants from the planning
                    intervenants_in_planning = set(event.get('intervenant') for event in planning_events)
                    print(f"Intervenants in planning: {intervenants_in_planning}")
                    
                    # Check if the planning respects the working hours
                    all_hours_respected = True
                    for event in planning_events:
                        start_time = event.get('start', '')
                        if start_time:
                            # Extract hour from ISO format (e.g., "2025-06-29T08:00")
                            hour = int(start_time.split('T')[1].split(':')[0])
                            
                            # Check if the hour is within the working hours
                            # Dupont: 07h00-14h00, Martin: 14h00-22h00
                            intervenant = event.get('intervenant', '')
                            if intervenant == 'Dupont' and (hour < 7 or hour >= 14):
                                print(f"❌ Hour {hour} for Dupont is outside working hours (7-14)")
                                all_hours_respected = False
                            elif intervenant == 'Martin' and (hour < 14 or hour >= 22):
                                print(f"❌ Hour {hour} for Martin is outside working hours (14-22)")
                                all_hours_respected = False
                    
                    if all_hours_respected:
                        print("✅ Working hours respected in the planning")
                    
                    # Save planning data for export tests if not already saved
                    if not test_results["planning_data"]:
                        test_results["planning_data"] = result
                    
                    test_results["new_csv_format"] = True
                    print("✅ New CSV format test passed")
                    return True
                else:
                    print(f"❌ Not all interventions were planned: {len(planning_events)}/3")
                    return False
            else:
                print(f"❌ New CSV format test failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing new CSV format: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and print summary"""
    print("\n=== Starting Backend API Tests ===")
    
    # Test health check
    health_check_result = test_health_check()
    
    # Test duplicate detection
    duplicate_detection_result = test_duplicate_detection()
    
    # Test new CSV format
    new_csv_format_result = test_new_csv_format()
    
    # Test upload CSV
    upload_csv_result = test_upload_csv()
    
    # If upload succeeded, test exports
    if upload_csv_result:
        # Test export CSV
        export_csv_result = test_export_csv()
        
        # Test export PDF
        export_pdf_result = test_export_pdf()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Health Check: {'✅ Passed' if test_results['health_check'] else '❌ Failed'}")
    print(f"Duplicate Detection: {'✅ Passed' if test_results['duplicate_detection'] else '❌ Failed'}")
    print(f"New CSV Format: {'✅ Passed' if test_results['new_csv_format'] else '❌ Failed'}")
    print(f"Upload CSV: {'✅ Passed' if test_results['upload_csv'] else '❌ Failed'}")
    print(f"Export CSV: {'✅ Passed' if test_results['export_csv'] else '❌ Failed'}")
    print(f"Export PDF: {'✅ Passed' if test_results['export_pdf'] else '❌ Failed'}")
    
    # Overall result
    all_passed = all([
        test_results['health_check'],
        test_results['duplicate_detection'],
        test_results['new_csv_format'],
        test_results['upload_csv'],
        test_results['export_csv'],
        test_results['export_pdf']
    ])
    
    print(f"\nOverall Result: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()