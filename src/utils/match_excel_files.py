#!/usr/bin/env python3
"""
Trial Bundle Index - Disclosure ID Generator
Parses Excel and creates Disclosure IDs in format: {Bundle}_{Tab}

British English throughout
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import re


def find_header_row(df: pd.DataFrame) -> int:
    """Find the actual header row in Excel file"""
    print("\n🔍 Scanning for header row...")
    
    for row_idx in range(min(10, len(df))):
        row = df.iloc[row_idx]
        non_empty = row.notna().sum()
        row_text = ' '.join([str(x).lower() for x in row if pd.notna(x)])
        
        header_keywords = ['tab', 'document', 'description', 'name', 'date', 'page', 'disclosure', 'bundle']
        keyword_matches = sum(1 for kw in header_keywords if kw in row_text)
        
        if non_empty >= 3 and keyword_matches >= 2:
            print(f"   ✅ Found headers at row {row_idx}")
            return row_idx
    
    print("   ⚠️  Could not auto-detect header row, using row 0")
    return 0


def load_excel_intelligently(file_path: Path) -> pd.DataFrame:
    """Load Excel with intelligent header detection"""
    print(f"\n📄 Loading: {file_path.name}")
    
    # Load raw to inspect
    df_raw = pd.read_excel(file_path, header=None)
    print(f"   Raw shape: {df_raw.shape[0]} rows × {df_raw.shape[1]} columns")
    
    # Find header row
    header_row = find_header_row(df_raw)
    
    # Reload with correct header
    df = pd.read_excel(file_path, header=header_row, engine='openpyxl')
    df.columns = [str(col).strip() for col in df.columns]
    df = df.dropna(how='all')
    
    print(f"   ✅ Loaded: {len(df)} rows × {len(df.columns)} columns")
    print(f"   Columns: {list(df.columns)[:5]}{'...' if len(df.columns) > 5 else ''}")
    
    return df


def preview_dataframe(df: pd.DataFrame, name: str, n: int = 5):
    """Show preview of DataFrame"""
    print(f"\n{'='*70}")
    print(f"PREVIEW: {name}")
    print(f"{'='*70}")
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst {n} rows:")
    print(df.head(n).to_string())
    print()


def find_column_interactive(df: pd.DataFrame, purpose: str, keywords: list) -> str:
    """Find column interactively with smart detection"""
    print(f"\n🔍 Looking for {purpose} column...")
    
    # Try exact match first
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if col_lower in keywords:
            print(f"   ✅ Auto-detected: '{col}' (exact match)")
            confirm = input(f"   Use this column? (y/n): ").lower()
            if confirm == 'y':
                return col
    
    # Manual selection
    print(f"\n   💡 Please select the correct column manually")
    print(f"\n   Available columns:")
    
    for i, col in enumerate(df.columns, 1):
        sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else "N/A"
        print(f"      {i}. {col}")
        print(f"         Example: {sample}")
    
    while True:
        choice = input(f"\n   Select column number (1-{len(df.columns)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(df.columns):
                selected = df.columns[idx]
                print(f"   ✅ Selected: '{selected}'")
                return selected
            else:
                print(f"   ❌ Invalid number. Must be 1-{len(df.columns)}")
        except ValueError:
            print("   ❌ Invalid input. Enter a number.")


def create_disclosure_ids(df: pd.DataFrame, bundle_column: str, tab_column: str) -> pd.DataFrame:
    """
    Create Disclosure IDs from Bundle + Tab
    
    Format: {BUNDLE}_{TAB}
    Example: AA_1, AA_1.1, BB_12
    """
    print(f"\n🔧 Creating Disclosure IDs")
    print(f"   Bundle column: '{bundle_column}'")
    print(f"   Tab column: '{tab_column}'")
    
    # Create Disclosure ID by combining Bundle + "_" + Tab
    df['Disclosure_ID'] = df[bundle_column].astype(str) + "_" + df[tab_column].astype(str)
    
    # Clean up any NaN combinations
    df.loc[df['Disclosure_ID'].str.contains('nan', case=False, na=False), 'Disclosure_ID'] = None
    
    created_count = df['Disclosure_ID'].notna().sum()
    unique_count = df['Disclosure_ID'].nunique()
    
    print(f"   ✅ Created {created_count} Disclosure IDs")
    print(f"   📊 {unique_count} unique IDs")
    
    return df


def extract_all_columns(df: pd.DataFrame, bundle_column: str, tab_column: str) -> pd.DataFrame:
    """Extract all relevant columns for output"""
    print("\n📋 Extracting all columns...")
    
    # Find Document Name column
    doc_name_col = find_column_interactive(
        df, 
        "Document Name/Description",
        ['document name', 'document', 'description', 'name']
    )
    
    # Find Date column
    date_col = find_column_interactive(
        df,
        "Date",
        ['date', 'dated']
    )
    
    # Optional: Pages column
    pages_col = None
    if input("\n   Does file have a Pages column? (y/n): ").lower() == 'y':
        pages_col = find_column_interactive(
            df,
            "Pages",
            ['pages', 'page']
        )
    
    # Create output DataFrame
    output_data = []
    
    for _, row in df.iterrows():
        if pd.notna(row.get('Disclosure_ID')):
            output_data.append({
                'Disclosure ID': row['Disclosure_ID'],
                'Bundle': row.get(bundle_column, ''),
                'Tab': row.get(tab_column, ''),
                'Document Name': row.get(doc_name_col, '') if doc_name_col else '',
                'Date': row.get(date_col, '') if date_col else '',
                'Pages': row.get(pages_col, '') if pages_col else ''
            })
    
    df_output = pd.DataFrame(output_data)
    print(f"\n   ✅ Extracted {len(df_output)} documents")
    
    return df_output


def save_output(df: pd.DataFrame, output_dir: Path):
    """Save output to formatted Excel"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"Trial_Bundle_With_Disclosure_IDs_{timestamp}.xlsx"
    
    print(f"\n💾 Saving to: {output_file.name}")
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Documents', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Documents']
        
        # Header format
        header_fmt = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Apply headers
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_fmt)
        
        # Column widths
        worksheet.set_column('A:A', 20)  # Disclosure ID
        worksheet.set_column('B:B', 12)  # Bundle
        worksheet.set_column('C:C', 12)  # Tab
        worksheet.set_column('D:D', 70)  # Document Name
        worksheet.set_column('E:E', 15)  # Date
        worksheet.set_column('F:F', 10)  # Pages
    
    print(f"   ✅ Saved successfully!")
    print(f"   Location: {output_file}")
    
    return output_file


def main():
    """Main execution"""
    
    print("="*70)
    print("TRIAL BUNDLE INDEX - DISCLOSURE ID GENERATOR")
    print("="*70)
    print("\nThis tool:")
    print("  ✓ Parses Trial Bundle Index Excel")
    print("  ✓ Creates Disclosure IDs: {Bundle}_{Tab}")
    print("  ✓ Extracts all relevant columns")
    print("\nExample Disclosure IDs:")
    print("  AA_1, AA_1.1, BB_12, CC_45.6")
    
    # File paths
    project_root = Path.cwd()
    downloads = Path.home() / "Downloads" / "To be discussed"
    bundle_file = downloads / "Trial Bundle Index - Excel - Draft 2 - 29.09.25.xlsx"
    
    # Check file exists
    if not bundle_file.exists():
        print(f"\n❌ Not found: {bundle_file}")
        bundle_file = Path(input("\n   Enter full path to Trial Bundle file: ").strip())
    
    try:
        # Load file
        print("\n" + "="*70)
        print("STEP 1: LOADING FILE")
        print("="*70)
        
        df_bundle = load_excel_intelligently(bundle_file)
        
        # Preview
        preview_dataframe(df_bundle, "Trial Bundle Index", n=3)
        
        if input("\nContinue? (y/n): ").lower() != 'y':
            print("Cancelled.")
            return
        
        # Find Bundle and Tab columns
        print("\n" + "="*70)
        print("STEP 2: SELECTING BUNDLE AND TAB COLUMNS")
        print("="*70)
        
        bundle_column = find_column_interactive(
            df_bundle,
            "Bundle (e.g., AA, BB, CC)",
            ['bundle']
        )
        
        tab_column = find_column_interactive(
            df_bundle,
            "Tab (e.g., 1, 1.1, 12)",
            ['tab']
        )
        
        # Create Disclosure IDs
        print("\n" + "="*70)
        print("STEP 3: CREATING DISCLOSURE IDs")
        print("="*70)
        
        df_bundle = create_disclosure_ids(df_bundle, bundle_column, tab_column)
        
        # Preview with retry
        ids_confirmed = False
        while not ids_confirmed:
            print("\nDisclosure ID examples:")
            print(df_bundle[['Disclosure_ID', bundle_column, tab_column]].dropna().head(15).to_string())
            
            confirm = input("\nDisclosure IDs look correct? (y/n/restart): ").lower()
            
            if confirm == 'y':
                ids_confirmed = True
            elif confirm == 'restart':
                print("\n🔄 Restarting column selection...")
                bundle_column = find_column_interactive(
                    df_bundle,
                    "Bundle (e.g., AA, BB, CC)",
                    ['bundle']
                )
                tab_column = find_column_interactive(
                    df_bundle,
                    "Tab (e.g., 1, 1.1, 12)",
                    ['tab']
                )
                df_bundle = create_disclosure_ids(df_bundle, bundle_column, tab_column)
            else:
                print("\n❌ Cancelled.")
                return
        
        # Extract all columns
        print("\n" + "="*70)
        print("STEP 4: EXTRACTING ALL COLUMNS")
        print("="*70)
        
        df_output = extract_all_columns(df_bundle, bundle_column, tab_column)
        
        # Preview output
        preview_dataframe(df_output, "Final Output", n=10)
        
        if input("\nSave this output? (y/n): ").lower() != 'y':
            print("Cancelled.")
            return
        
        # Save
        print("\n" + "="*70)
        print("STEP 5: SAVING OUTPUT")
        print("="*70)
        
        output_dir = project_root / "cases" / "lismore_v_ph" / "analysis" / "folder_69_review"
        output_file = save_output(df_output, output_dir)
        
        # Success
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   Documents: {len(df_output)}")
        print(f"   Unique Disclosure IDs: {df_output['Disclosure ID'].nunique()}")
        print(f"   Output: {output_file.name}")
        print(f"\n📋 Output columns:")
        print(f"   • Disclosure ID (AA_1 format)")
        print(f"   • Bundle")
        print(f"   • Tab")
        print(f"   • Document Name")
        print(f"   • Date")
        print(f"   • Pages")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()