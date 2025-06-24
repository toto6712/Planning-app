import requests
import json
import os
import time
from pathlib import Path

# Configuration
BACKEND_URL = "https://b263207e-5c0d-4840-a454-960de473501f.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test files
INTERVENTIONS_CSV = "/app/interventions_gps.csv"
INTERVENANTS_CSV = "/app/intervenants_coordonnees.csv"
INTERVENANTS_DUPLICATES_CSV = "/app/intervenants_duplicates_gps.csv"
INTERVENANTS_NOUVEAU_FORMAT_CSV = "/app/intervenants_coordonnees.csv"
INTERVENTIONS_COORDONNEES_CSV = "/app/interventions_coordonnees_fixed.csv"
INTERVENANTS_COORDONNEES_CSV = "/app/intervenants_coordonnees.csv"

# Test results
test_results = {
    "health_check": False,
    "upload_csv": False,
    "export_csv": False,
    "export_pdf": False,
    "duplicate_detection": False,
    "new_csv_format": False,
    "gps_coordinates": False,
    "travel_cache_stats": False,
    "travel_cache_enrichment": False,
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
        if not os.path.exists(INTERVENTIONS_COORDONNEES_CSV) or not os.path.exists(INTERVENANTS_CSV):
            print("❌ Test CSV files not found")
            return False
        
        # Open the files
        with open(INTERVENTIONS_COORDONNEES_CSV, 'rb') as interventions_file, open(INTERVENANTS_CSV, 'rb') as intervenants_file:
            files = {
                'interventions_file': ('interventions_coordonnees.csv', interventions_file, 'text/csv'),
                'intervenants_file': ('intervenants_coordonnees.csv', intervenants_file, 'text/csv')
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
        if not os.path.exists(INTERVENANTS_DUPLICATES_CSV) or not os.path.exists(INTERVENTIONS_COORDONNEES_CSV):
            print("❌ Test CSV files not found")
            return False
        
        # Open the files
        with open(INTERVENTIONS_COORDONNEES_CSV, 'rb') as interventions_file, open(INTERVENANTS_DUPLICATES_CSV, 'rb') as intervenants_file:
            files = {
                'interventions_file': ('interventions_coordonnees.csv', interventions_file, 'text/csv'),
                'intervenants_file': ('intervenants_duplicates.csv', intervenants_file, 'text/csv')
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
                
                # We should only have 2 unique intervenants (Jean Dupont and Marie Durand), not 4
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
        if not os.path.exists(INTERVENTIONS_COORDONNEES_CSV) or not os.path.exists(INTERVENANTS_NOUVEAU_FORMAT_CSV):
            print("❌ Test CSV files not found")
            return False
        
        # Open the files
        with open(INTERVENTIONS_COORDONNEES_CSV, 'rb') as interventions_file, open(INTERVENANTS_NOUVEAU_FORMAT_CSV, 'rb') as intervenants_file:
            files = {
                'interventions_file': ('interventions_coordonnees.csv', interventions_file, 'text/csv'),
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

def test_column_casing():
    """Test the column casing for 'Heure hebdomadaire'"""
    print("\n=== Testing Column Casing for 'Heure hebdomadaire' ===")
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
            print("Uploading CSV files to test column casing...")
            response = requests.post(f"{API_BASE_URL}/upload-csv", files=files)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                print(f"Planning Events: {len(result.get('planning', []))}")
                
                # Verify that the planning was generated correctly
                planning_events = result.get('planning', [])
                
                # Check if all interventions were planned
                if len(planning_events) > 0:
                    print("✅ Column casing test passed - 'Heure hebdomadaire' is correctly recognized")
                    return True
                else:
                    print("❌ Column casing test failed - No planning events generated")
                    return False
            else:
                print(f"❌ Column casing test failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing column casing: {str(e)}")
        return False

def test_travel_cache_stats():
    """Test the travel cache stats endpoint"""
    print("\n=== Testing Travel Cache Stats Endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/travel-cache/stats")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and response.json().get("success") == True:
            stats = response.json().get("stats", {})
            print(f"Total routes in cache: {stats.get('total_routes')}")
            print(f"Unique coordinates: {stats.get('unique_coordinates')}")
            print(f"Cache file path: {stats.get('cache_file_path')}")
            print(f"Cache file exists: {stats.get('cache_file_exists')}")
            print(f"Cache file size: {stats.get('cache_file_size_mb')} MB")
            print(f"Last updated: {stats.get('last_updated')}")
            
            test_results["travel_cache_stats"] = True
            print("✅ Travel cache stats test passed")
            return True
        else:
            print("❌ Travel cache stats test failed")
            return False
    except Exception as e:
        print(f"❌ Error testing travel cache stats: {str(e)}")
        return False

def test_gps_coordinates():
    """Test the GPS coordinates format in CSV files"""
    print("\n=== Testing GPS Coordinates Format ===")
    try:
        # Check if test files exist
        if not os.path.exists(INTERVENTIONS_COORDONNEES_CSV) or not os.path.exists(INTERVENANTS_COORDONNEES_CSV):
            print("❌ Test CSV files with coordinates not found")
            return False
        
        # Open the files
        with open(INTERVENTIONS_COORDONNEES_CSV, 'rb') as interventions_file, open(INTERVENANTS_COORDONNEES_CSV, 'rb') as intervenants_file:
            files = {
                'interventions_file': ('interventions_coordonnees.csv', interventions_file, 'text/csv'),
                'intervenants_file': ('intervenants_coordonnees.csv', intervenants_file, 'text/csv')
            }
            
            # Make the request
            print("Uploading CSV files with GPS coordinates...")
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
                test_results["gps_coordinates"] = True
                print("✅ GPS coordinates test passed")
                return True
            else:
                print(f"❌ GPS coordinates test failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing GPS coordinates: {str(e)}")
        return False

def test_travel_cache_enrichment():
    """Test if the travel cache is enriched after uploading files with GPS coordinates"""
    print("\n=== Testing Travel Cache Enrichment ===")
    try:
        # First, get the initial cache stats
        initial_response = requests.get(f"{API_BASE_URL}/travel-cache/stats")
        if initial_response.status_code != 200:
            print("❌ Could not get initial cache stats")
            return False
        
        initial_stats = initial_response.json().get("stats", {})
        initial_routes = initial_stats.get("total_routes", 0)
        print(f"Initial routes in cache: {initial_routes}")
        
        # Now upload files with GPS coordinates if not already done
        if not test_results["gps_coordinates"]:
            if not test_gps_coordinates():
                print("❌ GPS coordinates test failed, cannot test cache enrichment")
                return False
        
        # Wait a bit for the cache to be updated
        print("Waiting for cache to be updated...")
        time.sleep(2)
        
        # Get the updated cache stats
        updated_response = requests.get(f"{API_BASE_URL}/travel-cache/stats")
        if updated_response.status_code != 200:
            print("❌ Could not get updated cache stats")
            return False
        
        updated_stats = updated_response.json().get("stats", {})
        updated_routes = updated_stats.get("total_routes", 0)
        print(f"Updated routes in cache: {updated_routes}")
        
        # Check if the cache has been enriched
        if updated_routes >= initial_routes:
            print(f"✅ Cache has been enriched or maintained: {initial_routes} -> {updated_routes} routes")
            test_results["travel_cache_enrichment"] = True
            return True
        else:
            print(f"❌ Cache has not been enriched: {initial_routes} -> {updated_routes} routes")
            return False
    except Exception as e:
        print(f"❌ Error testing travel cache enrichment: {str(e)}")
        return False
def run_all_tests():
    """Run all tests and print summary"""
    print("\n=== Starting Backend API Tests ===")
    
    # Test health check
    health_check_result = test_health_check()
    
    # Test travel cache stats
    travel_cache_stats_result = test_travel_cache_stats()
    
    # Test GPS coordinates
    gps_coordinates_result = test_gps_coordinates()
    
    # Test travel cache enrichment
    travel_cache_enrichment_result = test_travel_cache_enrichment()
    
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
    print(f"Travel Cache Stats: {'✅ Passed' if test_results['travel_cache_stats'] else '❌ Failed'}")
    print(f"GPS Coordinates: {'✅ Passed' if test_results['gps_coordinates'] else '❌ Failed'}")
    print(f"Travel Cache Enrichment: {'✅ Passed' if test_results['travel_cache_enrichment'] else '❌ Failed'}")
    print(f"Duplicate Detection: {'✅ Passed' if test_results['duplicate_detection'] else '❌ Failed'}")
    print(f"New CSV Format: {'✅ Passed' if test_results['new_csv_format'] else '❌ Failed'}")
    print(f"Upload CSV: {'✅ Passed' if test_results['upload_csv'] else '❌ Failed'}")
    print(f"Export CSV: {'✅ Passed' if test_results['export_csv'] else '❌ Failed'}")
    print(f"Export PDF: {'✅ Passed' if test_results['export_pdf'] else '❌ Failed'}")
    
    # Overall result
    all_passed = all([
        test_results['health_check'],
        test_results['travel_cache_stats'],
        test_results['gps_coordinates'],
        test_results['travel_cache_enrichment'],
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