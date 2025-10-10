#!/usr/bin/env python3
"""
Match Excel Files - Doc IDs with Descriptions
British English throughout
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import re


def match_excel_files():
    """Match List of Documents with Trial Bundle Index"""
    
    print("="*70)
    print("EXCEL MATCHER")
    print("="*70)
    
    # Paths
    project_root = Path.cwd()
    list_file = project_root / "List of Documents Received from PHL on 15.09.25  Draft 1  16.09.25.xlsx"
    bundle_file = project_root / "Trial Bundle Index  Excel  Draft 2  29.09.25.xlsx"
    output_dir = project_root / "cases" / "lismore_v_ph" / "analysis" / "folder_69_review"
    
    # Check files
    if not list_file.exists():
        print(f"\n❌ Not found: {list_file.name}")
        return
    
    if not bundle_file.exists():
        print(f"\n❌ Not found: {bundle_file.name}")
        return
    
    # Load files
    print(f"\n📄 Loading files...")
    df_list = pd.read_excel(list_file)
    df_bundle = pd.read_excel(bundle_file)
    
    print(f"   List of Documents: {len(df_list)} rows")
    print(f"   Trial Bundle: {len(df_bundle)} rows")
    
    print(f"\n   List columns: {list(df_list.columns)}")
    print(f"   Bundle columns: {list(df_bundle.columns)}")
    
    # Find tab column in bundle
    tab_col = None
    for col in df_bundle.columns:
        if 'tab' in str(col).lower() or 'disclosure' in str(col).lower():
            tab_col = col
            break
    
    if not tab_col:
        print("\n⚠️  Could not find Tab column")
        print("Available columns:", list(df_bundle.columns))
        tab_col = input("Enter tab column name: ").strip()
    
    print(f"\n   Using tab column: {tab_col}")
    
    # Create Doc IDs
    print(f"\n🔧 Creating Doc IDs...")
    df_bundle['Doc_ID'] = None
    
    for tab in df_bundle[tab_col].unique():
        if pd.isna(tab):
            continue
        
        tab_clean = re.sub(r'[^0-9]', '', str(tab))
        if not tab_clean:
            continue
        
        tab_mask = df_bundle[tab_col] == tab
        tab_indices = df_bundle[tab_mask].index
        
        for seq_num, idx in enumerate(tab_indices, start=1):
            doc_id = f"Bundle_Tab_{tab_clean}_{seq_num:03d}"
            df_bundle.at[idx, 'Doc_ID'] = doc_id
    
    created = df_bundle['Doc_ID'].notna().sum()
    print(f"   ✅ Created {created} Doc IDs")
    
    # Find description columns
    doc_name_col = None
    date_col = None
    pages_col = None
    
    for col in df_bundle.columns:
        col_lower = str(col).lower()
        if 'document' in col_lower and 'name' in col_lower:
            doc_name_col = col
        elif 'date' in col_lower:
            date_col = col
        elif 'page' in col_lower:
            pages_col = col
    
    # Create output
    output_data = []
    for _, row in df_bundle.iterrows():
        if pd.notna(row.get('Doc_ID')):
            output_data.append({
                'Doc ID': row['Doc_ID'],
                'Document Name': row.get(doc_name_col, '') if doc_name_col else '',
                'Date': row.get(date_col, '') if date_col else '',
                'Pages': row.get(pages_col, '') if pages_col else ''
            })
    
    df_output = pd.DataFrame(output_data)
    
    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"Matched_Documents_{timestamp}.xlsx"
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df_output.to_excel(writer, sheet_name='Matched', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Matched']
        
        # Header format
        header_fmt = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white'
        })
        
        for col_num, value in enumerate(df_output.columns):
            worksheet.write(0, col_num, value, header_fmt)
        
        # Column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 70)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 10)
    
    print(f"\n✅ SUCCESS!")
    print(f"   Output: {output_file.name}")
    print(f"   Documents: {len(df_output)}")
    print(f"\n💡 Next: Run review_folder_69.py")


if __name__ == '__main__':
    match_excel_files()