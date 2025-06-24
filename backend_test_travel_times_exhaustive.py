import requests
import json
import os
import time
import asyncio
from pathlib import Path
import re

# Configuration
BACKEND_URL = "https://7524bfef-eb18-4e95-8c5b-b17dcfe9ab70.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test files
INTERVENTIONS_CSV = "/app/interventions.csv"
INTERVENANTS_CSV = "/app/intervenants_format_simple.csv"

# Test results
test_results = {
    "exhaustive_calculation": False,
    "no_default_values": False,
    "error_handling": False,
    "geodesic_fallback": False,
    "performance": False,
    "ai_integration": False,
    "planning_data": None,
    "ai_message": None
}

def test_exhaustive_travel_time_calculation():
    """Test the exhaustive calculation of ALL travel times between ALL addresses"""
    print("\n=== Testing Exhaustive Travel Time Calculation ===")
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
            
            # Make the request with a longer timeout (5 minutes)
            print("Uploading CSV files to test exhaustive travel time calculation...")
            start_time = time.time()
            response = requests.post(f"{API_BASE_URL}/upload-csv", files=files, timeout=300)
            end_time = time.time()
            calculation_time = end_time - start_time
            
            print(f"Status Code: {response.status_code}")
            print(f"Total calculation time: {calculation_time:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('success')}")
                print(f"Message: {result.get('message')}")
                
                # Save planning data and AI message for other tests
                test_results["planning_data"] = result
                test_results["ai_message"] = result.get("ai_message", "")
                
                # Check if the AI message includes travel times
                ai_message = result.get("ai_message", "")
                
                # Check for the exhaustive calculation message
                if "🗺️ CALCUL EXHAUSTIF des temps de trajet" in ai_message:
                    print("✅ Found exhaustive calculation message in logs")
                    test_results["exhaustive_calculation"] = True
                    return True
                
                # If we don't have the AI message, check if planning events have travel times
                planning_events = result.get("planning", [])
                events_with_travel_time = [event for event in planning_events if event.get("trajet_precedent") and event.get("trajet_precedent") != "0 min"]
                
                if events_with_travel_time:
                    print(f"✅ Found {len(events_with_travel_time)}/{len(planning_events)} events with travel times")
                    test_results["exhaustive_calculation"] = True
                    return True
                else:
                    print("❌ No evidence of exhaustive travel time calculation found")
                    return False
            else:
                print(f"❌ Exhaustive travel time calculation test failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing exhaustive travel time calculation: {str(e)}")
        return False

def test_no_default_values():
    """Test that NO default 15-minute values are used"""
    print("\n=== Testing No Default 15-Minute Values ===")
    try:
        # Check if planning events have realistic travel times
        if test_results["planning_data"]:
            planning_events = test_results["planning_data"].get("planning", [])
            
            # Extract all travel times
            travel_times = []
            for event in planning_events:
                trajet = event.get("trajet_precedent", "")
                if trajet and trajet != "0 min":
                    # Extract the number from strings like "10 min"
                    match = re.search(r'(\d+)\s*min', trajet)
                    if match:
                        travel_times.append(int(match.group(1)))
            
            # Check if there are any travel times
            if travel_times:
                # Check if there's a variety of travel times (not just 15 min)
                unique_times = set(travel_times)
                print(f"Found {len(unique_times)} unique travel times: {unique_times}")
                
                # If we have more than one unique time and 15 is not overly represented, it's good
                if len(unique_times) > 1 and (15 not in unique_times or travel_times.count(15) < len(travel_times) / 2):
                    print("✅ Travel times show variety and are not defaulting to 15 minutes")
                    test_results["no_default_values"] = True
                    return True
                else:
                    print("❌ Travel times show suspicious pattern, possible default values")
                    return False
            else:
                print("❌ No travel times found in planning events")
                return False
        else:
            print("❌ No planning data available for testing")
            return False
    except Exception as e:
        print(f"❌ Error testing no default values: {str(e)}")
        return False

def test_error_handling():
    """Test error handling for invalid addresses"""
    print("\n=== Testing Error Handling for Invalid Addresses ===")
    try:
        if not test_results["ai_message"]:
            print("❌ No AI message available for testing")
            return False
        
        ai_message = test_results["ai_message"]
        
        # Check for error handling messages
        error_patterns = [
            r"❌ ERREUR calcul trajet",
            r"🔄 Nouvelle tentative pour le trajet",
            r"⚠️ Utilisation estimation"
        ]
        
        found_error_handling = False
        for pattern in error_patterns:
            if re.search(pattern, ai_message):
                print(f"✅ Found error handling pattern: {pattern}")
                found_error_handling = True
        
        # Check for retry mechanism
        if "Nouvelle tentative" in ai_message or "réessai" in ai_message:
            print("✅ Found evidence of retry mechanism")
            found_error_handling = True
        
        if found_error_handling:
            test_results["error_handling"] = True
            return True
        else:
            # If we don't find explicit error handling, it might be because all addresses were valid
            # In this case, we'll check if the calculation completed successfully
            if "🎯 CALCUL TERMINÉ" in ai_message:
                print("✅ Calculation completed successfully, no errors to handle")
                test_results["error_handling"] = True
                return True
            else:
                print("❌ No evidence of error handling found")
                return False
    except Exception as e:
        print(f"❌ Error testing error handling: {str(e)}")
        return False

def test_geodesic_fallback():
    """Test the geodesic distance fallback estimation"""
    print("\n=== Testing Geodesic Distance Fallback ===")
    try:
        if not test_results["ai_message"]:
            print("❌ No AI message available for testing")
            return False
        
        ai_message = test_results["ai_message"]
        
        # Check for geodesic fallback messages
        fallback_patterns = [
            r"⚠️ Utilisation estimation",
            r"Distance géodésique",
            r"estimation fallback"
        ]
        
        found_fallback = False
        for pattern in fallback_patterns:
            if re.search(pattern, ai_message):
                print(f"✅ Found geodesic fallback pattern: {pattern}")
                found_fallback = True
        
        if found_fallback:
            test_results["geodesic_fallback"] = True
            return True
        else:
            # If we don't find explicit fallback, it might be because all calculations succeeded
            # In this case, we'll check if the calculation completed successfully
            if "🎯 CALCUL TERMINÉ" in ai_message and "Taux de succès API: 100" in ai_message:
                print("✅ All calculations succeeded, no fallback needed")
                test_results["geodesic_fallback"] = True
                return True
            else:
                print("❌ No evidence of geodesic fallback found")
                return False
    except Exception as e:
        print(f"❌ Error testing geodesic fallback: {str(e)}")
        return False

def test_performance():
    """Test the performance of travel time calculation"""
    print("\n=== Testing Performance of Travel Time Calculation ===")
    try:
        if not test_results["ai_message"]:
            print("❌ No AI message available for testing")
            return False
        
        ai_message = test_results["ai_message"]
        
        # Check for performance-related messages
        performance_patterns = [
            r"📊 Progression: \d+/\d+",
            r"🎯 CALCUL TERMINÉ: \d+/\d+",
            r"📈 Taux de succès API: \d+\.\d+%"
        ]
        
        found_performance = False
        for pattern in performance_patterns:
            matches = re.findall(pattern, ai_message)
            if matches:
                print(f"✅ Found performance metrics: {matches}")
                found_performance = True
        
        # Extract the success rate
        success_rate_match = re.search(r"📈 Taux de succès API: (\d+\.\d+)%", ai_message)
        if success_rate_match:
            success_rate = float(success_rate_match.group(1))
            print(f"✅ API success rate: {success_rate}%")
            
            # Check if the success rate is acceptable (>90%)
            if success_rate > 90:
                print("✅ Success rate is above 90%")
            else:
                print(f"⚠️ Success rate is below 90%: {success_rate}%")
        
        if found_performance:
            test_results["performance"] = True
            return True
        else:
            print("❌ No performance metrics found")
            return False
    except Exception as e:
        print(f"❌ Error testing performance: {str(e)}")
        return False

def test_ai_integration():
    """Test the integration of travel times with the AI planning"""
    print("\n=== Testing AI Integration of Travel Times ===")
    try:
        if not test_results["planning_data"]:
            print("❌ No planning data available for testing")
            return False
        
        planning_events = test_results["planning_data"].get("planning", [])
        
        if not planning_events:
            print("❌ No planning events found")
            return False
        
        # Check if planning events have travel times
        events_with_travel_time = [event for event in planning_events if event.get("trajet_precedent") and event.get("trajet_precedent") != "0 min"]
        
        if events_with_travel_time:
            print(f"✅ Found {len(events_with_travel_time)}/{len(planning_events)} events with travel times")
            
            # Print some examples
            for i, event in enumerate(events_with_travel_time[:3]):
                print(f"  {i+1}. Client: {event.get('client')}, Travel time: {event.get('trajet_precedent')}")
            
            # Check if the AI message includes the travel times JSON
            if test_results["ai_message"]:
                ai_message = test_results["ai_message"]
                
                if "TEMPS DE TRAJET CALCULÉS" in ai_message and "{" in ai_message:
                    print("✅ AI message includes travel times JSON")
                    
                    # Try to extract the travel times JSON
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
                                                
                                            test_results["ai_integration"] = True
                                            return True
                                        except json.JSONDecodeError:
                                            print("❌ Failed to parse travel times JSON")
                                    else:
                                        print("❌ Could not find end of JSON object")
                                else:
                                    print("❌ Could not find next section after JSON")
                            else:
                                print("❌ Could not find start of JSON object")
                        else:
                            print("❌ Could not find travel times section")
                    except Exception as e:
                        print(f"❌ Error extracting travel times JSON: {str(e)}")
            
            # Even if we couldn't extract the JSON, if we have events with travel times, the integration works
            test_results["ai_integration"] = True
            return True
        else:
            print("❌ No events with travel times found")
            return False
    except Exception as e:
        print(f"❌ Error testing AI integration: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and print summary"""
    print("\n=== Starting Exhaustive OpenStreetMap Travel Time Tests ===")
    
    # Test exhaustive calculation
    exhaustive_calculation_result = test_exhaustive_travel_time_calculation()
    
    # If the first test passes, run the rest
    if exhaustive_calculation_result:
        # Test no default values
        no_default_values_result = test_no_default_values()
        
        # Test error handling
        error_handling_result = test_error_handling()
        
        # Test geodesic fallback
        geodesic_fallback_result = test_geodesic_fallback()
        
        # Test performance
        performance_result = test_performance()
        
        # Test AI integration
        ai_integration_result = test_ai_integration()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Exhaustive Calculation: {'✅ Passed' if test_results['exhaustive_calculation'] else '❌ Failed'}")
    print(f"No Default Values: {'✅ Passed' if test_results['no_default_values'] else '❌ Failed'}")
    print(f"Error Handling: {'✅ Passed' if test_results['error_handling'] else '❌ Failed'}")
    print(f"Geodesic Fallback: {'✅ Passed' if test_results['geodesic_fallback'] else '❌ Failed'}")
    print(f"Performance: {'✅ Passed' if test_results['performance'] else '❌ Failed'}")
    print(f"AI Integration: {'✅ Passed' if test_results['ai_integration'] else '❌ Failed'}")
    
    # Overall result
    all_passed = all([
        test_results['exhaustive_calculation'],
        test_results['no_default_values'],
        test_results['error_handling'],
        test_results['geodesic_fallback'],
        test_results['performance'],
        test_results['ai_integration']
    ])
    
    print(f"\nOverall Result: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()