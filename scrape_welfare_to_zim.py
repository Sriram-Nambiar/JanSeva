#!/usr/bin/env python3
"""JanSeva openZIM Welfare Portal Scraper & Kiwix Compiler CLI.

Scrapes welfare portals (MyScheme, Central DBT, State Welfare Portals)
and compiles them into fully-compliant `.zim` archives with full-text search,
offline CSS, vector assets, and statutory requirement guides.

Compatible with Kiwix Desktop (https://github.com/Sriram-Nambiar/kiwix-desktop)
and the openZIM standard (https://github.com/openzim).

Usage:
    # 1. Scrape live portal and build ZIM archive:
    python scrape_welfare_to_zim.py --url https://myscheme.gov.in --output packs/myscheme_portal.zim

    # 2. Compile comprehensive verified welfare pack without network delay:
    python scrape_welfare_to_zim.py --curated-pack --output packs/welfare_all_india.zim

    # 3. Inspect any .zim file:
    python scrape_welfare_to_zim.py --inspect packs/welfare_schemes.zim
"""

import argparse
import json
import pathlib
import sys

from scraper.models import ScraperConfig
from scraper.welfare_scraper import WelfareZimScraper


BANNER = r"""
========================================================================
   __                                                   
  / /  ___ _ ___   ___  ___  _  __ ___ _                
 / /__/ _ `/ _ \ (_-< / -_)| |/ // _ `/                
/____/\_,_/_//_//___/ \__/ |___/ \_,_/  openZIM Scraper
========================================================================
 Offline Welfare Knowledge Archiver for Kiwix Desktop & Edge Kiosks
 Standard: openZIM (https://openzim.org) | libzim v3.13.1
========================================================================
"""


def main():
    parser = argparse.ArgumentParser(
        description="JanSeva openZIM Welfare Scraper: Scrapes Indian welfare portals to offline Kiwix .zim archives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--url",
        type=str,
        default="https://myscheme.gov.in",
        help="Seed URL of the welfare portal to crawl (default: https://myscheme.gov.in)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="packs/welfare_portal.zim",
        help="Target .zim file path (default: packs/welfare_portal.zim)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="JanSeva Welfare Directory",
        help="Human-readable title of the ZIM archive",
    )
    parser.add_argument(
        "--desc",
        type=str,
        default="Complete offline openZIM directory of Indian welfare schemes with statutory eligibility guides.",
        help="Description of the archive content",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="eng",
        help="ISO 639-3 language code for full-text search indexing (e.g. 'eng', 'hin', 'kan')",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=25,
        help="Maximum scheme pages to scrape",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Link crawl depth",
    )
    parser.add_argument(
        "--curated-pack",
        action="store_true",
        help="Compile curated high-fidelity welfare database directly without network delay",
    )
    parser.add_argument(
        "--inspect",
        type=str,
        default=None,
        help="Inspect an existing .zim archive and display openZIM metadata and entries",
    )

    args = parser.parse_args()

    print(BANNER)

    scraper = WelfareZimScraper(log_callback=lambda msg: print(f"[*] {msg}"))

    # Inspect Mode
    if args.inspect:
        target_path = pathlib.Path(args.inspect)
        print(f"Inspecting ZIM archive: {target_path}...\n")
        try:
            info = scraper.inspect_zim(target_path)
            print(f"Archive Filename:    {info['filename']}")
            print(f"Total File Size:     {info['filesize_kb']} KB ({info['filesize_bytes']} bytes)")
            print(f"Total Entries:       {info['entry_count']}")
            print(f"Article Count:       {info['article_count']}")
            print(f"Media Assets:        {info['media_count']}")
            print(f"Main Entry Path:     {info['main_path']}")
            print(f"Fulltext Index:      {'YES (Active)' if info['has_fulltext_index'] else 'NO'}")
            print(f"Title Index:         {'YES (Active)' if info['has_title_index'] else 'NO'}")
            print("\nopenZIM Metadata Tags:")
            for k, v in info["metadata"].items():
                print(f"  - {k}: {v}")
            print("\nSample Indexed Entries:")
            for e in info["sample_entries"][:10]:
                print(f"  • {e['path']} -> {e['title']}")
            print("\n[OK] Archive is valid and fully compatible with Kiwix Desktop.")
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to inspect ZIM archive: {e}", file=sys.stderr)
            return 1

    # Output file setup
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Curated Pack Mode
    if args.curated_pack:
        print(f"Compiling Curated Welfare Registry to {output_path}...")
        try:
            zim_file = scraper.generate_curated_welfare_zim(
                output_path=output_path,
                title=args.title,
                lang=args.lang,
            )
            print(f"\n[SUCCESS] Compiled {zim_file} ({round(zim_file.stat().st_size / 1024, 1)} KB)")
            print("[INFO] Open this file directly in Kiwix Desktop via File > Open File...")
            return 0
        except Exception as e:
            print(f"[ERROR] Compilation failed: {e}", file=sys.stderr)
            return 1

    # Live Crawl Mode
    config = ScraperConfig(
        seed_url=args.url,
        output_path=output_path,
        title=args.title,
        description=args.desc,
        language=args.lang,
        max_pages=args.max_pages,
        max_depth=args.depth,
        offline_fallback=True,
    )

    try:
        result = scraper.crawl_and_compile(config)
        print("\n" + "=" * 60)
        print("  SCRAPING & ZIM COMPILATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"  Output Archive:   {result['zim_path']}")
        print(f"  Archive Size:     {result['size_kb']} KB")
        print(f"  Schemes Indexed:  {result['article_count']}")
        print(f"  Elapsed Time:     {result['duration_seconds']} seconds")
        print("=" * 60)
        print("\nHow to browse offline:")
        print("1. Launch Kiwix Desktop (https://github.com/Sriram-Nambiar/kiwix-desktop)")
        print(f"2. Click File -> Open -> Select '{result['zim_filename']}'")
        print("3. Kiwix will load the offline catalog and enable full-text instant search!")
        return 0
    except Exception as e:
        print(f"[ERROR] Scraper pipeline failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
