#!/usr/bin/env python3
"""
Quick diagnostic to check C- file naming patterns
British English throughout.
"""

from pathlib import Path
import re

def main():
    """Check naming patterns for C- files"""
    
    folder = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1\73. Review of PHL Disclosures\01. Claimant's Factual Exhibits")
    
    print("="*70)
    print("C- FILE NAMING PATTERN CHECK")
    print("="*70)
    print(f"Folder: {folder}\n")
    
    # Get all C- PDFs (including subdirectories)
    c_files = sorted(folder.rglob("C-*.pdf"))
    
    print(f"Found {len(c_files)} C- files\n")
    
    if not c_files:
        print("❌ No C- files found!")
        return
    
    # Analyse naming patterns
    single_digit_with_zero = []  # C-01, C-02, C-03
    single_digit_no_zero = []    # C-1, C-2, C-3
    double_digit = []            # C-10, C-38, C-53
    triple_digit = []            # C-100, C-135
    
    for file_path in c_files:
        name = file_path.stem  # Filename without .pdf
        
        # Extract number
        match = re.match(r'C-(\d+)', name)
        if match:
            number_str = match.group(1)
            number = int(number_str)
            
            if number < 10:
                if len(number_str) == 2:  # Has leading zero
                    single_digit_with_zero.append(name)
                else:
                    single_digit_no_zero.append(name)
            elif number < 100:
                double_digit.append(name)
            else:
                triple_digit.append(name)
    
    # Display results
    print("NAMING PATTERN ANALYSIS:")
    print("-" * 70)
    
    if single_digit_with_zero:
        print(f"\n✅ Single digits WITH leading zero (C-01 format): {len(single_digit_with_zero)}")
        print(f"   Examples: {', '.join(single_digit_with_zero[:5])}")
    
    if single_digit_no_zero:
        print(f"\n✅ Single digits WITHOUT leading zero (C-1 format): {len(single_digit_no_zero)}")
        print(f"   Examples: {', '.join(single_digit_no_zero[:5])}")
    
    if double_digit:
        print(f"\n✅ Double digits (C-10+ format): {len(double_digit)}")
        print(f"   Examples: {', '.join(double_digit[:5])}")
    
    if triple_digit:
        print(f"\n✅ Triple digits (C-100+ format): {len(triple_digit)}")
        print(f"   Examples: {', '.join(triple_digit[:5])}")
    
    # Check for missing files from your list
    missing = ['C-1', 'C-2', 'C-3', 'C-5', 'C-7', 'C-8', 'C-9', 
               'C-38', 'C-39', 'C-41', 'C-53', 'C-62', 'C-115', 'C-116']
    
    print("\n" + "="*70)
    print("CHECKING YOUR MISSING FILES:")
    print("="*70)
    
    for ref in missing:
        number = int(ref.split('-')[1])
        
        # Try with leading zero
        zero_padded = f"C-{number:02d}"
        
        # Check what exists
        exact_match = f"{ref}.pdf"
        zero_match = f"{zero_padded}.pdf"
        
        found_exact = any(f.name == exact_match for f in c_files)
        found_zero = any(f.name == zero_match for f in c_files)
        
        if found_exact:
            print(f"  ✅ {ref}: Found as {exact_match}")
        elif found_zero:
            print(f"  ✅ {ref}: Found as {zero_match} (needs leading zero)")
        else:
            print(f"  ❌ {ref}: NOT FOUND (tried {exact_match} and {zero_match})")
    
    print("\n" + "="*70)
    print("RECOMMENDATION:")
    print("="*70)
    
    if len(single_digit_with_zero) > len(single_digit_no_zero):
        print("✅ Most single-digit files use leading zeros (C-01 format)")
        print("   The updated script will handle this automatically!")
    else:
        print("ℹ️  Files use mixed naming conventions")
        print("   The updated script tries both patterns")


if __name__ == "__main__":
    main()