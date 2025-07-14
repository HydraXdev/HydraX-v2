#!/usr/bin/env python3
"""
Summarize all documentation in /docs/ using SHEPHERD
"""
import os
import sys
import json
from datetime import datetime

sys.path.append('/root/HydraX-v2')
from bitten.core.shepherd.summarizer import summarize_markdown

# Get all MD files in docs directory
docs_path = '/root/HydraX-v2/docs'
md_files = []

for root, dirs, files in os.walk(docs_path):
    for file in files:
        if file.endswith('.md'):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, '/root/HydraX-v2')
            md_files.append(rel_path)

print(f"🧠 SHEPHERD Documentation Summarization")
print(f"Found {len(md_files)} documentation files to process\n")

# Process priority docs first
priority_docs = [
    'docs/SECURITY_AUDIT_REPORT.md',
    'docs/blueprint/BITTEN_FULL_PROJECT_SPEC.md',
    'docs/blueprint/BITTEN_SYSTEM_BLUEPRINT.md',
    'docs/USER_MANAGEMENT_TIER_SYSTEM_SPECIFICATIONS.md',
    'docs/STEALTH_PROTOCOL_IMPLEMENTATION.md',
    'docs/MT5_BRIDGE_SETUP.md',
    'docs/PRESS_PASS_SYSTEM.md',
    'docs/education/OPERATION_EDUCATION_FULL_BLUEPRINT.md'
]

# Sort files with priority first
priority_set = set(priority_docs)
sorted_files = []
for f in md_files:
    if f in priority_set:
        sorted_files.insert(0, f)
    else:
        sorted_files.append(f)

# Summarize each file
summaries = {}
errors = []

for i, filepath in enumerate(sorted_files[:20], 1):  # Process first 20 to avoid timeout
    print(f"[{i}/{min(20, len(sorted_files))}] Summarizing: {filepath}")
    try:
        result = summarize_markdown(filepath)
        summaries[filepath] = {
            'summary': result.summary[:200] + '...' if len(result.summary) > 200 else result.summary,
            'word_count': result.word_count,
            'key_points': result.key_points[:3]  # First 3 key points
        }
        print(f"  ✓ {result.word_count} words → {len(result.summary)} char summary")
    except Exception as e:
        errors.append(f"{filepath}: {str(e)}")
        print(f"  ✗ Error: {str(e)}")

# Save summaries to a digest file
digest_path = '/root/HydraX-v2/bitten/data/shepherd/docs_digest.json'
digest_data = {
    'metadata': {
        'generated_at': datetime.now().isoformat(),
        'total_files': len(md_files),
        'files_processed': len(summaries),
        'errors': len(errors)
    },
    'summaries': summaries,
    'errors': errors
}

with open(digest_path, 'w') as f:
    json.dump(digest_data, f, indent=2)

print(f"\n✅ Documentation summarization complete!")
print(f"Processed: {len(summaries)}/{len(md_files)} files")
print(f"Errors: {len(errors)}")
print(f"Digest saved to: {digest_path}")

# Show top summaries
print("\n📚 Key Documentation Summaries:")
for doc in priority_docs[:5]:
    if doc in summaries:
        print(f"\n{doc}:")
        print(f"  {summaries[doc]['summary']}")