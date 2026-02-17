#!/usr/bin/env python3
"""
Auto-populate review notes for Reddit data based on content analysis.
Detects Heritage Language Learner (HLL) indicators and writes notes only.
"""

import json
import re
from pathlib import Path

AUTO_PREFIX = "AUTOAN: "

# HLL indicator patterns
HLL_PATTERNS = {
    # Heritage language learning context
    "heritage": [
        r"heritage\s+speaker",
        r"heritage\s+language",
        r"my\s+parents?\s+speak",
        r"my\s+family\s+speak",
        r"family\s+language",
        r"first\s+language.*is",
        r"parents?\s+first\s+language",
        r"native\s+speaker",
        r"mother\s+tongue",
        r"estranged\s+from\s+my\s+family",
        r"grew\s+up\s+in.*usa",
        r"grew\s+up\s+in.*america",
        r"born\s+and.*grew\s+up",
    ],
    # Language comprehension gaps
    "comprehension_gap": [
        r"听.*不.*讲",  # Can listen but not speak
        r"understand.*can't\s+speak",
        r"understand.*can't\s+say",
        r"can\s+understand.*can't\s+speak",
        r"listening\s+comprehension.*can't\s+speak",
        r"passive.*active",
        r"comprehend.*not.*speak",
        r"can\s+follow.*can't\s+respond",
        r"recognize.*can't\s+produce",
        r"能听不能讲",
        r"会听不会说",
    ],
    # Second generation language learning
    "second_gen": [
        r"second\s+generation",
        r"2nd\s+generation",
        r"1\.5\s+generation",
        r"grew\s+up\s+here.*speak",
        r"immigr",
        r"foreign\s+language\s+to\s+me",
        r"lost.*language",
        r"trying\s+to\s+recover",
        r"re-learn",
    ],
    # Language proficiency self-assessment
    "proficiency": [
        r"fluent",
        r"conversational",
        r"broken",
        r"basic",
        r"intermediate",
        r"advanced",
        r"struggle",
        r"difficulty\s+with",
        r"have\s+trouble",
    ]
}

def detect_hll(text):
    """
    Detect if text indicates a Heritage Language Learner.
    Returns tuple: (is_hll, indicators_found)
    """
    if not text:
        return False, []
    
    text_lower = text.lower()
    indicators = []
    
    for category, patterns in HLL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                indicators.append(category)
                break
    
    # HLL if has heritage + comprehension gap OR second gen indicators
    is_hll = False
    if "heritage" in indicators and "comprehension_gap" in indicators:
        is_hll = True
    elif "heritage" in indicators and "second_gen" in indicators:
        is_hll = True
    elif "comprehension_gap" in indicators and "second_gen" in indicators:
        is_hll = True
    elif len(indicators) >= 3:  # Multiple strong indicators
        is_hll = True
    
    return is_hll, list(set(indicators))

def detect_mandarin_reference(text):
    """Check if text mentions Mandarin specifically."""
    if not text:
        return False
    
    mandarin_patterns = [
        r"mandarin",
        r"putonghua",
        r"普通话",
        r"汉语",
        r"中文.*not.*cantonese",
    ]
    
    return any(re.search(p, text.lower(), re.IGNORECASE) for p in mandarin_patterns)

def detect_thematic_analysis(text):
    """Check if text contains thematic content worth analyzing."""
    if not text:
        return False
    
    # Look for discussions of challenges, methods, experiences, etc.
    thematic_patterns = [
        r"how.*learn",
        r"best\s+way",
        r"advice",
        r"experience",
        r"challenge",
        r"difficulty",
        r"approach",
        r"method",
        r"studied",
        r"learning\s+journey",
        r"tips",
        r"help",
        r"suggest",
        r"resource",
        r"accelerat",
        r"progress",
    ]
    
    return any(re.search(p, text.lower(), re.IGNORECASE) for p in thematic_patterns)

def generate_explanation(item, is_hll, indicators):
    """Generate explanation for review decisions."""
    body = (item.get("body") or item.get("title") or "")[:200]
    
    explanations = []
    
    # HLL explanation
    if is_hll:
        explanations.append(f"HLL: Detected heritage language learning context ({', '.join(indicators)})")
    else:
        explanations.append("HLL: No clear heritage language learner indicators")
    
    # Mandarin reference
    if detect_mandarin_reference(body):
        explanations.append("Mandarin: Explicitly mentions Mandarin")
    
    # Thematic analysis
    if detect_thematic_analysis(body):
        explanations.append("Thematic: Contains learning experience/methodology discussion")
    
    # N/R suggestion (for now, mostly false unless very short)
    if len(body.strip()) < 20:
        explanations.append("N/R candidate: Very short response (possible low value)")
    
    return AUTO_PREFIX + " | ".join(explanations)

def append_auto_note(existing_notes, auto_note):
    if existing_notes:
        existing_notes = str(existing_notes).rstrip()
        if auto_note in existing_notes:
            return existing_notes
        return f"{existing_notes}\n{auto_note}"
    return auto_note

def analyze_and_update():
    """Analyze and update review JSON with AUTOAN notes only."""
    
    project_root = Path(__file__).resolve().parent.parent
    json_path = project_root / "data" / "reddit_comments_replies_review.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    hll_count = 0
    mandarin_count = 0
    thematic_count = 0
    updated_count = 0
    
    print(f"Analyzing {len(data)} items...\n")
    
    for i, item in enumerate(data):
        if item.get("type") not in ("comment", "reply"):
            continue
        if not item.get("is_new"):
            continue
        # Combine title and body for analysis
        text = (item.get("title", "") + " " + item.get("body", "")).strip()
        
        # Detect HLL (for notes only)
        is_hll, indicators = detect_hll(text)
        if is_hll:
            hll_count += 1
        
        # Detect thematic analysis relevance (for notes only)
        is_thematic = detect_thematic_analysis(text)
        if is_thematic:
            thematic_count += 1
        
        # Detect Mandarin reference (for notes only)
        has_mandarin = detect_mandarin_reference(text)
        if has_mandarin:
            mandarin_count += 1
        
        # Generate explanation
        explanation = generate_explanation(item, is_hll, indicators)
        item["notes"] = append_auto_note(item.get("notes"), explanation)
        updated_count += 1
        
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(data)} items...")
    
    # Save updated data
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Analysis complete!")
    print(f"\nSummary:")
    print(f"  Total items analyzed: {len(data)}")
    print(f"  Items updated with AUTOAN notes: {updated_count}")
    print(f"  HLL detected: {hll_count}")
    print(f"  Mandarin references: {mandarin_count}")
    print(f"  Thematic analysis worthy: {thematic_count}")
    print(f"\n✓ Updated file saved to: {json_path}")

if __name__ == "__main__":
    analyze_and_update()
