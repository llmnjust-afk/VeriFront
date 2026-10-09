"""VeriFront: experiment control for step-level counterfactual replacement pilots.

Source of truth for the research protocol: Prompt_V2.md (pilot plan v2.0).
"""

__version__ = "0.1.0"

STEP_TYPES = [
    "retrieval",
    "doc_parse_convert",
    "info_extract",
    "tool_args",
    "code_gen_repair",
    "numeric_stats",
    "analysis_planning",
    "result_interpretation",
]

UNASSIGNABLE = "unassignable"
