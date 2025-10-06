"""
Test script for PII Guardrails functionality.

This script tests the NeMo Guardrails PII detection system with various
queries containing PII and non-PII content.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from guardrails.pii_guardrails import check_ticket_for_pii, get_enabled_pii_checks
from datetime import datetime


# Test queries with different PII scenarios
TEST_QUERIES = {
    "clean_query": {
        "text": "The application is showing error 500 when trying to access the dashboard. Need help resolving this issue.",
        "expected_pii": False,
        "description": "Clean query without PII"
    },
    "email_pii": {
        "text": "User john.doe@example.com is unable to login to the system.",
        "expected_pii": True,
        "description": "Query with email address"
    },
    "phone_pii": {
        "text": "Customer called from 555-123-4567 reporting connection issues.",
        "expected_pii": True,
        "description": "Query with phone number"
    },
    "name_pii": {
        "text": "John Smith from accounting department needs password reset.",
        "expected_pii": True,
        "description": "Query with person name"
    },
    "ssn_pii": {
        "text": "Member with SSN 123-45-6789 has claim processing error.",
        "expected_pii": True,
        "description": "Query with Social Security Number"
    },
    "credit_card_pii": {
        "text": "Payment failed for card 4532-1234-5678-9010.",
        "expected_pii": True,
        "description": "Query with credit card number"
    },
    "ip_address_pii": {
        "text": "Server at IP 192.168.1.100 is not responding.",
        "expected_pii": True,
        "description": "Query with IP address"
    },
    "multiple_pii": {
        "text": "Contact Jane Doe at jane.doe@company.com or call 555-987-6543 for member ID 123-45-6789.",
        "expected_pii": True,
        "description": "Query with multiple PII types"
    },
    "technical_query": {
        "text": "Database connection timeout error in production environment. Error code: CONN_TIMEOUT_3001",
        "expected_pii": False,
        "description": "Technical query without PII"
    },
    "empty_query": {
        "text": "",
        "expected_pii": False,
        "description": "Empty query"
    }
}


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def print_result(test_name: str, query_info: dict, result):
    """Print formatted test result."""
    print(f"TEST: {test_name}")
    print(f"Description: {query_info['description']}")
    print(f"Query: {query_info['text'][:100]}...")
    print(f"\nExpected PII: {query_info['expected_pii']}")
    print(f"Detected PII: {result.pii_found}")

    if result.pii_found:
        print(f"PII Types Found: {', '.join(result.pii_types)}")
        print(f"PII Count: {result.pii_count}")

    # Check if result matches expectation
    match = result.pii_found == query_info['expected_pii']
    status = "✓ PASS" if match else "✗ FAIL"
    print(f"\nResult: {status}")
    print(f"Session ID: {result.session_id}")
    print(f"Timestamp: {result.timestamp}")

    return match


def run_single_test(query_text: str, session_id: str = "test_session"):
    """Run a single test with custom query."""
    print_separator()
    print("SINGLE QUERY TEST")
    print_separator()

    print(f"Query: {query_text}")
    print(f"Session ID: {session_id}")
    print("\nChecking for PII...")

    result = check_ticket_for_pii(query_text, session_id)

    print(f"\nPII Detected: {result.pii_found}")
    if result.pii_found:
        print(f"PII Types: {', '.join(result.pii_types)}")
        print(f"PII Count: {result.pii_count}")
        print(f"Ticket Excerpt: {result.ticket_excerpt}")
    else:
        print("No PII detected - query is safe to process")

    print(f"\nSession ID: {result.session_id}")
    print(f"Timestamp: {result.timestamp}")

    return result


def run_all_tests():
    """Run all predefined test cases."""
    print_separator()
    print("RUNNING ALL GUARDRAILS TESTS")
    print_separator()

    # Display enabled PII checks
    print("Enabled PII Checks:")
    for pii_type in get_enabled_pii_checks():
        print(f"  - {pii_type}")

    print_separator()

    # Run all tests
    results = {}
    passed = 0
    failed = 0

    for test_name, query_info in TEST_QUERIES.items():
        print_separator()

        session_id = f"test_{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = check_ticket_for_pii(query_info['text'], session_id)

        match = print_result(test_name, query_info, result)
        results[test_name] = {
            'result': result,
            'passed': match
        }

        if match:
            passed += 1
        else:
            failed += 1

    # Print summary
    print_separator()
    print("TEST SUMMARY")
    print_separator()
    print(f"Total Tests: {len(TEST_QUERIES)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(TEST_QUERIES)*100):.1f}%")
    print_separator()

    return results


def main():
    """Main test execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Test PII Guardrails')
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Run a single test with custom query'
    )
    parser.add_argument(
        '--session-id', '-s',
        type=str,
        default=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help='Session ID for the test'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Run all predefined test cases'
    )

    args = parser.parse_args()

    try:
        if args.query:
            # Run single test with custom query
            result = run_single_test(args.query, args.session_id)
        elif args.all:
            # Run all predefined tests
            results = run_all_tests()
        else:
            # Default: run all tests
            print("No arguments provided. Running all tests...")
            print("Use --query 'your query here' to test a specific query")
            print("Use --all to explicitly run all tests")
            print_separator()
            results = run_all_tests()

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
