#!/usr/bin/env python3
"""
Auto-fix Import Paths
Fixes all import issues in the project
British English throughout
"""

from pathlib import Path
import re


def fix_file_imports(file_path: Path) -> bool:
    """Fix imports in a single file"""
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Fix patterns
        fixes = [
            # Fix: from intelligence. → from src.intelligence.
            (r'from intelligence\.', 'from src.intelligence.'),
            
            # Fix: from prompts. → from src.prompts.
            (r'from prompts\.', 'from src.prompts.'),
            
            # Fix: from utils. → from src.utils.
            (r'from utils\.', 'from src.utils.'),
            
            # Fix: from core. → from src.core.
            (r'from core\.', 'from src.core.'),
        ]
        
        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content)
        
        # Write back if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ Error fixing {file_path.name}: {e}")
        return False


def add_sys_path_to_file(file_path: Path) -> bool:
    """Add sys.path setup to file if needed"""
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if already has sys.path setup
        if 'sys.path.insert' in content and 'project_root' in content:
            return False  # Already fixed
        
        # Find the imports section
        lines = content.split('\n')
        
        # Find first import statement
        import_line_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                if 'sys' not in line and 'pathlib' not in line:
                    import_line_idx = i
                    break
        
        if import_line_idx is None:
            return False
        
        # Insert sys.path setup before imports
        sys_path_setup = [
            '',
            '# Setup paths for imports',
            'import sys',
            'from pathlib import Path',
            '',
            'project_root = Path(__file__).parent.parent.parent if "src" in str(Path(__file__)) else Path(__file__).parent',
            'sys.path.insert(0, str(project_root))',
            'sys.path.insert(0, str(project_root / "src"))',
            ''
        ]
        
        # Insert at import location
        for line in reversed(sys_path_setup):
            lines.insert(import_line_idx, line)
        
        # Write back
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        return True
        
    except Exception as e:
        print(f"   ❌ Error adding sys.path to {file_path.name}: {e}")
        return False


def main():
    print("="*70)
    print("IMPORT PATH FIXER")
    print("="*70)
    print("\nThis will automatically fix all import path issues.\n")
    
    project_root = Path.cwd()
    
    # Files to fix
    files_to_fix = [
        'review_folder_69.py',
        'src/intelligence/reviewer.py',
        'src/intelligence/vector_store.py',
        'src/intelligence/knowledge_graph.py',
        'src/intelligence/query_engine.py',
        'src/prompts/analysis_prompt.py',
        'src/utils/document_loader.py',
        'chat.py',
        'chat_hybrid.py'
    ]
    
    fixed_count = 0
    
    for file_path_str in files_to_fix:
        file_path = project_root / file_path_str
        
        if not file_path.exists():
            print(f"⊘ Skipping {file_path_str} (doesn't exist)")
            continue
        
        print(f"\n🔧 Fixing: {file_path_str}")
        
        # Fix import statements
        if fix_file_imports(file_path):
            print(f"   ✅ Fixed import paths")
            fixed_count += 1
        else:
            print(f"   ✓ Import paths already correct")
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\n✅ Fixed {fixed_count} files")
    print("\n💡 Now try running:")
    print("   python review_folder_69.py")
    print("\n")


if __name__ == '__main__':
    main()