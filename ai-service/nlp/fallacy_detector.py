"""
Logical Fallacy Detector for DebateX.

Detects common logical fallacies in debate arguments using
pattern matching and keyword analysis.
"""

import re
from typing import Optional


# ── Fallacy Definitions ──────────────────────────────────────

FALLACIES = {
    "ad_hominem": {
        "name": "Ad Hominem",
        "description": "Attacking the person rather than the argument",
        "patterns": [
            r"\byou(?:'re| are)\s+(?:stupid|ignorant|foolish|wrong|naive|incompetent)",
            r"\bmy opponent\s+(?:is|clearly)\s+(?:not|un)\w+",
            r"\banyone who (?:believes|thinks|says)\s+(?:that|this)\s+(?:is|must be)\s+\w+",
            r"\byour\s+(?:lack|absence)\s+of\s+(?:knowledge|understanding|intelligence)",
            r"\bonly\s+(?:a\s+)?(?:fool|idiot|naive person)",
        ],
        "keywords": ["personally", "character", "you yourself", "your kind"],
        "weight": 1.5,
    },
    "straw_man": {
        "name": "Straw Man",
        "description": "Misrepresenting opponent's argument to make it easier to attack",
        "patterns": [
            r"\bso\s+(?:you're|you are)\s+saying\s+(?:that\s+)?(?:we should|all|every)",
            r"\bwhat\s+(?:you're|my opponent is)\s+(?:really|actually)\s+saying",
            r"\byou\s+(?:want|think)\s+(?:everyone|all people|nobody)\s+should",
            r"\baccording to (?:you|my opponent),?\s+(?:we|everyone)\s+(?:should|must)\s+(?:just|simply)",
        ],
        "keywords": ["so basically you want", "what you really mean", "you're essentially saying"],
        "weight": 1.2,
    },
    "appeal_to_authority": {
        "name": "Appeal to Authority",
        "description": "Using authority as evidence without proper justification",
        "patterns": [
            r"\bexperts?\s+(?:say|agree|believe|confirm|have shown)\s+that",
            r"\bscientists?\s+(?:say|agree|believe|confirm)\s+that",
            r"\beveryone\s+(?:knows|agrees|believes)\s+that",
            r"\bits?\s+(?:a\s+)?(?:well[- ]known|established|accepted)\s+fact\s+that",
        ],
        "keywords": [],
        "weight": 0.8,
    },
    "false_dichotomy": {
        "name": "False Dichotomy",
        "description": "Presenting only two options when more exist",
        "patterns": [
            r"\b(?:either|it's either)\s+.{5,50}\s+or\s+",
            r"\byou(?:'re| are)\s+either\s+(?:with|for)\s+(?:us|this)\s+or\s+(?:against|not)",
            r"\bthere\s+(?:are|is)\s+only\s+(?:two|2)\s+(?:options?|choices?|ways?)",
            r"\bif\s+(?:you|we)\s+don't\s+.{5,30}\s+then\s+.{5,30}\s+will\s+(?:happen|occur|result)",
        ],
        "keywords": ["only two choices", "no other option", "either we", "or else"],
        "weight": 1.0,
    },
    "slippery_slope": {
        "name": "Slippery Slope",
        "description": "Assuming one event will inevitably lead to extreme consequences",
        "patterns": [
            r"\bif\s+we\s+(?:allow|let|permit|start)\s+.{5,30}\s+then\s+(?:soon|next|eventually|before long)",
            r"\bthis\s+will\s+(?:inevitably|ultimately|eventually)\s+lead\s+to",
            r"\bwhere\s+(?:does|will)\s+it\s+(?:end|stop)",
            r"\bopen(?:ing)?\s+the\s+(?:flood)?gates?\s+(?:to|for)",
        ],
        "keywords": ["slippery slope", "domino effect", "where does it end", "what's next"],
        "weight": 1.0,
    },
    "circular_reasoning": {
        "name": "Circular Reasoning",
        "description": "Using the conclusion as a premise",
        "patterns": [
            r"\bbecause\s+(?:it\s+)?(?:is|it's)\s+(?:true|right|correct|obvious)",
            r"\bthis\s+is\s+(?:true|right)\s+because\s+(?:it\s+)?(?:is|it's)\s+(?:true|correct)",
            r"\bwe\s+know\s+(?:this|it)\s+because\s+.{5,30}\s+which\s+(?:shows|proves)\s+(?:this|it)",
        ],
        "keywords": ["because it is", "it's true because it's true", "self-evident"],
        "weight": 1.3,
    },
    "appeal_to_emotion": {
        "name": "Appeal to Emotion (excessive)",
        "description": "Using excessive emotional manipulation instead of logical reasoning",
        "patterns": [
            r"\bthink\s+of\s+the\s+(?:children|families|victims|people|elderly)",
            r"\bhow\s+(?:can|could|dare)\s+(?:you|we|anyone)\s+(?:stand|sit)\s+(?:by|idle)",
            r"\bthe\s+(?:blood|tears|suffering|pain)\s+(?:of|from)\s+",
            r"\bshame\s+on\s+(?:you|anyone|those)\s+who",
        ],
        "keywords": ["heartless", "unconscionable", "monstrous", "unforgivable"],
        "weight": 0.7,
    },
    "hasty_generalization": {
        "name": "Hasty Generalization",
        "description": "Drawing a broad conclusion from limited examples",
        "patterns": [
            r"\b(?:all|every|always|never|no one|everyone|nobody)\s+(?:is|are|does|do|will|can|should)",
            r"\b(?:this|that)\s+(?:one|single)\s+(?:example|case|instance)\s+(?:proves|shows)\s+that\s+(?:all|every)",
        ],
        "keywords": ["always", "never", "all people", "no one ever", "every single"],
        "weight": 0.9,
    },
}


def detect_fallacies(text: str) -> list[dict]:
    """
    Detect logical fallacies in a debate argument.

    Returns a list of detected fallacies with:
      - name, description, confidence (0-1), matches
    """
    text_lower = text.lower()
    detected = []

    for fallacy_id, fallacy in FALLACIES.items():
        confidence = 0.0
        matches = []

        # Check regex patterns
        for pattern in fallacy["patterns"]:
            found = re.findall(pattern, text_lower)
            if found:
                confidence += 0.3 * len(found)
                matches.extend(found)

        # Check keywords
        for keyword in fallacy["keywords"]:
            if keyword.lower() in text_lower:
                confidence += 0.2
                matches.append(keyword)

        if confidence > 0:
            confidence = min(confidence, 1.0)
            detected.append({
                "id": fallacy_id,
                "name": fallacy["name"],
                "description": fallacy["description"],
                "confidence": round(confidence, 3),
                "weight": fallacy["weight"],
                "matches": matches[:3],  # Limit match examples
            })

    # Sort by confidence (highest first)
    detected.sort(key=lambda x: x["confidence"], reverse=True)
    return detected


def compute_fallacy_penalty(text: str) -> float:
    """
    Compute the fallacy penalty score for an argument (0-5 scale).

    Higher penalty = more detected fallacies with higher confidence.
    """
    fallacies = detect_fallacies(text)
    if not fallacies:
        return 0.0

    # Weighted sum of fallacy confidences
    penalty = sum(f["confidence"] * f["weight"] for f in fallacies)
    return round(min(5.0, penalty), 2)


def get_fallacy_summary(text: str) -> str:
    """Get a human-readable summary of detected fallacies."""
    fallacies = detect_fallacies(text)
    if not fallacies:
        return "No significant logical fallacies detected."

    lines = []
    for f in fallacies:
        conf_pct = int(f["confidence"] * 100)
        lines.append(f"• {f['name']} ({conf_pct}% confidence): {f['description']}")

    return "\n".join(lines)
