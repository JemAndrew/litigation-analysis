#!/usr/bin/env python3
"""
Complete Import & Class Name Fixer
Fixes all imports and class references across the entire project
British English throughout
"""

from pathlib import Path
import re


# =============================================================================
# DEFINITIVE CLASS NAME MAPPING
# =============================================================================

CLASS_NAME_FIXES = {
    # Old name (WRONG) -> New name (CORRECT)
    'EnhancedVectorStore': 'VectorStore',
    'EnhancedFolder69Reviewer': 'Folder69Reviewer',
    'EnhancedDocumentScore': 'DocumentScore',
}

# =============================================================================
# DEFINITIVE IMPORT MAPPING
# =============================================================================

CORRECT_IMPORTS = {
    # Class name -> Correct import statement
    'CaseManager': 'from src.core.case_manager import CaseManager',
    'CaseMetadata': 'from src.core.case_manager import CaseMetadata',
    'VectorStore': 'from src.intelligence.vector_store import VectorStore',
    'CumulativeKnowledgeGraph': 'from src.intelligence.knowledge_graph import CumulativeKnowledgeGraph',
    'QueryEngine': 'from src.intelligence.query_engine import QueryEngine',
    'QueryResult': 'from src.intelligence.query_engine import QueryResult',
    'Folder69Reviewer': 'from src.intelligence.reviewer import Folder69Reviewer',
    'DocumentScore': 'from src.intelligence.reviewer import DocumentScore',
    'AnalysisPrompts': 'from src.prompts.analysis_prompt import AnalysisPrompts',
    'UniversalForensicPrompts': 'from src.prompts.universal_forensic_prompts import UniversalForensicPrompts',
    'ForensicPrompts': 'from src.prompts.universal_forensic_prompts import ForensicPrompts',
    'DocumentLoader': 'from src.utils.document_loader import DocumentLoader',
}

# =============================================================================
# FILES TO PROCESS
# =============================================================================

FILES_TO_FIX = [
    # Entry points
    'review_folder_69.py',
    'chat.py',
    'chat_hybrid.py',
    
    # Core
    'src/core/case_manager.py',
    
    # Intelligence
    'src/intelligence/vector_store.py',
    'src/intelligence/knowledge_graph.py',
    'src/intelligence/query_engine.py',
    'src/intelligence/reviewer.py',
    
    # Prompts
    'src/prompts/analysis_prompt.py',
    'src/prompts/universal_forensic_prompts.py',
    
    # Utils
    'src/utils/document_loader.py',
]


def fix_class_names(content: str) -> tuple[str, list]:
    """
    Fix all class name references in content
    
    Args:
        content: File content
        
    Returns:
        Tuple of (fixed_content, list_of_changes)
    """
    changes = []
    
    for old_name, new_name in CLASS_NAME_FIXES.items():
        # Fix class definitions
        pattern = rf'class {old_name}\('
        if re.search(pattern, content):
            content = re.sub(pattern, f'class {new_name}(', content)
            changes.append(f"Class definition: {old_name} → {new_name}")
        
        # Fix class instantiations
        pattern = rf'\b{old_name}\('
        if re.search(pattern, content):
            content = re.sub(pattern, f'{new_name}(', content)
            changes.append(f"Class instantiation: {old_name}(...) → {new_name}(...)")
        
        # Fix import statements
        pattern = rf'from .+ import {old_name}'
        if re.search(pattern, content):
            content = re.sub(pattern, f'from \\g<1> import {new_name}', content)
            changes.append(f"Import: {old_name} → {new_name}")
    
    return content, changes


def fix_imports(content: str, file_path: Path) -> tuple[str, list]:
    """
    Fix import statements to use correct paths
    
    Args:
        content: File content
        file_path: Path to the file being fixed
        
    Returns:
        Tuple of (fixed_content, list_of_changes)
    """
    changes = []
    
    # Fix relative imports to absolute
    relative_import_patterns = [
        (r'from \.\.intelligence\.', 'from src.intelligence.'),
        (r'from \.\.prompts\.', 'from src.prompts.'),
        (r'from \.\.utils\.', 'from src.utils.'),
        (r'from \.\.core\.', 'from src.core.'),
        (r'from \.intelligence\.', 'from src.intelligence.'),
        (r'from \.prompts\.', 'from src.prompts.'),
        (r'from \.utils\.', 'from src.utils.'),
        (r'from \.core\.', 'from src.core.'),
    ]
    
    for pattern, replacement in relative_import_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes.append(f"Fixed relative import: {pattern} → {replacement}")
    
    # Fix incorrect absolute imports
    incorrect_imports = [
        (r'from intelligence\.', 'from src.intelligence.'),
        (r'from prompts\.', 'from src.prompts.'),
        (r'from utils\.', 'from src.utils.'),
        (r'from core\.', 'from src.core.'),
    ]
    
    for pattern, replacement in incorrect_imports:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes.append(f"Fixed incorrect import: {pattern} → {replacement}")
    
    return content, changes


def verify_imports(content: str) -> list:
    """
    Verify all imports are correct
    
    Args:
        content: File content
        
    Returns:
        List of potential issues
    """
    issues = []
    
    # Check for old class names in imports
    for old_name in CLASS_NAME_FIXES.keys():
        pattern = rf'from .+ import .*{old_name}'
        if re.search(pattern, content):
            issues.append(f"⚠️  Still importing old class name: {old_name}")
    
    # Check for relative imports
    if re.search(r'from \.\.|from \.', content):
        issues.append("⚠️  Relative imports still present")
    
    # Check for imports without 'src.' prefix (in root scripts)
    incorrect_patterns = [
        r'from intelligence\.',
        r'from prompts\.',
        r'from utils\.',
        r'from core\.',
    ]
    
    for pattern in incorrect_patterns:
        if re.search(pattern, content):
            issues.append(f"⚠️  Import without 'src.' prefix: {pattern}")
    
    return issues


def add_sys_path_setup(content: str, file_path: Path) -> tuple[str, bool]:
    """
    Add sys.path setup to files in src/ if missing
    
    Args:
        content: File content
        file_path: Path to file
        
    Returns:
        Tuple of (content, was_added)
    """
    # Only add to files in src/
    if 'src' not in str(file_path):
        return content, False
    
    # Check if already has sys.path setup
    if 'sys.path.insert' in content and 'src_dir' in content:
        return content, False
    
    # Find first import line
    lines = content.split('\n')
    insert_idx = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            # Skip if it's sys or pathlib import
            if 'sys' in line or 'pathlib' in line or 'Path' in line:
                continue
            insert_idx = i
            break
    
    if insert_idx is None:
        return content, False
    
    # Add sys.path setup
    setup_lines = [
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
    
    for line in reversed(setup_lines):
        lines.insert(insert_idx, line)
    
    return '\n'.join(lines), True


def fix_file(file_path: Path, project_root: Path) -> dict:
    """
    Fix all issues in a single file
    
    Args:
        file_path: Path to file
        project_root: Project root directory
        
    Returns:
        Dictionary with fix results
    """
    if not file_path.exists():
        return {'status': 'missing', 'changes': []}
    
    try:
        # Read file
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        all_changes = []
        
        # 1. Fix class names
        content, changes = fix_class_names(content)
        all_changes.extend(changes)
        
        # 2. Fix imports
        content, changes = fix_imports(content, file_path)
        all_changes.extend(changes)
        
        # 3. Add sys.path setup if needed
        content, was_added = add_sys_path_setup(content, file_path)
        if was_added:
            all_changes.append("Added sys.path setup")
        
        # 4. Verify imports
        issues = verify_imports(content)
        
        # Write back if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return {
                'status': 'fixed',
                'changes': all_changes,
                'issues': issues
            }
        else:
            return {
                'status': 'ok',
                'changes': [],
                'issues': issues
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'changes': [],
            'issues': []
        }


def main():
    """Main execution"""
    print("="*70)
    print("COMPLETE IMPORT & CLASS NAME FIXER")
    print("="*70)
    print()
    print("This script will:")
    print("  ✓ Fix all class names (remove 'Enhanced' prefix)")
    print("  ✓ Fix all import statements")
    print("  ✓ Fix relative imports to absolute")
    print("  ✓ Add sys.path setup where needed")
    print("  ✓ Verify all imports are correct")
    print()
    
    project_root = Path.cwd()
    
    # Process all files
    results = {
        'fixed': [],
        'ok': [],
        'missing': [],
        'error': []
    }
    
    for file_path_str in FILES_TO_FIX:
        file_path = project_root / file_path_str
        
        print(f"📄 Processing: {file_path_str}")
        
        result = fix_file(file_path, project_root)
        
        if result['status'] == 'fixed':
            print(f"   ✅ FIXED")
            for change in result['changes']:
                print(f"      • {change}")
            if result['issues']:
                print(f"   ⚠️  ISSUES:")
                for issue in result['issues']:
                    print(f"      • {issue}")
            results['fixed'].append(file_path_str)
        
        elif result['status'] == 'ok':
            print(f"   ✓ OK (no changes needed)")
            if result['issues']:
                print(f"   ⚠️  ISSUES:")
                for issue in result['issues']:
                    print(f"      • {issue}")
            results['ok'].append(file_path_str)
        
        elif result['status'] == 'missing':
            print(f"   ⊘ File not found (skipping)")
            results['missing'].append(file_path_str)
        
        elif result['status'] == 'error':
            print(f"   ❌ ERROR: {result['error']}")
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
    
    # Final verification
    print("="*70)
    print("VERIFICATION")
    print("="*70)
    print()
    print("Testing all imports...")
    
    test_script = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / 'src'))

try:
    from src.core.case_manager import CaseManager
    from src.intelligence.vector_store import VectorStore
    from src.intelligence.knowledge_graph import CumulativeKnowledgeGraph
    from src.intelligence.query_engine import QueryEngine
    from src.intelligence.reviewer import Folder69Reviewer
    from src.prompts.analysis_prompt import AnalysisPrompts
    from src.prompts.universal_forensic_prompts import UniversalForensicPrompts
    from src.utils.document_loader import DocumentLoader
    print('✅ All imports successful!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"""
    
    # Write test script
    test_file = project_root / 'test_imports.py'
    test_file.write_text(test_script)
    
    # Run test
    import subprocess
    try:
        result = subprocess.run(
            ['python', str(test_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
    except Exception as e:
        print(f"⚠️  Could not run verification: {e}")
    finally:
        # Clean up test file
        test_file.unlink()
    
    print()
    print("="*70)
    print()
    
    if results['fixed'] or results['error']:
        print("🎯 Next steps:")
        print("   1. Review changes above")
        print("   2. Run: python review_folder_69.py")
        print("   3. If errors persist, check specific files manually")
    else:
        print("✅ All imports are already correct!")
        print()
        print("You can now run: python review_folder_69.py")
    
    print()


if __name__ == '__main__':
    main()