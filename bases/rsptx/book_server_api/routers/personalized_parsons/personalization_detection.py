import re

def detect_loop_statements(code_snippet):
    for_range_statements = re.findall(r'\bfor\s+\w+\s+in\s+range\b', code_snippet)
    general_for_statements = re.findall(r'\bfor\s+\w+\s+in\b', code_snippet)
    while_statements = re.findall(r'\bwhile\b', code_snippet)
    return for_range_statements>0, general_for_statements>0, while_statements>0

def detect_control_statements(code_snippet):
    if_else_statements = re.findall(r'\bif\s+.*\s+else\b', code_snippet)
    if_elif_statements = re.findall(r'\bif\s+.*\s+elif\b', code_snippet)
    return len(if_else_statements), len(if_elif_statements)

def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0.0


def rule_personalize_detection(buggy_code, fixed_code):


