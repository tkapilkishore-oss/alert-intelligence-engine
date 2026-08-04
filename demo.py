"""CLI Demonstration Script for Alert Intelligence Engine (Stage 12)."""

import json
from pathlib import Path

from src.pipeline import AlertPipeline


def main() -> None:
    """Run CLI showcase demonstration across all supported formats and natural language layer."""
    print("=" * 80)
    print(" ALERT INTELLIGENCE ENGINE — STAGE 12 SYSTEM DEMONSTRATION")
    print("=" * 80)

    pipe = AlertPipeline()
    data_dir = Path("data")

    # 1. JSON Processing
    print("\n--- 1. JSON Alert Processing ---")
    json_path = data_dir / "raw_alerts_json.json"
    raw_json = json.loads(json_path.read_text())
    json_alerts = pipe.process(raw_json, "json")
    json_dup_count = sum(1 for a in json_alerts if a.is_duplicate)
    print(f"Parsed Count: {len(json_alerts)}")
    print(f"Duplicate Count: {json_dup_count}")
    print("Sample Normalized Alert (First Record):")
    if json_alerts:
        print(json.dumps(json_alerts[0].model_dump(), indent=2))

    # 2. CAP XML Processing
    print("\n--- 2. CAP XML Alert Processing ---")
    cap_path = data_dir / "raw_alerts_cap.xml"
    raw_cap = cap_path.read_text()
    cap_alerts = pipe.process(raw_cap, "cap_xml")
    cap_dup_count = sum(1 for a in cap_alerts if a.is_duplicate)
    print(f"Parsed Count: {len(cap_alerts)}")
    print(f"Duplicate Count: {cap_dup_count}")
    print("Sample Normalized Alert (First Record):")
    if cap_alerts:
        print(json.dumps(cap_alerts[0].model_dump(), indent=2))

    # 3. RSS XML Processing
    print("\n--- 3. RSS XML Alert Processing ---")
    rss_path = data_dir / "raw_alerts_rss.xml"
    raw_rss = rss_path.read_text()
    rss_alerts = pipe.process(raw_rss, "rss")
    rss_dup_count = sum(1 for a in rss_alerts if a.is_duplicate)
    print(f"Parsed Count: {len(rss_alerts)}")
    print(f"Duplicate Count: {rss_dup_count}")
    print("Sample Normalized Alert (First Record):")
    if rss_alerts:
        print(json.dumps(rss_alerts[0].model_dump(), indent=2))

    # 4. Plaintext Processing
    print("\n--- 4. Plaintext Alert Processing ---")
    plaintext_path = data_dir / "raw_alerts_plaintext.txt"
    raw_plaintext = plaintext_path.read_text()
    plaintext_alerts = pipe.process(raw_plaintext, "plaintext")
    plaintext_dup_count = sum(1 for a in plaintext_alerts if a.is_duplicate)
    print(f"Parsed Count: {len(plaintext_alerts)}")
    print(f"Duplicate Count: {plaintext_dup_count}")
    print("Sample Normalized Alert (First Record):")
    if plaintext_alerts:
        print(json.dumps(plaintext_alerts[0].model_dump(), indent=2))

    # 5. Natural Language Layer Processing
    print("\n--- 5. Natural Language Layer Processing ---")
    nl_text = "Heavy rainfall is expected tomorrow morning in Devapur. People should avoid flooded roads."
    print(f"Input Prompt: \"{nl_text}\"")
    nl_alerts = pipe.process_natural_language(nl_text)
    nl_dup_count = sum(1 for a in nl_alerts if a.is_duplicate)
    print(f"Parsed Count: {len(nl_alerts)}")
    print(f"Duplicate Count: {nl_dup_count}")
    print("Normalized Output Alert:")
    if nl_alerts:
        print(json.dumps(nl_alerts[0].model_dump(), indent=2))

    # 6. Sequential Processing Summary Across All Formats
    print("\n" + "=" * 80)
    print(" SEQUENTIAL PROCESSING SUMMARY ACROSS ALL FORMATS")
    print("=" * 80)

    all_normalized = json_alerts + cap_alerts + rss_alerts + plaintext_alerts
    total_alerts = len(all_normalized)
    total_duplicates = sum(1 for a in all_normalized if a.is_duplicate)

    print(f"JSON : {len(json_alerts)}")
    print(f"CAP : {len(cap_alerts)}")
    print(f"RSS : {len(rss_alerts)}")
    print(f"PLAINTEXT : {len(plaintext_alerts)}")
    print()
    print(f"TOTAL ALERTS : {total_alerts}")
    print(f"TOTAL DUPLICATES : {total_duplicates}")
    print("=" * 80)


if __name__ == "__main__":
    main()
