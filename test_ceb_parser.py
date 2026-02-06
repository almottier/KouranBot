#!/usr/bin/env python3
"""Quick test script for the CEB parser."""

import asyncio
import json
import sys

# Add the project root to path
sys.path.insert(0, '.')

from bot.ceb_parser import (
    fetch_and_parse_outages,
    parse_french_date,
    generate_outage_id,
)


def test_date_parsing():
    """Test French date parsing."""
    print("Testing date parsing...")

    test_cases = [
        "Le dimanche 13 mars 2022 de 09:30:00 à 13:00:00",
        "Le lundi 14 février 2022 de 08:00:00 à 16:00:00",
    ]

    for date_str in test_cases:
        from_time, to_time = parse_french_date(date_str)
        print(f"  Input: {date_str}")
        print(f"  From:  {from_time}")
        print(f"  To:    {to_time}")
        print()


def test_id_generation():
    """Test ID generation matches expected format."""
    print("Testing ID generation...")

    outage = {
        'date': 'Le dimanche 13 mars 2022 de 09:30:00 à 13:00:00',
        'locality': 'TAMARIN',
        'streets': 'AVE DES MARLINS',
        'district': 'blackriver',
    }

    outage_id = generate_outage_id(outage)
    print(f"  Outage: {outage}")
    print(f"  Generated ID: {outage_id}")
    print(f"  ID length: {len(outage_id)} (expected: 32)")
    print()


async def test_full_fetch():
    """Test fetching and parsing from CEB website."""
    print("Testing full fetch from CEB website...")
    print("(This may take a few seconds)")
    print()

    try:
        data = await fetch_and_parse_outages()

        today_count = len(data.get('today', []))
        future_count = len(data.get('future', []))

        print(f"  Today outages: {today_count}")
        print(f"  Future outages: {future_count}")
        print()

        # Show sample outages
        if data.get('today'):
            print("  Sample today outage:")
            print(f"    {json.dumps(data['today'][0], indent=4)}")
            print()

        if data.get('future'):
            print("  Sample future outage:")
            print(f"    {json.dumps(data['future'][0], indent=4)}")
            print()

        print("SUCCESS: CEB parser is working!")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("CEB Parser Test")
    print("=" * 60)
    print()

    test_date_parsing()
    test_id_generation()

    success = asyncio.run(test_full_fetch())

    print("=" * 60)
    sys.exit(0 if success else 1)
