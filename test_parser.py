#!/usr/bin/env python3
"""Quick test script to debug document parsing."""

from document_parser import parse_date, split_entries_by_date, validate_entries

# Test date parsing
test_dates = [
    "2025-12-31",
    "12/31/2025",
    "December 31, 2025",
    "Dec 31, 2025",
]

print("Testing date parsing:")
for date_str in test_dates:
    result = parse_date(date_str)
    print(f"  '{date_str}' -> '{result}'")

# Test entry splitting
test_text = """2025-12-31
Had a wonderful day at the beach. The weather was perfect.

2025-12-30
Finished reading that book I've been working on. Great ending!

2025-12-29
Rainy day, but managed to be productive at home."""

print("\nTesting entry splitting:")
entries = split_entries_by_date(test_text)
for entry in entries:
    print(f"  Date: {entry['date']}")
    print(f"  Content: {entry['content'][:50]}...")

# Test validation
print("\nTesting validation:")
valid, errors = validate_entries(entries)
print(f"  Valid entries: {len(valid)}")
print(f"  Errors: {len(errors)}")
for error in errors:
    print(f"    - {error}")
