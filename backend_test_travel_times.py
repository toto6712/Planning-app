import requests
import json
import os
import time
import asyncio
from pathlib import Path

# Configuration
BACKEND_URL = "https://7524bfef-eb18-4e95-8c5b-b17dcfe9ab70.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test files
INTERVENTIONS_CSV = "/app/interventions.csv"
INTERVENANTS_CSV = "/app/intervenants_format_simple.csv"

# Test results
test_results = {
    "travel_time_calculation": False,
    "travel_time_in_planning": False,
    "travel_time_in_fallback": False,
    "planning_data": None
}

def test_travel_time_calculation():
    """Test the travel time calculation via OpenStreetMap"""
    print("\n=== Testing Travel Time Calculation via OpenStreetMap ===")
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
            print("Uploading CSV files to test travel time calculation...")
            response = requests.post(f"{API_BASE_URL}/upload-csv", files=files)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                
                # Save planning data for other tests
                test_results["planning_data"] = result
                
                # Check logs for travel time calculation
                logs = result.get('logs', [])
                travel_time_logs = [log for log in logs if "Calcul des temps de trajet via OpenStreetMap" in log]
                
                if travel_time_logs:
                    print("✅ Found travel time calculation logs:")
                    for log in travel_time_logs:
                        print(f"  - {log}")
                    
                    # Check if we have progress logs for travel time calculation
                    progress_logs = [log for log in logs if "Progression calcul trajets" in log]
                    if progress_logs:
                        print(f"✅ Found {len(progress_logs)} progress logs for travel time calculation")
                    
                    test_results["travel_time_calculation"] = True
                    return True
                else:
                    print("❌ No travel time calculation logs found")
                    return False
            else:
                print(f"❌ Travel time calculation test failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing travel time calculation: {str(e)}")
        return False

def test_travel_time_in_planning():
    """Test if travel times are included in the planning"""
    print("\n=== Testing Travel Times in Planning ===")
    try:
        if not test_results["planning_data"]:
            print("❌ No planning data available for travel time test")
            return False
        
        # Check if the planning includes travel times
        planning_events = test_results["planning_data"].get("planning", [])
        
        if not planning_events:
            print("❌ No planning events found")
            return False
        
        # Check if the AI message includes travel times
        ai_message = test_results["planning_data"].get("ai_message", "")
        
        if "TEMPS DE TRAJET CALCULÉS" in ai_message and "OpenStreetMap" in ai_message:
            print("✅ AI message includes travel times section")
            
            # Try to extract the travel times JSON from the AI message
            try:
                start_idx = ai_message.find("TEMPS DE TRAJET CALCULÉS")
                if start_idx > 0:
                    json_start = ai_message.find("{", start_idx)
                    if json_start > 0:
                        # Find the end of the JSON object (before the next section)
                        next_section = ai_message.find("RÈGLES CRITIQUES", json_start)
                        if next_section > 0:
                            json_end = ai_message.rfind("}", json_start, next_section)
                            if json_end > 0:
                                travel_times_json = ai_message[json_start:json_end+1]
                                try:
                                    travel_times = json.loads(travel_times_json)
                                    print(f"✅ Successfully extracted travel times JSON with {len(travel_times)} addresses")
                                    
                                    # Print a sample of travel times
                                    sample_address = next(iter(travel_times))
                                    sample_destinations = travel_times[sample_address]
                                    print(f"Sample travel times from '{sample_address}':")
                                    for dest, time in list(sample_destinations.items())[:3]:
                                        print(f"  - To '{dest}': {time} minutes")
                                except json.JSONDecodeError:
                                    print("❌ Failed to parse travel times JSON")
            except Exception as e:
                print(f"❌ Error extracting travel times from AI message: {str(e)}")
        
        # Check if planning events have trajet_precedent field with real values
        events_with_travel_time = [event for event in planning_events if event.get("trajet_precedent") and event.get("trajet_precedent") != "0 min"]
        
        if events_with_travel_time:
            print(f"✅ Found {len(events_with_travel_time)}/{len(planning_events)} events with travel times")
            
            # Print some examples
            for i, event in enumerate(events_with_travel_time[:3]):
                print(f"  {i+1}. Client: {event.get('client')}, Travel time: {event.get('trajet_precedent')}")
            
            test_results["travel_time_in_planning"] = True
            return True
        else:
            print("❌ No events with travel times found in planning")
            return False
    except Exception as e:
        print(f"❌ Error testing travel times in planning: {str(e)}")
        return False

def test_travel_time_in_fallback():
    """Test if travel times are included in the fallback planning"""
    print("\n=== Testing Travel Times in Fallback Planning ===")
    try:
        # Create a scenario that will trigger the fallback planning
        # We'll use a malformed interventions file to force the AI to fail
        
        # Create a temporary malformed file
        with open("/app/malformed_interventions.csv", "w") as f:
            f.write("Client,Date,Durée,Adresse,Intervenant\n")
            f.write("Test Client,invalid-date,01:00,1 rue des Lilas Strasbourg,\n")
        
        # Open the files
        with open("/app/malformed_interventions.csv", 'rb') as interventions_file, open(INTERVENANTS_CSV, 'rb') as intervenants_file:
            files = {
                'interventions_file': ('interventions.csv', interventions_file, 'text/csv'),
                'intervenants_file': ('intervenants.csv', intervenants_file, 'text/csv')
            }
            
            # Make the request
            print("Uploading malformed CSV to trigger fallback planning...")
            response = requests.post(f"{API_BASE_URL}/upload-csv", files=files)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                
                # Check if we got a fallback planning
                planning_events = result.get("planning", [])
                
                if not planning_events:
                    print("❌ No fallback planning events found")
                    return False
                
                # Check if fallback planning events have trajet_precedent field with real values
                events_with_travel_time = [event for event in planning_events if event.get("trajet_precedent") and event.get("trajet_precedent") != "0 min"]
                
                if events_with_travel_time:
                    print(f"✅ Found {len(events_with_travel_time)}/{len(planning_events)} fallback events with travel times")
                    
                    # Print some examples
                    for i, event in enumerate(events_with_travel_time[:3]):
                        print(f"  {i+1}. Client: {event.get('client')}, Travel time: {event.get('trajet_precedent')}")
                    
                    test_results["travel_time_in_fallback"] = True
                    return True
                else:
                    print("❌ No events with travel times found in fallback planning")
                    return False
            else:
                print(f"❌ Fallback planning test failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing travel times in fallback planning: {str(e)}")
        return False
    finally:
        # Clean up the temporary file
        if os.path.exists("/app/malformed_interventions.csv"):
            os.remove("/app/malformed_interventions.csv")

def run_all_tests():
    """Run all tests and print summary"""
    print("\n=== Starting OpenStreetMap Travel Time Integration Tests ===")
    
    # Test travel time calculation
    travel_time_calculation_result = test_travel_time_calculation()
    
    # Test travel time in planning
    travel_time_in_planning_result = test_travel_time_in_planning()
    
    # Test travel time in fallback planning
    travel_time_in_fallback_result = test_travel_time_in_fallback()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Travel Time Calculation: {'✅ Passed' if test_results['travel_time_calculation'] else '❌ Failed'}")
    print(f"Travel Time in Planning: {'✅ Passed' if test_results['travel_time_in_planning'] else '❌ Failed'}")
    print(f"Travel Time in Fallback: {'✅ Passed' if test_results['travel_time_in_fallback'] else '❌ Failed'}")
    
    # Overall result
    all_passed = all([
        test_results['travel_time_calculation'],
        test_results['travel_time_in_planning'],
        test_results['travel_time_in_fallback']
    ])
    
    print(f"\nOverall Result: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()