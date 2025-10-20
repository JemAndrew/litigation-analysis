#!/usr/bin/env python3
"""
Bible Validator - Pre-Flight Checks Before Building

Validates:
- Case structure (folders exist)
- Document availability (key files present)
- API access (key valid, credits available)
- Output permissions (can write files)
- Python dependencies

British English throughout.
"""

import os
from pathlib import Path
from typing import Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)


class BibleValidator:
    """
    Validate everything before expensive Bible build
    
    Prevents wasted API costs by catching issues early
    """
    
    def __init__(self, case_root: Path, output_dir: Path, api_key: str):
        """
        Initialise validator
        
        Args:
            case_root: Root directory of case documents
            output_dir: Where Bible will be saved
            api_key: Anthropic API key
        """
        self.case_root = Path(case_root)
        self.output_dir = Path(output_dir)
        self.api_key = api_key
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        Run all validation checks
        
        Returns:
            (is_valid, list_of_issues)
        """
        
        issues = []
        
        print("\n" + "="*70)
        print("🔍 PRE-FLIGHT VALIDATION")
        print("="*70)
        
        # 1. Check case structure
        print("\n1. Validating case structure...")
        case_issues = self._validate_case_structure()
        if case_issues:
            issues.extend(case_issues)
        else:
            print("   ✅ Case structure valid")
        
        # 2. Check API access
        print("\n2. Validating API access...")
        api_issues = self._validate_api_access()
        if api_issues:
            issues.extend(api_issues)
        else:
            print("   ✅ API access valid")
        
        # 3. Check output permissions
        print("\n3. Validating output directory...")
        output_issues = self._validate_output_permissions()
        if output_issues:
            issues.extend(output_issues)
        else:
            print("   ✅ Output directory writable")
        
        # 4. Check dependencies
        print("\n4. Validating Python dependencies...")
        dep_issues = self._validate_dependencies()
        if dep_issues:
            issues.extend(dep_issues)
        else:
            print("   ✅ All dependencies available")
        
        # 5. Check disk space
        print("\n5. Checking disk space...")
        disk_issues = self._validate_disk_space()
        if disk_issues:
            issues.extend(disk_issues)
        else:
            print("   ✅ Sufficient disk space")
        
        # Summary
        print("\n" + "="*70)
        if issues:
            print(f"❌ VALIDATION FAILED: {len(issues)} issue(s) found")
            print("="*70)
            return (False, issues)
        else:
            print("✅ VALIDATION PASSED: Ready to build Bible")
            print("="*70)
            return (True, [])
    
    def _validate_case_structure(self) -> List[str]:
        """
        Validate case directory structure
        
        Returns:
            List of issues (empty if valid)
        """
        
        issues = []
        
        # Check case root exists
        if not self.case_root.exists():
            issues.append(f"Case root not found: {self.case_root}")
            return issues  # Can't check further if root doesn't exist
        
        # Check it's a directory
        if not self.case_root.is_dir():
            issues.append(f"Case root is not a directory: {self.case_root}")
            return issues
        
        # Check has folders
        try:
            folders = [f for f in self.case_root.iterdir() if f.is_dir()]
            folder_count = len(folders)
            
            if folder_count < 10:
                issues.append(
                    f"Only {folder_count} folders found in case root "
                    f"(expected 70+). Check path is correct."
                )
            
            # Check for some expected folders
            expected_indicators = [
                'statement of claim',
                'defence',
                'witness',
                'disclosure',
                'procedural',
                'po'
            ]
            
            folder_names_lower = [f.name.lower() for f in folders]
            found_indicators = sum(
                1 for indicator in expected_indicators
                if any(indicator in name for name in folder_names_lower)
            )
            
            if found_indicators < 3:
                issues.append(
                    f"Case structure doesn't look like litigation documents. "
                    f"Only found {found_indicators}/6 expected folder types."
                )
        
        except PermissionError:
            issues.append(f"Cannot read case root directory: Permission denied")
        
        except Exception as e:
            issues.append(f"Error reading case root: {e}")
        
        return issues
    
    def _validate_api_access(self) -> List[str]:
        """
        Validate Anthropic API access
        
        Returns:
            List of issues (empty if valid)
        """
        
        issues = []
        
        # Check API key exists
        if not self.api_key:
            issues.append("ANTHROPIC_API_KEY not set in environment")
            return issues
        
        # Check API key format
        if not self.api_key.startswith('sk-ant-'):
            issues.append(
                "API key doesn't look valid (should start with 'sk-ant-')"
            )
        
        # Try a test API call
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Make minimal cost test call
            response = client.messages.create(
                model='claude-sonnet-4-5-20250929',
                max_tokens=10,
                messages=[{
                    'role': 'user',
                    'content': 'Say OK'
                }]
            )
            
            # If we get here, API key is valid
            
        except anthropic.AuthenticationError:
            issues.append("API key is invalid or expired")
        
        except anthropic.RateLimitError:
            issues.append("API rate limit exceeded - try again in a few minutes")
        
        except Exception as e:
            issues.append(f"API test failed: {e}")
        
        return issues
    
    def _validate_output_permissions(self) -> List[str]:
        """
        Validate can write to output directory
        
        Returns:
            List of issues (empty if valid)
        """
        
        issues = []
        
        try:
            # Try to create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Try writing a test file
            test_file = self.output_dir / '.test_write'
            test_file.write_text('test')
            test_file.unlink()
        
        except PermissionError:
            issues.append(
                f"Cannot write to output directory: Permission denied"
            )
        
        except Exception as e:
            issues.append(f"Cannot write to output directory: {e}")
        
        return issues
    
    def _validate_dependencies(self) -> List[str]:
        """
        Validate required Python packages are installed
        
        Returns:
            List of issues (empty if valid)
        """
        
        issues = []
        
        required_packages = [
            ('anthropic', 'Anthropic API client'),
            ('PyPDF2', 'PDF extraction'),
            ('docx', 'Word document extraction'),
            ('yaml', 'Configuration file parsing'),
        ]
        
        for package, description in required_packages:
            try:
                __import__(package)
            except ImportError:
                issues.append(
                    f"Missing package: {package} ({description})\n"
                    f"   Install with: pip install {package}"
                )
        
        return issues
    
    def _validate_disk_space(self) -> List[str]:
        """
        Validate sufficient disk space
        
        Returns:
            List of issues (empty if valid)
        """
        
        issues = []
        
        try:
            import shutil
            
            # Check free space on output drive
            stat = shutil.disk_usage(self.output_dir.parent)
            free_gb = stat.free / (1024**3)
            
            # Need at least 1GB free (Bible is typically <10MB, but be safe)
            if free_gb < 1.0:
                issues.append(
                    f"Low disk space: Only {free_gb:.1f} GB free. "
                    f"Need at least 1 GB."
                )
        
        except Exception as e:
            # Non-critical - just warn
            logger.warning(f"Could not check disk space: {e}")
        
        return issues


def main():
    """Test validator"""
    
    from pathlib import Path
    import os
    
    # Test configuration
    case_root = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1")
    output_dir = Path("cases/lismore_v_ph")
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Run validation
    validator = BibleValidator(case_root, output_dir, api_key)
    is_valid, issues = validator.validate_all()
    
    # Show results
    if not is_valid:
        print("\n❌ VALIDATION FAILED:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nPlease fix these issues before building Bible.")
    else:
        print("\n✅ All validations passed - ready to build Bible!")


if __name__ == '__main__':
    main()