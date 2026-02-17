"""
keyword_sets.py

Defines keyword sets used to identify Reddit posts related to heritage language
learners, with a focus on affective factors such as shame, guilt, obligation,
and identity conflict.
"""

CATEGORIZED_KEYWORDS = {
    "Heritage identity markers": [
        "heritage language",
        "heritage speaker",
        "heritage learner",
        "mother tongue",
        "native language",
        "family language",
        "parents language",
        "home language",
        "mother language",
        "dad language",
        "mother speaks",
        "dad speaks",
        "first language",
        "my culture's language",
    ],
    "Obligation & expectation": [
        "feel obligated to learn",
        "should know my language",
        "supposed to speak",
        "expected to speak",
        "pressure to learn",
        "family expectation",
        "cultural expectation",
        "should speak",
        "should learn",
        "need to speak",
    ],
    "Shame & guilt": [
        "feel ashamed",
        "language shame",
        "feel guilty",
        "guilt about language",
        "embarrassed to speak",
        "embarrassment speaking",
        "feel dumb speaking",
        "feel stupid speaking",
    ],
    "Social judgement & shaming": [
        "being shamed",
        "people shame me",
        "family shames me",
        "parents shame me",
        "judged for my language",
        "criticized for my accent",
    ],
    "Competence & identity conflict": [
        "not fluent",
        "not fluent enough",
        "not good enough",
        "bad accent",
        "broken language",
        "childish language",
        "sound like a child",
        "slow speaker",
    ],
    "Loss / regret / delay": [
        "never learned",
        "didn't learn growing up",
        "regret not learning",
        "lost my language",
        "language attrition",
    ],
    "Comparison & legitimacy anxiety": [
        "others speak better",
        "compared to others",
        "not a real speaker",
        "don't feel legitimate",
        "feel fake speaking",
    ],
    "Explicit emotional framing": [
        "feel embarrassed",
        "feel ashamed to say",
        "anxious speaking",
        "afraid to speak",
    ],
    "Pride, joy": [
        "proud of",
        "am happy",
        "feel content",
        "joy",
    ],
    "Approach": [
        "want to speak",
        "want to learn",
        "can speak",
        "hope to master",
        "hope to speak",
        "will speak",
    ],
}

HERITAGE_LANGUAGE_KEYWORDS = [
    term
    for group in CATEGORIZED_KEYWORDS.values()
    for term in group
]
