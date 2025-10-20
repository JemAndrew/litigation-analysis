#!/usr/bin/env python3
"""
Document Matcher - Enrich List of Documents with Trial Bundle Metadata

Matches Doc IDs (format: Bundle_Tab) from List of Documents Received
against Trial Bundle Index (Bundle + Tab columns) and adds metadata.

British English throughout.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import re


def find_header_row(df: pd.DataFrame, expected_columns: list) -> int:
    """
    Find actual header row in Excel (handles merged cells, empty rows)
    
    Args:
        df: Raw DataFrame
        expected_columns: Keywords to look for in headers
        
    Returns:
        Index of header row
    """
    print("\n🔍 Scanning for header row...")
    
    for row_idx in range(min(15, len(df))):
        row = df.iloc[row_idx]
        row_text = ' '.join([str(x).lower() for x in row if pd.notna(x)])
        
        # Count matches
        matches = sum(1 for col in expected_columns if col.lower() in row_text)
        
        if matches >= 2:
            print(f"   ✅ Found headers at row {row_idx}")
            return row_idx
    
    print("   ⚠️  Auto-detection failed, using row 0")
    return 0


def load_trial_bundle_index(file_path: Path) -> pd.DataFrame:
    """
    Load Trial Bundle Index with intelligent header detection
    
    Expected columns: Bundle, Tab, Description/Document Name, Date, Pages
    """
    print(f"\n📄 Loading Trial Bundle Index: {file_path.name}")
    
    # Load raw
    df_raw = pd.read_excel(file_path, header=None)
    print(f"   Raw shape: {df_raw.shape[0]} rows × {df_raw.shape[1]} columns")
    
    # Find header row
    expected_cols = ['bundle', 'tab', 'document', 'description', 'date', 'page']
    header_row = find_header_row(df_raw, expected_cols)
    
    # Reload with correct header
    df = pd.read_excel(file_path, header=header_row)
    df.columns = [str(col).strip() for col in df.columns]
    df = df.dropna(how='all')
    
    print(f"   ✅ Loaded: {len(df)} rows")
    print(f"   Columns: {list(df.columns)[:8]}{'...' if len(df.columns) > 8 else ''}")
    
    return df


def load_list_of_documents_received(file_path: Path) -> pd.DataFrame:
    """
    Load List of Documents Received
    
    Expected column: Doc ID (format: Bundle_Tab, e.g., AA_1)
    """
    print(f"\n📄 Loading List of Documents Received: {file_path.name}")
    
    # Load raw
    df_raw = pd.read_excel(file_path, header=None)
    print(f"   Raw shape: {df_raw.shape[0]} rows × {df_raw.shape[1]} columns")
    
    # Find header row
    expected_cols = ['doc id', 'document id', 'bundle', 'tab']
    header_row = find_header_row(df_raw, expected_cols)
    
    # Reload with correct header
    df = pd.read_excel(file_path, header=header_row)
    df.columns = [str(col).strip() for col in df.columns]
    df = df.dropna(how='all')
    
    print(f"   ✅ Loaded: {len(df)} rows")
    print(f"   Columns: {list(df.columns)}")
    
    return df


def identify_columns_interactive(df: pd.DataFrame, purpose: str, keywords: list) -> str:
    """
    Identify column interactively with smart suggestions
    
    Args:
        df: DataFrame
        purpose: What we're looking for (e.g., "Bundle column")
        keywords: Keywords to search for
        
    Returns:
        Selected column name
    """
    print(f"\n🔍 Identifying {purpose}...")
    
    # Try automatic detection
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if any(keyword in col_lower for keyword in keywords):
            print(f"   ✅ Auto-detected: '{col}'")
            confirm = input(f"   Use this column? (y/n): ").lower()
            if confirm == 'y':
                return col
    
    # Manual selection
    print(f"\n   💡 Please select manually:")
    for i, col in enumerate(df.columns, 1):
        sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else "N/A"
        print(f"      {i}. {col}")
        print(f"         Example: {sample}")
    
    while True:
        choice = input(f"\n   Select column (1-{len(df.columns)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(df.columns):
                selected = df.columns[idx]
                print(f"   ✅ Selected: '{selected}'")
                return selected
        except ValueError:
            pass
        print(f"   ❌ Invalid. Enter 1-{len(df.columns)}")


def split_doc_id(doc_id: str) -> tuple:
    """
    Split Doc ID into Bundle and Tab
    
    Handles formats:
    - AA_1 → ("AA", "1")
    - BB_12.5 → ("BB", "12.5")
    - CC_3a → ("CC", "3a")
    
    Args:
        doc_id: Document ID (e.g., "AA_1")
        
    Returns:
        Tuple of (bundle, tab)
    """
    if pd.isna(doc_id) or str(doc_id).strip() == '':
        return (None, None)
    
    doc_id_str = str(doc_id).strip()
    
    # Split on underscore
    if '_' in doc_id_str:
        parts = doc_id_str.split('_', 1)
        return (parts[0].strip(), parts[1].strip())
    
    # No underscore - try to infer
    # Assume format: [Letters][Numbers/Dots]
    match = re.match(r'^([A-Za-z]+)[\s_-]?(.+)$', doc_id_str)
    if match:
        return (match.group(1), match.group(2))
    
    return (None, None)


def match_documents(trial_bundle_df: pd.DataFrame,
                   list_df: pd.DataFrame,
                   bundle_col_tb: str,
                   tab_col_tb: str,
                   doc_id_col_list: str,
                   description_col_tb: str,
                   date_col_tb: str,
                   pages_col_tb: str) -> pd.DataFrame:
    """
    Match documents and enrich List with metadata from Trial Bundle
    
    Args:
        trial_bundle_df: Trial Bundle Index DataFrame
        list_df: List of Documents Received DataFrame
        bundle_col_tb: Bundle column name in Trial Bundle
        tab_col_tb: Tab column name in Trial Bundle
        doc_id_col_list: Doc ID column name in List
        description_col_tb: Description column in Trial Bundle
        date_col_tb: Date column in Trial Bundle
        pages_col_tb: Pages column in Trial Bundle
        
    Returns:
        Enriched DataFrame
    """
    print(f"\n{'='*70}")
    print("MATCHING DOCUMENTS")
    print(f"{'='*70}\n")
    
    # Prepare Trial Bundle lookup
    print("🔧 Building lookup index from Trial Bundle...")
    
    # Create composite key: Bundle_Tab
    trial_bundle_df['_lookup_key'] = (
        trial_bundle_df[bundle_col_tb].astype(str).str.strip().str.upper() + '_' +
        trial_bundle_df[tab_col_tb].astype(str).str.strip()
    )
    
    # Create lookup dictionary
    lookup = {}
    for _, row in trial_bundle_df.iterrows():
        key = row['_lookup_key']
        lookup[key] = {
            'Description': row.get(description_col_tb, ''),
            'Date': row.get(date_col_tb, ''),
            'Pages': row.get(pages_col_tb, '')
        }
    
    print(f"   ✅ Indexed {len(lookup):,} documents from Trial Bundle")
    
    # Match each document in List
    print(f"\n🔍 Matching {len(list_df):,} documents from List...")
    
    enriched_data = []
    matched_count = 0
    unmatched_count = 0
    unmatched_ids = []
    
    for _, row in list_df.iterrows():
        doc_id = row.get(doc_id_col_list, '')
        
        # Split into Bundle + Tab
        bundle, tab = split_doc_id(doc_id)
        
        if not bundle or not tab:
            unmatched_count += 1
            unmatched_ids.append(str(doc_id))
            enriched_data.append({
                'Doc ID': doc_id,
                'Bundle': '',
                'Tab': '',
                'Description': 'ERROR: Could not parse Doc ID',
                'Date': '',
                'Pages': '',
                'Match Status': 'PARSE ERROR'
            })
            continue
        
        # Create lookup key
        lookup_key = f"{bundle.upper()}_{tab}"
        
        # Try to find match
        if lookup_key in lookup:
            matched_count += 1
            metadata = lookup[lookup_key]
            
            enriched_data.append({
                'Doc ID': doc_id,
                'Bundle': bundle,
                'Tab': tab,
                'Description': metadata['Description'],
                'Date': metadata['Date'],
                'Pages': metadata['Pages'],
                'Match Status': 'MATCHED'
            })
        else:
            unmatched_count += 1
            unmatched_ids.append(str(doc_id))
            
            enriched_data.append({
                'Doc ID': doc_id,
                'Bundle': bundle,
                'Tab': tab,
                'Description': 'NOT FOUND IN TRIAL BUNDLE',
                'Date': '',
                'Pages': '',
                'Match Status': 'NOT FOUND'
            })
    
    # Create enriched DataFrame
    enriched_df = pd.DataFrame(enriched_data)
    
    # Results
    print(f"\n{'='*70}")
    print("MATCHING RESULTS")
    print(f"{'='*70}")
    print(f"\n✅ Matched: {matched_count:,} / {len(list_df):,} ({matched_count/len(list_df)*100:.1f}%)")
    print(f"❌ Unmatched: {unmatched_count:,} / {len(list_df):,} ({unmatched_count/len(list_df)*100:.1f}%)")
    
    if unmatched_count > 0 and unmatched_count <= 20:
        print(f"\n⚠️  Unmatched Doc IDs:")
        for doc_id in unmatched_ids:
            print(f"   • {doc_id}")
    elif unmatched_count > 20:
        print(f"\n⚠️  {unmatched_count} unmatched Doc IDs (too many to display)")
        print(f"   See output Excel for full list")
    
    return enriched_df


def export_enriched_excel(df: pd.DataFrame, output_path: Path):
    """
    Export enriched DataFrame to Excel with formatting
    
    Args:
        df: Enriched DataFrame
        output_path: Output file path
    """
    print(f"\n{'='*70}")
    print("EXPORTING ENRICHED EXCEL")
    print(f"{'='*70}\n")
    
    print(f"💾 Saving to: {output_path.name}")
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Enriched Documents', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Enriched Documents']
        
        # Formats
        header_fmt = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'text_wrap': True
        })
        
        matched_fmt = workbook.add_format({'bg_color': '#C6EFCE'})
        unmatched_fmt = workbook.add_format({'bg_color': '#FFC7CE'})
        wrap_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top'})
        
        # Apply header format
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_fmt)
        
        # Set column widths
        worksheet.set_column('A:A', 15)  # Doc ID
        worksheet.set_column('B:B', 10)  # Bundle
        worksheet.set_column('C:C', 10)  # Tab
        worksheet.set_column('D:D', 70)  # Description
        worksheet.set_column('E:E', 12)  # Date
        worksheet.set_column('F:F', 10)  # Pages
        worksheet.set_column('G:G', 15)  # Match Status
        
        # Apply match status colours
        match_col = df.columns.get_loc('Match Status')
        for row_num, status in enumerate(df['Match Status'], start=1):
            if status == 'MATCHED':
                worksheet.write(row_num, match_col, status, matched_fmt)
            else:
                worksheet.write(row_num, match_col, status, unmatched_fmt)
        
        # Wrap text in Description
        desc_col = df.columns.get_loc('Description')
        for row_num in range(1, len(df) + 1):
            cell_value = df.iloc[row_num - 1]['Description']
            worksheet.write(row_num, desc_col, cell_value, wrap_fmt)
    
    print(f"   ✅ Excel saved: {output_path}")


def main():
    """Main execution"""
    
    print("="*70)
    print("DOCUMENT MATCHER - TRIAL BUNDLE ENRICHMENT")
    print("="*70)
    print("\nThis tool:")
    print("  ✓ Loads Trial Bundle Index (Bundle + Tab columns)")
    print("  ✓ Loads List of Documents Received (Doc ID column)")
    print("  ✓ Matches Doc IDs (Bundle_Tab format)")
    print("  ✓ Enriches List with Description, Date, Pages")
    print("  ✓ Exports complete spreadsheet\n")
    
    # File paths - YOUR ACTUAL FILES
    downloads = Path(r"C:\Users\JemAndrew\Downloads\To be discussed")
    
    trial_bundle_file = downloads / "Trial Bundle Index - Excel - Draft 2 - 29.09.25.xlsx"
    list_docs_file = downloads / "List of Documents Received from PHL on 15.09.25 - Draft 1 - 16.09.25.xlsx"
    
    output_dir = Path.cwd() / "cases" / "lismore_v_ph" / "analysis" / "folder_69_review"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check files exist
    if not trial_bundle_file.exists():
        print(f"❌ Trial Bundle Index not found: {trial_bundle_file}")
        trial_bundle_file = Path(input("\nEnter path to Trial Bundle Index: ").strip())
    
    if not list_docs_file.exists():
        print(f"❌ List of Documents not found: {list_docs_file}")
        list_docs_file = Path(input("\nEnter path to List of Documents: ").strip())
    
    try:
        # Load files
        print(f"\n{'='*70}")
        print("STEP 1: LOADING FILES")
        print(f"{'='*70}")
        
        trial_bundle_df = load_trial_bundle_index(trial_bundle_file)
        list_df = load_list_of_documents_received(list_docs_file)
        
        # Identify columns in Trial Bundle
        print(f"\n{'='*70}")
        print("STEP 2: IDENTIFY TRIAL BUNDLE COLUMNS")
        print(f"{'='*70}")
        
        bundle_col_tb = identify_columns_interactive(
            trial_bundle_df,
            "Bundle column (e.g., AA, BB, CC)",
            ['bundle']
        )
        
        tab_col_tb = identify_columns_interactive(
            trial_bundle_df,
            "Tab column (e.g., 1, 1.1, 12)",
            ['tab']
        )
        
        description_col_tb = identify_columns_interactive(
            trial_bundle_df,
            "Description/Document Name column",
            ['description', 'document name', 'document', 'name']
        )
        
        date_col_tb = identify_columns_interactive(
            trial_bundle_df,
            "Date column",
            ['date', 'dated']
        )
        
        pages_col_tb = identify_columns_interactive(
            trial_bundle_df,
            "Pages column",
            ['page', 'pages']
        )
        
        # Identify Doc ID column in List
        print(f"\n{'='*70}")
        print("STEP 3: IDENTIFY DOC ID COLUMN IN LIST")
        print(f"{'='*70}")
        
        doc_id_col_list = identify_columns_interactive(
            list_df,
            "Doc ID column (format: Bundle_Tab)",
            ['doc id', 'document id', 'id']
        )
        
        # Preview
        print(f"\n{'='*70}")
        print("PREVIEW")
        print(f"{'='*70}\n")
        
        print("Trial Bundle Index (first 3 rows):")
        print(trial_bundle_df[[bundle_col_tb, tab_col_tb, description_col_tb]][:3].to_string())
        
        print(f"\nList of Documents (first 5 rows):")
        print(list_df[[doc_id_col_list]][:5].to_string())
        
        # Confirm
        confirm = input("\n✅ Proceed with matching? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Cancelled.")
            return
        
        # Match documents
        print(f"\n{'='*70}")
        print("STEP 4: MATCHING DOCUMENTS")
        print(f"{'='*70}")
        
        enriched_df = match_documents(
            trial_bundle_df=trial_bundle_df,
            list_df=list_df,
            bundle_col_tb=bundle_col_tb,
            tab_col_tb=tab_col_tb,
            doc_id_col_list=doc_id_col_list,
            description_col_tb=description_col_tb,
            date_col_tb=date_col_tb,
            pages_col_tb=pages_col_tb
        )
        
        # Preview enriched data
        print(f"\n{'='*70}")
        print("PREVIEW ENRICHED DATA")
        print(f"{'='*70}\n")
        
        print("First 10 rows:")
        print(enriched_df[['Doc ID', 'Bundle', 'Tab', 'Description', 'Match Status']][:10].to_string())
        
        # Export
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"Enriched_List_of_Documents_{timestamp}.xlsx"
        
        export_enriched_excel(enriched_df, output_file)
        
        # Success
        print(f"\n{'='*70}")
        print("✅ SUCCESS!")
        print(f"{'='*70}\n")
        
        print(f"📊 Summary:")
        print(f"   Total documents: {len(enriched_df):,}")
        print(f"   Matched: {len(enriched_df[enriched_df['Match Status'] == 'MATCHED']):,}")
        print(f"   Unmatched: {len(enriched_df[enriched_df['Match Status'] != 'MATCHED']):,}")
        print(f"\n📂 Output: {output_file}")
        print(f"\n💡 Open Excel to review enriched documents!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()