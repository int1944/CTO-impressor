import requests
import json
from typing import List, Tuple, Dict, Set
from collections import defaultdict
import time
import re

# API Configuration
API_URL = "http://10.106.104.140:8001/suggest"

# Define valid slots for each LOB
LOB_VALID_SLOTS = {
    "flight": {"from", "to", "date", "passengers", "class", "time", "return"},
    "hotel": {"city", "checkin", "checkout", "nights", "guests", "rooms", "category"},
    "train": {"from", "to", "date", "class", "passengers", "quota", "berth"},
    "holiday": {"to", "date", "nights", "passengers", "theme", "budget"},
    None: {"intent"}  # When no intent is determined
}

# Mapping of slot names to their detection patterns
SLOT_DETECTION_PATTERNS = {
    "from": r"\b(from|leaving|departing|origin)\s+([A-Z][a-z]+)",
    "to": r"\b(to|going|arriving|destination)\s+([A-Z][a-z]+)",
    "city": r"\b(in|at)\s+([A-Z][a-z]+)",
    "date": r"\b(on|tomorrow|next|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d+th|\d+st|\d+nd|\d+rd|january|february|march|april|may|june|july|august|september|october|november|december)",
    "passengers": r"\b(\d+\s+(passenger|people|person|traveler|guest)|for\s+\d+|family\s+of\s+\d+|me\s+and\s+my)",
    "nights": r"\b(\d+\s+(night|day)|for\s+\d+\s+(night|day)|week)",
    "guests": r"\b(\d+\s+(guest|people)|for\s+\d+\s+guest)",
    "class": r"\b(business|economy|first|premium|3AC|2AC|1AC|sleeper|AC|non-AC)",
    "time": r"\b(morning|afternoon|evening|night)",
    "rooms": r"\b(room|suite|deluxe|single|double)",
    "category": r"\b(\d-star|budget|luxury)",
    "checkin": r"\b(check.?in|arriving|for\s+tomorrow|from\s+\d+|on\s+\w+)",
}


def extract_present_slots(query: str) -> Set[str]:
    """
    Extract which slots are already present in the query.
    
    Args:
        query: User query text
        
    Returns:
        Set of slot names that are present in the query
    """
    present = set()
    query_lower = query.lower()
    
    for slot, pattern in SLOT_DETECTION_PATTERNS.items():
        if re.search(pattern, query_lower, re.IGNORECASE):
            present.add(slot)
    
    # Special handling: if city is present, it counts as "to" for holidays
    if "city" in present:
        present.add("to")
    
    return present


def is_slot_valid(actual_slot: str, query: str, intent: str) -> Tuple[bool, str]:
    """
    Check if the suggested slot is valid:
    1. It should be in scope for the LOB
    2. It should not already be present in the query
    
    Args:
        actual_slot: The slot suggested by the system
        query: The user query
        intent: The detected intent/LOB
        
    Returns:
        Tuple of (is_valid, reason)
    """
    if actual_slot is None or actual_slot == "None":
        return False, "Slot is None"
    
    # Special case: "intent" is always valid if no intent is determined
    if actual_slot == "intent":
        return True, "Intent slot is always valid when no LOB determined"
    
    # Get valid slots for this LOB
    valid_slots = LOB_VALID_SLOTS.get(intent, set())
    
    # Check if slot is in scope for the LOB
    if actual_slot not in valid_slots:
        return False, f"Slot '{actual_slot}' not valid for LOB '{intent}' (valid: {valid_slots})"
    
    # Check if slot is already present in query
    present_slots = extract_present_slots(query)
    
    if actual_slot in present_slots:
        return False, f"Slot '{actual_slot}' already present in query"
    
    return True, "Valid and not present"


# Test Queries: (query, expected_next_slot, expected_classification)
test_queries = [
    # ============ FLIGHTS ============
    
    ## Complete Intent - Early Stage
    ("Book a flight", "from", "rule_based"),
    ("I want to book a flight", "from", "rule_based"),
    ("Need a flight", "from", "rule_based"),
    ("I need to book a flight", "from", "rule_based"),
    ("Looking for a flight", "from", "rule_based"),
    ("Book me a flight", "from", "rule_based"),
    ("I want a flight", "from", "rule_based"),
    ("Find me a flight", "from", "rule_based"),
    ("Search for a flight", "from", "rule_based"),
    ("Get me a flight ticket", "from", "rule_based"),
    
    ## Partial Intent (before specifying flight/hotel/etc)
    ("I want to book a", "intent", "rule_based"),
    ("Book a", "intent", "rule_based"),
    ("I need to book", "intent", "rule_based"),
    ("Looking for a", "intent", "rule_based"),
    ("I want a", "intent", "rule_based"),
    
    ## Flight - Source provided
    ("Book a flight from Mumbai", "to", "rule_based"),
    ("Flight from Delhi", "to", "rule_based"),
    ("I want to book a flight from Bengaluru", "to", "rule_based"),
    ("Need a flight from Chennai", "to", "rule_based"),
    ("Book flight from Kolkata", "to", "rule_based"),
    ("From Hyderabad I need a flight", "to", "rule_based"),
    ("I'm flying from Mumbai", "to", "rule_based"),
    
    ## Flight - Source & Destination
    ("Book a flight from Mumbai to Delhi", "date", "rule_based"),
    ("Flight from Bengaluru to Chennai", "date", "rule_based"),
    ("I want to fly from Delhi to Mumbai", "date", "rule_based"),
    ("Need a flight Mumbai to Hyderabad", "date", "rule_based"),
    ("Book me a flight from Kolkata to Bengaluru", "date", "rule_based"),
    ("Delhi to Mumbai flight", "date", "rule_based"),
    ("Bengaluru to Delhi", "intent", "rule_based"),
    
    ## Flight - With Date
    ("Book a flight from Mumbai to Delhi tomorrow", "passengers", "rule_based"),
    ("Flight from Delhi to Bengaluru on 15th January", "passengers", "rule_based"),
    ("I want to fly from Chennai to Mumbai on Monday", "passengers", "rule_based"),
    ("Need a flight from Kolkata to Delhi next Friday", "passengers", "rule_based"),
    ("Book flight Mumbai to Hyderabad on 20th December", "passengers", "rule_based"),
    ("Flight to Delhi tomorrow", "from", "rule_based"),
    ("Flight on 25th December", "from", "llm_fallback"),
    
    ## Flight - With Passengers
    ("Book a flight from Mumbai to Delhi for 2 passengers", "date", "rule_based"),
    ("Flight for 3 people from Bengaluru to Chennai", "date", "rule_based"),
    ("I need 4 tickets from Delhi to Mumbai", "date", "rule_based"),
    ("Book flight for family of 5 from Hyderabad to Kolkata", "date", "llm_fallback"),
    ("Flight from Mumbai to Delhi for me and my wife", "date", "llm_fallback"),
    
    ## Flight - With Class
    ("Book a business class flight from Mumbai to Delhi", "date", "rule_based"),
    ("Economy flight from Bengaluru to Chennai", "date", "rule_based"),
    ("I want first class tickets from Delhi to Mumbai", "date", "rule_based"),
    ("Premium economy flight from Chennai to Kolkata", "date", "llm_fallback"),
    
    ## Flight - With Time
    ("Book a morning flight from Mumbai to Delhi", "date", "rule_based"),
    ("Evening flight from Bengaluru to Chennai", "date", "rule_based"),
    ("I need an afternoon flight from Delhi to Mumbai", "date", "rule_based"),
    ("Night flight from Hyderabad to Bengaluru", "date", "llm_fallback"),
    
    ## Flight - Complex/Varied Order
    ("Tomorrow I need a flight from Mumbai to Delhi", "passengers", "rule_based"),
    ("For 2 passengers book a flight from Bengaluru to Chennai", "date", "rule_based"),
    ("Business class flight tomorrow from Delhi to Mumbai", "passengers", "rule_based"),
    ("I want to travel to Delhi from Mumbai next Monday", "passengers", "llm_fallback"),
    ("Can you book me a return flight to Hyderabad from Mumbai?", "date", "llm_fallback"),
    
    # ============ HOTELS ============
    
    ## Complete Intent - Early Stage
    ("Book a hotel", "city", "rule_based"),
    ("I want to book a hotel", "city", "rule_based"),
    ("Need a hotel", "city", "rule_based"),
    ("Looking for a hotel", "city", "rule_based"),
    ("Find me a hotel", "city", "rule_based"),
    ("I need accommodation", "city", "llm_fallback"),
    ("Book me a room", "city", "llm_fallback"),
    ("I want to stay somewhere", "city", "llm_fallback"),
    ("Need a place to stay", "city", "llm_fallback"),
    ("Book hotel room", "city", "rule_based"),
    
    ## Hotel - Location provided
    ("Book a hotel in Mumbai", "checkin", "rule_based"),
    ("Hotel in Delhi", "checkin", "rule_based"),
    ("I want a hotel in Bengaluru", "checkin", "rule_based"),
    ("Need a hotel in Hyderabad", "checkin", "rule_based"),
    ("Looking for hotels in Chennai", "checkin", "rule_based"),
    ("Find me a hotel in Kolkata", "checkin", "rule_based"),
    ("I want to stay in Mumbai", "checkin", "llm_fallback"),
    ("Need accommodation in Delhi", "checkin", "llm_fallback"),
    
    ## Hotel - Location & Check-in
    ("Book a hotel in Mumbai for tomorrow", "nights", "rule_based"),
    ("Hotel in Delhi from 15th January", "nights", "rule_based"),
    ("I want a hotel in Bengaluru on Monday", "nights", "rule_based"),
    ("Need a hotel in Hyderabad checking in on 20th December", "nights", "rule_based"),
    ("Hotel in Chennai arriving tomorrow", "nights", "llm_fallback"),
    
    ## Hotel - Location & Duration
    ("Book a hotel in Mumbai for 3 nights", "checkin", "rule_based"),
    ("Hotel in Delhi for 2 days", "checkin", "rule_based"),
    ("I need a hotel in Bengaluru for a week", "checkin", "llm_fallback"),
    ("Stay in Kolkata for 5 nights", "checkin", "llm_fallback"),
    
    ## Hotel - Location & Guests
    ("Book a hotel in Mumbai for 2 guests", "checkin", "rule_based"),
    ("Hotel in Delhi for 3 people", "checkin", "rule_based"),
    ("I need a room in Bengaluru for 4 guests", "checkin", "rule_based"),
    ("Hotel for a family of 5 in Hyderabad", "checkin", "llm_fallback"),
    ("Room for me and my partner in Chennai", "checkin", "llm_fallback"),
    
    ## Hotel - With Room Type
    ("Book a deluxe room in Mumbai", "checkin", "rule_based"),
    ("Suite in Delhi", "checkin", "rule_based"),
    ("I want a double room in Bengaluru", "checkin", "rule_based"),
    ("Single room in Chennai", "checkin", "rule_based"),
    
    ## Hotel - With Category
    ("Book a 5-star hotel in Mumbai", "checkin", "rule_based"),
    ("3 star hotel in Delhi", "checkin", "rule_based"),
    ("I need a budget hotel in Bengaluru", "checkin", "rule_based"),
    ("Luxury hotel in Hyderabad", "checkin", "rule_based"),
    
    ## Hotel - Complex/Varied Order
    ("Tomorrow I need a hotel in Mumbai for 2 nights", "guests", "rule_based"),
    ("For 3 guests book a hotel in Delhi from 20th Jan", "nights", "rule_based"),
    ("I want to stay in Kolkata from tomorrow for a week", "guests", "llm_fallback"),
    ("5-star hotel in Mumbai for 2 nights starting tomorrow", "guests", "rule_based"),
    
    # ============ TRAINS ============
    
    ## Complete Intent - Early Stage
    ("Book a train", "from", "rule_based"),
    ("I want to book a train", "from", "rule_based"),
    ("Need a train ticket", "from", "rule_based"),
    ("Looking for a train", "from", "rule_based"),
    ("Find me a train", "from", "rule_based"),
    ("Book train ticket", "from", "rule_based"),
    ("I need a train", "from", "rule_based"),
    ("Search for trains", "from", "rule_based"),
    
    ## Train - Source provided
    ("Book a train from Mumbai", "to", "rule_based"),
    ("Train from Delhi", "to", "rule_based"),
    ("I want a train from Bengaluru", "to", "rule_based"),
    ("Need train from Chennai", "to", "rule_based"),
    ("Train ticket from Kolkata", "to", "rule_based"),
    
    ## Train - Source & Destination
    ("Book a train from Mumbai to Delhi", "date", "rule_based"),
    ("Train from Bengaluru to Chennai", "date", "rule_based"),
    ("I want to travel by train from Delhi to Mumbai", "date", "rule_based"),
    ("Need a train Mumbai to Hyderabad", "date", "rule_based"),
    ("Train from Kolkata to Delhi", "date", "rule_based"),
    
    ## Train - With Date
    ("Book a train from Mumbai to Delhi tomorrow", "class", "rule_based"),
    ("Train from Bengaluru to Chennai on 15th January", "class", "rule_based"),
    ("I need a train from Delhi to Mumbai next Monday", "class", "rule_based"),
    ("Train from Hyderabad to Bengaluru on Friday", "class", "rule_based"),
    
    ## Train - With Class
    ("Book AC train from Mumbai to Delhi", "date", "rule_based"),
    ("Sleeper class train from Bengaluru to Chennai", "date", "rule_based"),
    ("I want 3AC tickets from Delhi to Mumbai", "date", "rule_based"),
    ("First AC train from Chennai to Kolkata", "date", "rule_based"),
    ("Non-AC train from Hyderabad to Mumbai", "date", "rule_based"),
    
    ## Train - With Time
    ("Book morning train from Mumbai to Delhi", "date", "rule_based"),
    ("Evening train from Bengaluru to Chennai", "date", "rule_based"),
    ("Afternoon train from Delhi to Mumbai", "date", "llm_fallback"),
    ("Night train from Kolkata to Delhi", "date", "llm_fallback"),
    
    ## Train - Complex/Varied Order
    ("Tomorrow I need a train from Mumbai to Delhi", "class", "rule_based"),
    ("AC train tomorrow from Bengaluru to Chennai", "passengers", "rule_based"),
    ("I want to travel to Delhi from Mumbai by train next week", "class", "llm_fallback"),
    ("Book me sleeper class tickets for tomorrow from Hyderabad to Mumbai", "passengers", "rule_based"),
    
    # ============ HOLIDAYS ============
    
    ## Complete Intent - Early Stage
    ("Book a holiday package", "to", "rule_based"),
    ("I want a holiday package", "to", "rule_based"),
    ("Need a holiday", "to", "rule_based"),
    ("Looking for a vacation package", "to", "llm_fallback"),
    ("Plan a holiday for me", "to", "llm_fallback"),
    ("I want to go on vacation", "to", "llm_fallback"),
    ("Book holiday", "to", "rule_based"),
    ("Need a vacation package", "to", "llm_fallback"),
    
    ## Holiday - Destination provided
    ("Book a holiday package to Hyderabad", "date", "rule_based"),
    ("Holiday to Mumbai", "date", "rule_based"),
    ("I want a vacation to Kolkata", "date", "llm_fallback"),
    ("Need a holiday package to Chennai", "date", "rule_based"),
    ("Plan a trip to Bengaluru", "date", "llm_fallback"),
    
    ## Holiday - Destination & Date
    ("Book a holiday to Hyderabad starting tomorrow", "nights", "rule_based"),
    ("Holiday to Mumbai from 15th January", "nights", "rule_based"),
    ("I want to go to Kolkata next month", "nights", "llm_fallback"),
    ("Vacation to Chennai starting 20th December", "nights", "llm_fallback"),
    
    ## Holiday - Destination & Duration
    ("Book a 5-day holiday to Hyderabad", "date", "rule_based"),
    ("7 nights holiday package to Mumbai", "date", "rule_based"),
    ("I need a week-long vacation to Kolkata", "date", "llm_fallback"),
    ("10-day holiday to Chennai", "date", "rule_based"),
    
    ## Holiday - Destination & Travelers
    ("Book a holiday to Hyderabad for 2 travelers", "date", "rule_based"),
    ("Holiday package to Mumbai for 4 people", "date", "rule_based"),
    ("Vacation to Kolkata for family of 5", "date", "llm_fallback"),
    ("Holiday for me and my wife to Chennai", "date", "llm_fallback"),
    
    ## Holiday - Complex/Varied Order
    ("I want to go to Hyderabad next weekend with my family", "nights", "llm_fallback"),
    ("Book a 7-night holiday to Mumbai starting tomorrow", "passengers", "rule_based"),
    ("For 4 travelers book a holiday package to Kolkata", "date", "rule_based"),
    ("Next month I want to take my family to Chennai for 10 days", "passengers", "llm_fallback"),
    
    # ============ EDGE CASES & AMBIGUOUS ============
    
    ## City-first (no intent)
    ("Mumbai", "to", "rule_based"),
    ("Delhi to Mumbai", "intent", "rule_based"),
    ("From Mumbai to Delhi", "intent", "rule_based"),
    ("Mumbai to Bengaluru tomorrow", "intent", "rule_based"),
    
    ## Very incomplete
    ("I want", "intent", "llm_fallback"),
    ("Book", "intent", "rule_based"),
    ("Tomorrow", "intent", "llm_fallback"),
    ("For 2 people", "intent", "llm_fallback"),
    
    ## Natural language variations
    ("I'm planning a trip to Mumbai next week", "intent", "llm_fallback"),
    ("Can you help me find a place to stay in Delhi?", "checkin", "llm_fallback"),
    ("What are the flight options to Bengaluru?", "from", "llm_fallback"),
    ("I need to reach Chennai by tomorrow evening", "from", "llm_fallback"),
]


def test_query(query: str, expected_slot: str, expected_source: str) -> Dict:
    """
    Test a single query against the API with flexible validation.
    
    Returns:
        Dict with test results including pass/fail status
    """
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "cursor_position": len(query)},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        actual_slot = data.get("next_slot")
        actual_source = data.get("source")
        actual_intent = data.get("intent")
        latency = data.get("latency_ms", 0)
        
        # NEW: Flexible validation
        is_valid, validation_reason = is_slot_valid(actual_slot, query, actual_intent)
        
        # Check if slot matches expected (for reporting)
        slot_match = actual_slot == expected_slot
        
        # Check if source matches (rule_based vs llm_fallback)
        source_match = actual_source == expected_source
        
        return {
            "query": query,
            "expected_slot": expected_slot,
            "actual_slot": actual_slot,
            "expected_source": expected_source,
            "actual_source": actual_source,
            "intent": actual_intent,
            "latency_ms": latency,
            "slot_match": slot_match,
            "source_match": source_match,
            "is_valid": is_valid,
            "validation_reason": validation_reason,
            "passed": is_valid,  # Main criterion: slot is valid (in scope and not present)
            "error": None
        }
    except Exception as e:
        return {
            "query": query,
            "expected_slot": expected_slot,
            "actual_slot": None,
            "expected_source": expected_source,
            "actual_source": None,
            "intent": None,
            "latency_ms": 0,
            "slot_match": False,
            "source_match": False,
            "is_valid": False,
            "validation_reason": str(e),
            "passed": False,
            "error": str(e)
        }


def run_tests():
    """Run all test queries and generate report."""
    print(f"🚀 Starting test suite with {len(test_queries)} queries...\n")
    print(f"API Endpoint: {API_URL}\n")
    print(f"📋 FLEXIBLE VALIDATION CRITERIA:")
    print(f"   1. ✅ Slot must be in scope for the LOB")
    print(f"   2. ✅ Slot must NOT already be present in query\n")
    print("=" * 80)
    
    results = []
    passed = 0
    failed = 0
    exact_matches = 0
    flexible_passes = 0
    
    for i, (query, expected_slot, expected_source) in enumerate(test_queries, 1):
        print(f"[{i}/{len(test_queries)}] Testing: {query[:60]}...", end=" ")
        
        result = test_query(query, expected_slot, expected_source)
        results.append(result)
        
        if result["passed"]:
            passed += 1
            if result["slot_match"]:
                exact_matches += 1
                print("✅ PASS (exact)")
            else:
                flexible_passes += 1
                print(f"✅ PASS (flex: {result['actual_slot']})")
        else:
            failed += 1
            print(f"❌ FAIL - {result['validation_reason'][:50]}")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    print("\n" + "=" * 80)
    print("\n📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Total Queries: {len(test_queries)}")
    print(f"✅ Passed: {passed} ({passed/len(test_queries)*100:.1f}%)")
    print(f"   • Exact matches: {exact_matches}")
    print(f"   • Flexible passes: {flexible_passes}")
    print(f"❌ Failed: {failed} ({failed/len(test_queries)*100:.1f}%)")
    
    # Statistics by expected source
    rule_based_expected = [r for r in results if r["expected_source"] == "rule_based"]
    llm_expected = [r for r in results if r["expected_source"] == "llm_fallback"]
    
    rule_based_passed = sum(1 for r in rule_based_expected if r["passed"])
    llm_passed = sum(1 for r in llm_expected if r["passed"])
    
    print(f"\n📈 BY EXPECTED SOURCE:")
    print(f"Rule-based: {rule_based_passed}/{len(rule_based_expected)} passed ({rule_based_passed/len(rule_based_expected)*100:.1f}%)")
    print(f"LLM Fallback: {llm_passed}/{len(llm_expected)} passed ({llm_passed/len(llm_expected)*100:.1f}%)")
    
    # Average latency
    avg_latency = sum(r["latency_ms"] for r in results if r["latency_ms"]) / len(results)
    print(f"\n⏱️  Average Latency: {avg_latency:.2f}ms")
    
    # Failed queries report
    if failed > 0:
        print("\n" + "=" * 80)
        print("❌ FAILED QUERIES REPORT")
        print("=" * 80)
        
        failed_results = [r for r in results if not r["passed"]]
        
        for r in failed_results:
            print(f"\nQuery: {r['query']}")
            print(f"  Expected: {r['expected_slot']} | Actual: {r['actual_slot']} | Intent: {r['intent']}")
            print(f"  Reason: {r['validation_reason']}")
            print(f"  Latency: {r['latency_ms']}ms")
    
    # Export detailed results to JSON
    output_file = "test_results_flexible.json"
    with open(output_file, "w") as f:
        json.dump({
            "summary": {
                "total": len(test_queries),
                "passed": passed,
                "failed": failed,
                "exact_matches": exact_matches,
                "flexible_passes": flexible_passes,
                "pass_rate": f"{passed/len(test_queries)*100:.1f}%",
                "avg_latency_ms": avg_latency
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
