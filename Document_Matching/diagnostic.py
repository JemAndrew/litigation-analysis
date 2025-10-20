#!/usr/bin/env python3
"""
Quick diagnostic: What C- files actually exist in folder 01?
"""

from pathlib import Path
import re

folder_01 = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1\73. Review of PHL Disclosures\01. Claimant's Factual Exhibits")

print("="*70)
print("DIAGNOSTIC: CHECKING ALL C- FILES")
print("="*70)

# Find ALL C- files
all_c_files = list(folder_01.rglob("C-*.pdf"))
print(f"\n✅ Found {len(all_c_files)} C- files total\n")

# Extract numbers and sort
c_numbers = []
for file_path in all_c_files:
    match = re.match(r'C-0*(\d+)', file_path.stem)
    if match:
        c_numbers.append(int(match.group(1)))

c_numbers = sorted(set(c_numbers))

if c_numbers:
    print(f"📊 C- FILE RANGE:")
    print(f"   Lowest: C-{min(c_numbers)}")
    print(f"   Highest: C-{max(c_numbers)}")
    print(f"   Total unique numbers: {len(c_numbers)}")
    
    # Show gaps
    print(f"\n📋 BREAKDOWN BY RANGE:")
    ranges = {
        "C-1 to C-30": [n for n in c_numbers if 1 <= n <= 30],
        "C-31 to C-60": [n for n in c_numbers if 31 <= n <= 60],
        "C-61 to C-100": [n for n in c_numbers if 61 <= n <= 100],
        "C-101 to C-140": [n for n in c_numbers if 101 <= n <= 140],
        "C-141+": [n for n in c_numbers if n >= 141]
    }
    
    for range_name, nums in ranges.items():
        if nums:
            print(f"   {range_name}: {len(nums)} files (C-{min(nums)} to C-{max(nums)})")
        else:
            print(f"   {range_name}: 0 files ❌")
    
    # Show first 20 and last 20
    print(f"\n📄 FIRST 20 C- FILES:")
    for n in c_numbers[:20]:
        print(f"   C-{n}")
    
    if len(c_numbers) > 40:
        print(f"\n   ... ({len(c_numbers) - 40} more) ...\n")
        
        print(f"📄 LAST 20 C- FILES:")
        for n in c_numbers[-20:]:
            print(f"   C-{n}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)

# Check if we only have C-31 to C-140
c_31_to_140 = [n for n in c_numbers if 31 <= n <= 140]
if len(c_31_to_140) == len(c_numbers):
    print("\n⚠️  YOU ONLY HAVE C-31 TO C-140!")
    print("   There are NO C- files outside this range.")
    print("   The script removing the range restriction won't help.")
    print("   You're already checking ALL C- files that exist.")
else:
    print(f"\n✅ You have C- files outside C-31 to C-140!")
    print(f"   Outside range: {len(c_numbers) - len(c_31_to_140)} files")
    print(f"   The updated script WILL find more matches!")

print("="*70)