"""Test script with predefined queries - easy to add/remove test cases.

Usage:
    python test_queries.py                    # Run all tests
    python test_queries.py 1 3 5              # Run tests 1, 3, 5 only
    python test_queries.py --llm              # Run all with LLM fallback
    python test_queries.py 1 3 --llm          # Run tests 1, 3 with LLM fallback

To add/remove test cases, edit the TEST_QUERIES list below.
"""

from src.parser.rule_engine import RuleEngine
from src.parser.suggestion_generator import SuggestionGenerator
from src.llm.llm_fallback import LLMFallbackService
import asyncio

# ============================================================================
# TEST QUERIES - Add/remove queries here as needed
# ============================================================================

TEST_QUERIES = [
    # Basic intent detection
    "book a flight",
    "hotel in mumbai",
    "train from delhi",
    
    # City-first queries
    "mumbai",
    "mumbai to delhi",
    "from mumbai",
    "to mumbai",
    
    # Date-related queries
    "weekday on",
    "weekend on",
    "flight from delhi to mumbai on",
    "hotel in goa on",
    
    # Multi-word cities
    "new yo",
    "sao pa",
    "san fra",
    
    # Slot inference
    "i want to book a flight",
    "flight from delhi to mumbai",
    "hotel in goa for 3 nights",
    "train from delhi to mumbai for 2 passengers",
    
    # Edge cases
    "weekend to where",
    "from ",
    "to ",
    "something on",
]

# ============================================================================
# Test Functions
# ============================================================================

def test_query(query: str, use_llm_fallback: bool = False):
    """Test a single query and display results."""
    engine = RuleEngine(enable_cache=False)
    generator = SuggestionGenerator()
    llm_fallback = LLMFallbackService()
    
    print("\n" + "=" * 80)
    print(f"Query: '{query}'")
    print("=" * 80)
    
    match = engine.match(query)
    
    if match:
        if match.intent:
            print(f"\n✓ Intent Detected: {match.intent.upper()}")
        else:
            print(f"\n✓ Partial Match Detected (intent not yet specified)")
        print(f"  Confidence: {match.confidence:.2%}")
        print(f"  Next Slot: {match.next_slot}")
        
        if match.entities:
            print(f"\n  Extracted Entities:")
            for entity_type, values in match.entities.items():
                if values:
                    print(f"    - {entity_type}: {values}")
        
        suggestions = generator.generate(match, include_placeholder=True, max_suggestions=10, query=query)
        if suggestions:
            print(f"\n  Suggestions ({len(suggestions)}):")
            for i, s in enumerate(suggestions, 1):
                marker = " [PLACEHOLDER]" if s.is_placeholder else " [SELECTABLE]"
                print(f"    {i}. '{s.text}'{marker}")
        else:
            print("\n  (no suggestions)")
    else:
        print("\n✗ No rule matched")
        
        if use_llm_fallback:
            print("  → Trying LLM fallback...")
            try:
                match = asyncio.run(llm_fallback.get_next_slot(query))
                if match:
                    print(f"  ✓ LLM Fallback: Next Slot = '{match.next_slot}'")
                    suggestions = generator.generate(match, include_placeholder=True, max_suggestions=10, query=query)
                    if suggestions:
                        print(f"\n  LLM Suggestions ({len(suggestions)}):")
                        for i, s in enumerate(suggestions, 1):
                            marker = " [PLACEHOLDER]" if s.is_placeholder else " [SELECTABLE]"
                            print(f"    {i}. '{s.text}'{marker}")
                else:
                    print("  ✗ LLM fallback also failed")
            except Exception as e:
                print(f"  ✗ LLM fallback error: {e}")
        else:
            print("  (LLM fallback disabled - set use_llm_fallback=True to enable)")
    
    print("=" * 80)

def run_all_tests(use_llm_fallback: bool = False):
    """Run all test queries."""
    print("\n" + "=" * 80)
    print(f"Running {len(TEST_QUERIES)} Test Queries")
    print("=" * 80)
    
    results = {
        "matched": 0,
        "no_match": 0,
        "with_intent": 0,
        "partial": 0
    }
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}]")
        engine = RuleEngine(enable_cache=False)
        match = engine.match(query)
        
        if match:
            results["matched"] += 1
            if match.intent:
                results["with_intent"] += 1
            else:
                results["partial"] += 1
        else:
            results["no_match"] += 1
        
        test_query(query, use_llm_fallback=use_llm_fallback)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total queries: {len(TEST_QUERIES)}")
    print(f"  ✓ Matched: {results['matched']}")
    print(f"    - With intent: {results['with_intent']}")
    print(f"    - Partial match: {results['partial']}")
    print(f"  ✗ No match: {results['no_match']}")
    print("=" * 80)

def run_specific_tests(indices: list, use_llm_fallback: bool = False):
    """Run specific test queries by index (1-based)."""
    print("\n" + "=" * 80)
    print(f"Running {len(indices)} Specific Test Queries")
    print("=" * 80)
    
    for idx in indices:
        if 1 <= idx <= len(TEST_QUERIES):
            query = TEST_QUERIES[idx - 1]
            print(f"\n[Test #{idx}]")
            test_query(query, use_llm_fallback=use_llm_fallback)
        else:
            print(f"\n[Test #{idx}] ✗ Invalid index (valid range: 1-{len(TEST_QUERIES)})")

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    use_llm = "--llm" in sys.argv or "-l" in sys.argv
    
    if len(sys.argv) > 1 and sys.argv[1] not in ["--llm", "-l"]:
        # Run specific queries by index
        try:
            indices = [int(x) for x in sys.argv[1:] if x not in ["--llm", "-l"]]
            run_specific_tests(indices, use_llm_fallback=use_llm)
        except ValueError:
            print("Usage:")
            print("  python test_queries.py                    # Run all tests")
            print("  python test_queries.py 1 3 5              # Run tests 1, 3, 5")
            print("  python test_queries.py --llm              # Run all with LLM fallback")
            print("  python test_queries.py 1 3 --llm          # Run tests 1, 3 with LLM fallback")
    else:
        # Run all tests
        run_all_tests(use_llm_fallback=use_llm)
