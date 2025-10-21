# Save as check_prompt_size.py
from pathlib import Path
from src.core.bible_builder import BibleBuilder
import dotenv
dotenv.load_dotenv()
# Your config
CASE_ROOT = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1")

builder = BibleBuilder(
    case_root=CASE_ROOT,
    case_id="lismore_v_ph",
    case_name="Lismore Capital Limited v Process Holdings Limited",
    claimant="Process Holdings Limited",
    respondent="Lismore Capital Limited",
    tribunal="LCIA"
)

# Classify and extract (but don't call API)
organised = builder.classifier.get_folders_for_bible()
to_process = (organised['critical'] + organised['high'] + 
              organised['medium'] + organised['legal_authorities'])
selected = builder.selector.select_for_bible_building(to_process)
builder._extract_all_documents(selected)

# Build prompt
prompt = builder._build_bible_prompt()

# CHECK SIZE
chars = len(prompt)
tokens = chars // 4  # Rough estimate

print(f"\n{'='*70}")
print("PROMPT SIZE DIAGNOSTIC")
print(f"{'='*70}")
print(f"\nCharacters: {chars:,}")
print(f"Estimated tokens: {tokens:,}")
print(f"\nClaude limit: 200,000 tokens")
print(f"Your usage: {tokens/200000*100:.1f}%")

if tokens > 200000:
    print(f"\n🚨 PROBLEM: Exceeds 200K limit by {tokens-200000:,} tokens!")
    print(f"\nSOLUTION: Need to truncate more aggressively")
elif tokens > 180000:
    print(f"\n⚠️  WARNING: Very close to limit (90%+)")
    print(f"\nWith extended thinking (20K) + output (32K) = {tokens+52000:,} tokens")
    if tokens + 52000 > 200000:
        print(f"🚨 EXCEEDS LIMIT with thinking/output!")
else:
    print(f"\n✅ Within limits")

print(f"\n{'='*70}")