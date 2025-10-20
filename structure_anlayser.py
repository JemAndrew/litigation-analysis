#!/usr/bin/env python3
"""
Simple Folder Overview
Just shows what folders exist and example files

British English throughout
"""

from pathlib import Path

def show_folder_overview(root_path: str):
    """
    Simple overview: folders, subfolders, example files
    """
    
    root = Path(root_path)
    
    if not root.exists():
        print(f"❌ Path not found: {root}")
        return
    
    print("="*80)
    print("📂 FOLDER OVERVIEW - LISMORE v PH DOCUMENTS")
    print("="*80)
    print(f"\nRoot: {root}\n")
    
    # Get all top-level folders
    top_folders = sorted([f for f in root.iterdir() if f.is_dir()])
    
    print(f"Found {len(top_folders)} main folders\n")
    print("="*80)
    
    for i, folder in enumerate(top_folders, 1):
        print(f"\n{i}. 📁 {folder.name}")
        print("   " + "-"*76)
        
        # Count files
        all_files = list(folder.rglob('*'))
        files = [f for f in all_files if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.doc', '.msg', '.eml', '.xlsx']]
        
        print(f"   Files: {len(files)}")
        
        # Show subfolders if any
        subfolders = [f for f in folder.iterdir() if f.is_dir()]
        if subfolders:
            print(f"   Subfolders: {len(subfolders)}")
            for subfolder in subfolders[:3]:  # Show first 3
                print(f"      └─ {subfolder.name}")
            if len(subfolders) > 3:
                print(f"      └─ ... and {len(subfolders)-3} more subfolders")
        
        # Show 5 example files
        if files:
            print(f"   \n   Example files:")
            for file in files[:5]:
                # Show relative path from folder
                rel_path = file.relative_to(folder)
                print(f"      • {rel_path}")
            if len(files) > 5:
                print(f"      • ... and {len(files)-5} more files")
        
        print()
    
    print("="*80)
    print(f"✅ Overview complete - {len(top_folders)} folders analysed")
    print("="*80)


if __name__ == '__main__':
    # Your path
    ROOT_PATH = r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1"
    
    show_folder_overview(ROOT_PATH)
