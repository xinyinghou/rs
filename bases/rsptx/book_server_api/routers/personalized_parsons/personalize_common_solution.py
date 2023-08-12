import re
def extract_variable_names(code):
    # Regular expressions to find variable names in assignments, for loops, and while loops
    assignment_pattern = re.compile(r'\b(\w+)\s*=\s*')
    for_loop_pattern = re.compile(r'\bfor\s+(\w+)\s+in\s+(?!range\b)')
    for_range_pattern = re.compile(r'\bfor\s+(\w+)\s+in\s+range\s*\(')
    while_loop_pattern = re.compile(r'\bwhile\s+(\w+)\b')
    print(for_range_pattern)
    sorted_assignment_variables = sorted([(match.group(1), match.start(1)) for match in assignment_pattern.finditer(code)], key=lambda x: x[1])
    sorted_for_loop_variables = sorted([(match.group(1), match.start(1)) for match in for_loop_pattern.finditer(code)], key=lambda x: x[1])
    sorted_while_loop_variables = sorted([(match.group(1), match.start(1)) for match in while_loop_pattern.finditer(code)], key=lambda x: x[1])
    sorted_for_range_variables = sorted([(match.group(1), match.start(1)) for match in for_range_pattern.finditer(code)], key=lambda x: x[1])
    return sorted_assignment_variables, sorted_for_loop_variables, sorted_while_loop_variables, sorted_for_range_variables

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
    avc, fvc, wvc, frvc = extract_variable_names(common_solution)
    avb, fvb, wvb, frvb = extract_variable_names(buggy_solution)
    
    dicta = mapping_var_names(avc, avb)
    dictf = mapping_var_names(fvc, fvb)
    dictw = mapping_var_names(wvc, wvb)
    dictfr = mapping_var_names(frvc, frvb)
    combined_mapping_dict = {**dicta, **dictf, **dictw, **dictfr}
    print("combined_mapping_dict", combined_mapping_dict)
    return combined_mapping_dict

def change_variable_names(common_solution, combined_mapping_dict):
    for old_var, new_var in combined_mapping_dict.items():
        # Use regex to find whole-word occurrences of the variable names
        pattern = r'\b{}\b'.format(re.escape(old_var))
        common_solution = re.sub(pattern, new_var, common_solution)

    converted_common_solution = re.sub(r'\n\s*\n', '\n', common_solution)
    print("converted_common_solution", converted_common_solution)
    return converted_common_solution
