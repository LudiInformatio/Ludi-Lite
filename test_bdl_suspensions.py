#!/usr/bin/env python3
"""
Test BDL API for Suspension Data
Specifically checking if Paul George's 25-game suspension appears in BDL injury data.

Usage: python3 test_bdl_suspensions.py
"""

import json
import sys
from typing import Dict, List

try:
    import bdl_client
except ImportError:
    print("❌ Error: Could not import bdl_client")
    print("Make sure you're running from the Ludi-Lite directory")
    sys.exit(1)


def test_bdl_suspensions():
    """Test if BDL returns suspension data, specifically Paul George."""

    print("=" * 80)
    print("BDL SUSPENSION DATA TEST")
    print("=" * 80)
    print()

    # Check if API key is configured
    if not bdl_client.is_available():
        print("⚠️  BDL API key not configured")
        print("Set BALLDONTLIE_KEY in .streamlit/secrets.toml or environment")
        return

    print("✓ BDL API key found")
    print()

    # Fetch all current injuries
    print("📊 Fetching injury data from BDL...")
    try:
        injuries = bdl_client.get_injuries()
    except Exception as e:
        print(f"❌ Error fetching injuries: {e}")
        return

    if not injuries:
        print("⚠️  No injury data returned (empty list)")
        return

    print(f"✓ Received {len(injuries)} injury records")
    print()

    # --- TEST 1: Search for Paul George specifically ---
    print("=" * 80)
    print("TEST 1: Paul George (PHI - 25-game suspension)")
    print("=" * 80)
    print()

    pg_records = []
    for inj in injuries:
        player = inj.get("player", {})
        first = player.get("first_name", "").lower()
        last = player.get("last_name", "").lower()

        if "paul" in first and "george" in last:
            pg_records.append(inj)

    if pg_records:
        print("✅ Paul George FOUND in BDL injury data!")
        print()
        for record in pg_records:
            print(json.dumps(record, indent=2))
            print()

            # Highlight key fields
            status = record.get("status", "N/A")
            comment = record.get("comment", "N/A")
            player_obj = record.get("player", {})
            team_obj = record.get("team", {})

            print(f"📌 Key Fields:")
            print(f"   Player: {player_obj.get('first_name')} {player_obj.get('last_name')}")
            print(f"   Team: {team_obj.get('abbreviation', 'N/A')} ({team_obj.get('full_name', 'N/A')})")
            print(f"   Status: {status}")
            print(f"   Comment: {comment}")
            print(f"   Report Date: {record.get('report_date', 'N/A')}")
            print()
    else:
        print("❌ Paul George NOT found in BDL injury data")
        print("   (Same behavior as Tank01 - suspended players removed?)")
        print()

    # --- TEST 2: Check all unique status values ---
    print("=" * 80)
    print("TEST 2: All Unique Status Values in BDL")
    print("=" * 80)
    print()

    all_statuses = set()
    status_examples = {}  # Store one example for each status

    for inj in injuries:
        status = inj.get("status", "").strip()
        if status:
            all_statuses.add(status)
            if status not in status_examples:
                player = inj.get("player", {})
                status_examples[status] = f"{player.get('first_name', '')} {player.get('last_name', '')}"

    print(f"Found {len(all_statuses)} unique status values:")
    print()
    for status in sorted(all_statuses):
        example = status_examples.get(status, "N/A")
        print(f"  • {status:20s} (e.g., {example})")
    print()

    # --- TEST 3: Search for suspension keywords in comments ---
    print("=" * 80)
    print("TEST 3: Suspension Keywords in Comments")
    print("=" * 80)
    print()

    suspension_keywords = ["suspend", "disciplin", "violation", "game ban"]
    suspension_matches = []

    for inj in injuries:
        comment = inj.get("comment", "").lower()
        for keyword in suspension_keywords:
            if keyword in comment:
                player = inj.get("player", {})
                suspension_matches.append({
                    "player": f"{player.get('first_name', '')} {player.get('last_name', '')}",
                    "status": inj.get("status", "N/A"),
                    "comment": inj.get("comment", "N/A")
                })
                break

    if suspension_matches:
        print(f"✓ Found {len(suspension_matches)} records with suspension keywords:")
        print()
        for match in suspension_matches:
            print(f"   Player: {match['player']}")
            print(f"   Status: {match['status']}")
            print(f"   Comment: {match['comment']}")
            print()
    else:
        print("❌ No records with suspension keywords found")
        print("   Keywords searched: suspend, disciplin, violation, game ban")
        print()

    # --- SUMMARY ---
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    if pg_records:
        print("✅ RESULT: BDL DOES return suspension data")
        print(f"   Paul George found with status: {pg_records[0].get('status', 'N/A')}")
        print()
        print("📌 RECOMMENDATION: BDL can be used as primary injury source")
        print("   - Suspensions appear in the data (unlike Tank01)")
        print("   - 15-minute cache already in place")
        print("   - Could replace manual KNOWN_SUSPENSIONS")
    else:
        print("❌ RESULT: BDL does NOT return suspension data")
        print("   Paul George not found (same as Tank01)")
        print()
        print("📌 RECOMMENDATION: Keep manual KNOWN_SUSPENSIONS")
        print("   - Both Tank01 and BDL remove/omit suspended players")
        print("   - Manual tracking is the only reliable source")
        print("   - Document this limitation in code comments")
    print()

    # Show sample record structure
    if injuries:
        print("=" * 80)
        print("SAMPLE BDL INJURY RECORD STRUCTURE")
        print("=" * 80)
        print()
        print("First record in dataset:")
        print(json.dumps(injuries[0], indent=2))
        print()


if __name__ == "__main__":
    test_bdl_suspensions()
