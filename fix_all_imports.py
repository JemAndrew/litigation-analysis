#!/usr/bin/env python3
"""
Comprehensive Import Fixer
Analyses and fixes all import issues in the project
British English throughout
"""

from pathlib import Path
import re


def analyse_and_fix_file(file_path: Path) -> dict:
    """Analyse imports in a file and fix issues"""
    
    if not file_path.exists():
        return {'status': 'missing', 'issues': [], 'fixed': False}
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        issues = []
        
        # Check for relative imports
        relative_imports = re.findall(r'from \.\.?[\w.]+ import', content)
        if relative_imports:
            issues.append(f"Relative imports found: {len(relative_imports)}")
        
        # Fix patterns
        fixes = {
            # Fix double-dot relative imports
            r'from \.\.utils\.': 'from src.utils.',
            r'from \.\.prompts\.': 'from src.prompts.',
            r'from \.\.intelligence\.': 'from src.intelligence.',
            r'from \.\.core\.': 'from src.core.',
            
            # Fix single-dot relative imports
            r'from \.utils\.': 'from src.utils.',
            r'from \.prompts\.': 'from src.prompts.',
            r'from \.intelligence\.': 'from src.intelligence.',
            r'from \.core\.': 'from src.core.',
            
            # Fix absolute imports without src prefix
            r'\nfrom intelligence\.': '\nfrom src.intelligence.',
            r'\nfrom prompts\.': '\nfrom src.prompts.',
            r'\nfrom utils\.': '\nfrom src.utils.',
            r'\nfrom core\.': '\nfrom src.core.',
        }
        
        for pattern, replacement in fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                issues.append(f"Fixed: {pattern} -> {replacement}")
        
        # Add sys.path setup if missing and file is in src/
        if 'src' in str(file_path) and 'sys.path' not in content:
            # Find first import line
            lines = content.split('\n')
            insert_idx = None
            
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    if 'sys' not in line and 'Path' not in line:
                        insert_idx = i
                        break
            
            if insert_idx:
                sys_path_setup = [
                    '',
                    '# Add src to path for imports',
                    'import sys',
                    'from pathlib import Path',
                    'src_dir = Path(__file__).parent.parent if "src" in str(Path(__file__).parent) else Path(__file__).parent',
                    'if str(src_dir) not in sys.path:',
                    '    sys.path.insert(0, str(src_dir))',
                    '    sys.path.insert(0, str(src_dir.parent))',
                    ''
                ]
                
                for line in reversed(sys_path_setup):
                    lines.insert(insert_idx, line)
                
                content = '\n'.join(lines)
                issues.append("Added sys.path setup")
        
        # Write back if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return {'status': 'fixed', 'issues': issues, 'fixed': True}
        else:
            return {'status': 'ok', 'issues': [], 'fixed': False}
            
    except Exception as e:
        return {'status': 'error', 'issues': [str(e)], 'fixed': False}


def main():
    print("="*70)
    print("COMPREHENSIVE IMPORT ANALYSER & FIXER")
    print("="*70)
    print()
    
    project_root = Path.cwd()
    
    # Files to check
    files_to_check = [
        # Main entry points
        'review_folder_69.py',
        'chat.py',
        'chat_hybrid.py',
        
        # Core modules
        'src/core/case_manager.py',
        
        # Intelligence modules
        'src/intelligence/reviewer.py',
        'src/intelligence/vector_store.py',
        'src/intelligence/knowledge_graph.py',
        'src/intelligence/query_engine.py',
        
        # Prompts
        'src/prompts/analysis_prompt.py',
        'src/prompts/universal_forensic_prompts.py',
        
        # Utils
        'src/utils/document_loader.py',
    ]
    
    results = {
        'fixed': [],
        'ok': [],
        'missing': [],
        'error': []
    }
    
    for file_path_str in files_to_check:
        file_path = project_root / file_path_str
        
        print(f"📄 Checking: {file_path_str}")
        result = analyse_and_fix_file(file_path)
        
        if result['status'] == 'fixed':
            print(f"   ✅ FIXED")
            for issue in result['issues']:
                print(f"      • {issue}")
            results['fixed'].append(file_path_str)
        elif result['status'] == 'ok':
            print(f"   ✓ OK (no issues)")
            results['ok'].append(file_path_str)
        elif result['status'] == 'missing':
            print(f"   ⊘ File not found (skipping)")
            results['missing'].append(file_path_str)
        elif result['status'] == 'error':
            print(f"   ❌ ERROR")
            for issue in result['issues']:
                print(f"      • {issue}")
            results['error'].append(file_path_str)
        
        print()
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print(f"✅ Fixed:   {len(results['fixed'])} files")
    print(f"✓  OK:      {len(results['ok'])} files")
    print(f"⊘  Missing: {len(results['missing'])} files")
    print(f"❌ Errors:  {len(results['error'])} files")
    print()
    
    if results['fixed']:
        print("📝 Fixed files:")
        for f in results['fixed']:
            print(f"   • {f}")
        print()
    
    if results['error']:
        print("⚠️  Files with errors:")
        for f in results['error']:
            print(f"   • {f}")
        print()
    
    print("="*70)
    print()
    
    if results['fixed'] or results['error']:
        print("🎯 Next steps:")
        print("   1. Review changes above")
        print("   2. Run: python review_folder_69.py")
        print("   3. If errors persist, check specific files manually")
    else:
        print("✅ All imports are correct! You're good to go.")
        print()
        print("Run: python review_folder_69.py")
    
    print()


if __name__ == '__main__':
    main()