import re


def extract_variable_names(code):
    # Regular expressions to find variable names in assignments, for loops, and while loops
    # Pattern for variable assignments followed by an opening curly brace
    assignment_pattern_with_curly_brace = re.compile(r'\b(\w+)\s*=\s*\{')
    # Pattern for variable assignments followed by an opening square bracket
    assignment_pattern_with_square_bracket = re.compile(r'\b(\w+)\s*=\s*\[\s*')
    # Pattern for variable assignments followed by a number
    assignment_pattern_with_number = re.compile(r'\b(\w+)\s*=\s*\d+\s*')
    # Pattern for variable assignments followed by string
    assignment_pattern_with_string = re.compile(r'\b(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')\s*')
    # Pattern for variable assignments followed by other
    assignment_pattern_all = re.compile(r'\b(\w+)\s*=\s*(\w+)\s*')
    for_loop_pattern = re.compile(r'\bfor\s+(\w+)\s+in\s+(?!range\b)')
    for_dict_iterate_pattern = re.compile(r'\bfor\s+(\w+)\s*,\s*(\w+)\s+in\s+')
    for_range_pattern = re.compile(r'\bfor\s+(\w+)\s+in\s+range\s*\(')
    while_loop_pattern = re.compile(r'\bwhile\s+(\w+)\b')
    def_function_pattern = re.compile(r'def\s+\w+\s*\(([^)]*)\)')
    #print(for_range_pattern)
    sorted_def_variables = sorted([(param, match.start(1)) for match in def_function_pattern.finditer(code) for param in re.findall(r'\w+', match.group(1))], key=lambda x: x[1])
    sorted_ass_curly_brace_variables = sorted([(match.group(1), match.start(1)) for match in assignment_pattern_with_curly_brace.finditer(code)], key=lambda x: x[1])
    sorted_ass_square_bracket_variables = sorted([(match.group(1), match.start(1)) for match in assignment_pattern_with_square_bracket.finditer(code)], key=lambda x: x[1])
    sorted_ass_number_variables = sorted([(match.group(1), match.start(1)) for match in assignment_pattern_with_number.finditer(code)], key=lambda x: x[1])
    sorted_ass_pattern_string = sorted([(match.group(1), match.start(1)) for match in assignment_pattern_with_string.finditer(code)], key=lambda x: x[1])
    sorted_ass_pattern_all = sorted([(match.group(1), match.start(1)) for match in assignment_pattern_all.finditer(code)], key=lambda x: x[1])
    # Get the set of variables from each sorted list
    existing_variables = set()
    existing_variables.update(name for name, _ in sorted_def_variables)
    existing_variables.update(name for name, _ in sorted_ass_curly_brace_variables)
    existing_variables.update(name for name, _ in sorted_ass_square_bracket_variables)
    existing_variables.update(name for name, _ in sorted_ass_number_variables)

    # Filter assignments in sorted_ass_pattern_all that are not in existing_variables
    sorted_ass_pattern_other = sorted([(name, start_index) for name, start_index in sorted_ass_pattern_all if name not in existing_variables], key=lambda x: x[1])
    
    sorted_for_loop_variables = sorted([(match.group(1), match.start(1)) for match in for_loop_pattern.finditer(code)], key=lambda x: x[1])
    sorted_while_loop_variables = sorted([(match.group(1), match.start(1)) for match in while_loop_pattern.finditer(code)], key=lambda x: x[1])
    sorted_for_range_variables = sorted([(match.group(1), match.start(1)) for match in for_range_pattern.finditer(code)], key=lambda x: x[1])
    sorted_for_dict_iterate_variables = sorted([(match.group(1), match.group(2), match.start(1)) for match in for_dict_iterate_pattern.finditer(code)], key=lambda x: x[2])
    print("sorted_def_variables",sorted_def_variables, "sorted_ass_curly_brace_variables",sorted_ass_curly_brace_variables)
    return sorted_def_variables, sorted_ass_curly_brace_variables, sorted_ass_square_bracket_variables, sorted_ass_number_variables, sorted_ass_pattern_string, sorted_ass_pattern_other, sorted_for_loop_variables, sorted_while_loop_variables, sorted_for_range_variables, sorted_for_dict_iterate_variables

def mapping_var_names(sorted_common_var, sorted_buggy_var):
    #print(sorted_var1, sorted_var2)
    min_len = min(len(sorted_common_var), len(sorted_buggy_var))
    name_mapping = {}
    for i in range(min_len):
        # build a dictionary with key as the common variable name and value as the buggy variable name
        # use this to change common variable names to buggy variable names
        name_mapping[sorted_buggy_var[i][0]] = sorted_common_var[i][0]

    return name_mapping

def map_variable_names(common_solution, buggy_solution):
    dvc, curly_avc, square_avc, number_avc, string_avc, other_avc, fvc, wvc, frvc, fdvc = extract_variable_names(common_solution)
    print("c", dvc, curly_avc, square_avc, number_avc, string_avc, other_avc, fvc, wvc, frvc, fdvc)
    dvb, curly_avb, square_avb, number_avb, string_avb, other_avb, fvb, wvb, frvb, fdvb = extract_variable_names(buggy_solution)
    print("b", dvb, curly_avb, square_avb, number_avb, string_avb, other_avb, fvb, wvb, frvb, fdvb)
    dicd = mapping_var_names(dvc, dvb)
    dicta_curly = mapping_var_names(curly_avc, curly_avb)
    dicta_square = mapping_var_names(square_avc, square_avb)
    dicta_number = mapping_var_names(number_avc, number_avb)
    dicta_string = mapping_var_names(string_avc, string_avb)
    dicta_other = mapping_var_names(other_avc, other_avb)
    print("dicta_curly", dicta_curly, "dicta_square", dicta_square, "dicta_number", dicta_number, "dicta_string", dicta_string, "dicta_other", dicta_other)
    dictf = mapping_var_names(fvc, fvb)
    dictw = mapping_var_names(wvc, wvb)
    dictfr = mapping_var_names(frvc, frvb)
    dictfd = mapping_var_names(fdvc, fdvb)
    combined_mapping_dict = {**dicd, **dicta_curly, **dicta_square, **dicta_number, **dicta_string, **dicta_other, **dictf, **dictw, **dictfr, **dictfd}
    print("combined_mapping_dict", combined_mapping_dict)
    return combined_mapping_dict

def change_variable_names(common_solution, combined_mapping_dict):
    for old_var, new_var in combined_mapping_dict.items():
        # Use regex to find whole-word occurrences of the variable names
        pattern = r'\b{}\b'.format(re.escape(old_var))
        common_solution = re.sub(pattern, new_var, common_solution)

    converted_common_solution = re.sub(r'\n\s*\n', '\n', common_solution)
    print("converted_solution", converted_common_solution)
    return converted_common_solution
