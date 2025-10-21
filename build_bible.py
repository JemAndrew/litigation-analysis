#!/usr/bin/env python3
"""
Build Case Bible - Entry Point (SIMPLIFIED VERSION)

Improvements:
- Loads from config.yaml (no hardcoded paths!)
- Pre-flight validation
- Cost estimation & confirmation
- Error recovery
- Comprehensive logging

Usage:
    python build_bible.py

British English throughout.
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
import sys
import json
import os
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.bible_builder import BibleBuilder
from src.core.bible_validator import BibleValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bible_build.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """
    Load configuration from config.yaml
    
    Returns:
        Configuration dict
    
    Raises:
        FileNotFoundError if config doesn't exist
    """
    
    config_file = Path('config.yaml')
    
    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        
        print("\n" + "="*70)
        print("❌ ERROR: config.yaml not found")
        print("="*70)
        print("\nPlease create a config.yaml file with your case details.")
        print("See the artifact 'config.yaml - Case Configuration Template' for an example.")
        print("\nMinimum required fields:")
        print("  - case_id")
        print("  - case_name")
        print("  - claimant")
        print("  - respondent")
        print("  - case_root (path to your case documents)")
        
        sys.exit(1)
    
    # Load YAML
    try:
        import yaml
    except ImportError:
        print("\n❌ ERROR: PyYAML not installed")
        print("   Install with: pip install pyyaml")
        sys.exit(1)
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Configuration loaded from {config_file}")
    return config


def validate_config(config: dict) -> tuple[bool, list[str]]:
    """
    Validate configuration
    
    Args:
        config: Configuration dict
    
    Returns:
        (is_valid, list of issues)
    """
    
    issues = []
    
    # Check required fields
    required_fields = [
        'case_id', 'case_name', 'claimant', 
        'respondent', 'case_root'
    ]
    
    for field in required_fields:
        if not config.get(field):
            issues.append(f"Missing required field: {field}")
    
    # Check case root exists
    if config.get('case_root'):
        case_root = Path(config['case_root'])
        if not case_root.exists():
            issues.append(f"Case root directory not found: {case_root}")
        else:
            # Check it has folders
            folders = list(case_root.iterdir())
            if len(folders) < 10:
                issues.append(
                    f"Case root has only {len(folders)} folders "
                    f"(expected 70+). Is this the correct path?"
                )
    
    return (len(issues) == 0, issues)


def estimate_cost(builder: BibleBuilder) -> dict:
    """
    Estimate Bible build cost
    
    Args:
        builder: BibleBuilder instance
    
    Returns:
        Cost estimate dict
    """
    
    print("\n" + "="*70)
    print("💰 COST ESTIMATION")
    print("="*70)
    
    # This is a rough estimate based on typical Bible sizes
    # Real cost calculated during build
    
    estimated = {
        'input_tokens': 100000,  # ~100K tokens typical
        'output_tokens': 60000,   # ~60K tokens output
        'thinking_tokens': 20000, # Extended thinking
        'total_tokens': 180000,
        'cost_gbp': 1.5  # Approximate
    }
    
    print(f"\nEstimated tokens:")
    print(f"  Input:    {estimated['input_tokens']:>8,} tokens")
    print(f"  Output:   {estimated['output_tokens']:>8,} tokens")
    print(f"  Thinking: {estimated['thinking_tokens']:>8,} tokens")
    print(f"  Total:    {estimated['total_tokens']:>8,} tokens")
    
    print(f"\nEstimated cost: £{estimated['cost_gbp']:.2f}")
    print(f"(Actual cost will be calculated during build)")
    
    return estimated


def confirm_build(config: dict, cost_estimate: dict) -> bool:
    """
    Get user confirmation before building
    
    Args:
        config: Configuration
        cost_estimate: Cost estimate dict
    
    Returns:
        True if user confirms
    """
    
    print("\n" + "="*70)
    print("📋 BUILD SUMMARY")
    print("="*70)
    
    print(f"\nCase: {config['case_name']}")
    print(f"Root: {Path(config['case_root'])}")
    print(f"\nWhat this will do:")
    print(f"  1. Classify 74 folders intelligently")
    print(f"  2. Select ~40-44 Bible-critical documents")
    print(f"  3. Extract text from selected documents")
    print(f"  4. Generate comprehensive Case Bible with Claude")
    print(f"  5. Save Bible to cases/{config['case_id']}/")
    
    print(f"\nEstimated:")
    print(f"  Cost: £{cost_estimate['cost_gbp']:.2f}")
    print(f"  Time: 10-15 minutes")
    
    max_cost = config.get('max_cost_gbp', 5.0)
    if cost_estimate['cost_gbp'] > max_cost:
        print(f"\n⚠️  WARNING: Estimated cost exceeds max_cost_gbp setting (£{max_cost:.2f})")
    
    # Get confirmation
    response = input("\n✅ Proceed with Bible generation? (y/n): ")
    return response.lower() == 'y'


def build_with_recovery(
    builder: BibleBuilder,
    use_extended_thinking: bool
) -> Path:
    """
    Build Bible with error recovery
    
    Args:
        builder: BibleBuilder instance
        use_extended_thinking: Use Claude's extended thinking
    
    Returns:
        Path to saved Bible
    """
    
    try:
        bible_path = builder.build_bible(
            use_extended_thinking=use_extended_thinking
        )
        
        return bible_path
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Build cancelled by user")
        raise
        
    except Exception as e:
        logger.error(f"Bible build failed: {e}", exc_info=True)
        
        print(f"\n\n❌ FATAL ERROR:")
        print(f"   {str(e)}")
        print(f"\nFull error logged to: bible_build_error.log")
        
        # Log full traceback to separate error file
        import traceback
        error_log = Path('bible_build_error.log')
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write(f"Bible build error at {datetime.now()}\n")
            f.write("="*70 + "\n\n")
            f.write(f"Config:\n")
            f.write(f"  Case: {builder.case_name}\n")
            f.write(f"  Root: {builder.case_root}\n\n")
            f.write("="*70 + "\n\n")
            f.write(traceback.format_exc())
        
        print(f"   Error details: {error_log}")
        
        raise


def show_results(bible_path: Path):
    """
    Show build results
    
    Args:
        bible_path: Path to generated Bible
    """
    
    print("\n" + "="*70)
    print("✅ CASE BIBLE BUILD COMPLETE!")
    print("="*70)
    
    # Show created files
    print(f"\n📁 Files created:")
    
    files_created = [
        (bible_path, "📖 Plain text Bible"),
        (bible_path.parent / 'case_bible_structured.json', "📊 Structured Bible (JSON)"),
        (bible_path.parent / 'case_bible_metadata.json', "📈 Build metadata"),
        (bible_path.parent / 'extracted_documents.json', "📋 Document list")
    ]
    
    for file_path, description in files_created:
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   {description}")
            print(f"      {file_path}")
            print(f"      ({size_mb:.2f} MB)")
    
    # Show metadata
    metadata_file = bible_path.parent / 'case_bible_metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print(f"\n📊 Build Statistics:")
        print(f"   Folders analysed: {metadata.get('folders_analysed', 0)}")
        print(f"   Documents extracted: {metadata.get('documents_extracted', 0)}")
        print(f"   Legal authorities noted: {metadata.get('legal_authorities_noted', 0)}")
        print(f"   Bible length: {metadata.get('bible_length_chars', 0):,} characters")
        print(f"   Estimated tokens: {metadata.get('bible_length_tokens_est', 0):,}")
        
        print(f"\n💰 Cost:")
        print(f"   Total: £{metadata.get('total_cost_gbp', 0):.2f}")
        
        print(f"\n⏱️  Duration:")
        duration_sec = metadata.get('build_duration_seconds', 0)
        print(f"   {duration_sec / 60:.1f} minutes")
    
    print(f"\n🎉 Bible is ready for use!")
    print(f"   Use it in chat with: --use-bible")


def main():
    """Main entry point"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Build Case Bible for litigation analysis'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                     CASE BIBLE BUILDER                            ║
║                                                                   ║
║  This will analyse your case documents and build a comprehensive ║
║  Case Bible that will be cached for all future queries.          ║
║                                                                   ║
║  ONE-TIME COST: £1-2 (with extended thinking!)                   ║
║  Time required: 10-15 minutes                                     ║
║  Future query cost: £0.30 (95% savings with caching!)            ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Load config
        config = load_config()
        
        # Validate config
        is_valid, issues = validate_config(config)
        if not is_valid:
            print("\n❌ CONFIGURATION VALIDATION FAILED:")
            for issue in issues:
                print(f"   • {issue}")
            print("\nPlease fix config.yaml and try again.")
            return 1
        
        print("✅ Configuration valid")
        
        # ═══════════════════════════════════════════════════════════
        # PRE-FLIGHT VALIDATION (using BibleValidator)
        # ═══════════════════════════════════════════════════════════
        case_root = Path(config['case_root'])
        output_dir = (
            Path(config['output_dir']) if config.get('output_dir')
            else Path(f"cases/{config['case_id']}")
        )
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Run pre-flight validation
        validator = BibleValidator(case_root, output_dir, api_key)
        is_valid_preflight, preflight_issues = validator.validate_all()
        
        if not is_valid_preflight:
            print("\n❌ PRE-FLIGHT VALIDATION FAILED:")
            for issue in preflight_issues:
                print(f"   • {issue}")
            print("\nPlease fix these issues before building Bible.")
            return 1
        # ═══════════════════════════════════════════════════════════
        
        # Create builder (validation passed!)
        builder = BibleBuilder(
            case_root=case_root,
            case_id=config['case_id'],
            case_name=config['case_name'],
            claimant=config['claimant'],
            respondent=config['respondent'],
            tribunal=config.get('tribunal', 'LCIA')
        )
        
        # Estimate cost
        cost_estimate = estimate_cost(builder)
        
        # Get confirmation
        if not confirm_build(config, cost_estimate):
            print("\n❌ Build cancelled")
            return 1
        
        # Build Bible
        use_extended_thinking = config.get('use_extended_thinking', True)
        
        bible_path = build_with_recovery(
            builder=builder,
            use_extended_thinking=use_extended_thinking
        )
        
        # Show results
        show_results(bible_path)
        
        return 0
        
    except KeyboardInterrupt:
        return 1
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())