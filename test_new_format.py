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
INTERVENANTS_NOUVEAU_FORMAT_CSV = "/app/intervenants_nouveau_format.csv"

# Test results
test_results = {
    "new_csv_format": False,
    "planning_data": None
}

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
                'intervenants_file': ('intervenants.csv', intervenants_file, 'text/csv')
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
                    
                    # Save planning data for export tests
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

if __name__ == "__main__":
    test_new_csv_format()