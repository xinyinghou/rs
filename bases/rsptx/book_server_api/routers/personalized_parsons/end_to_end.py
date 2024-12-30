# import necessary packages
import time
import traceback
# import necessary functions from other files
# from buggy_code_checker import buggy_code_checker
# from get_personalized_solution import *
# from evaluate_fixed_code import *
# from generate_parsons_blocks import *
# from personalize_parsons import *
# from token_compare import *

from .buggy_code_checker import buggy_code_checker
from .get_personalized_solution import *
from .evaluate_fixed_code import *
from .generate_parsons_blocks import *
from .personalize_parsons import *
from .token_compare import *


# Include: Problem Name, Question Description, Cluster
# Example_student_solution, Example_buggy_code, Example_fixed_code

def get_parsons_help(dict_buggy_code, df_question_bank, personalization):
    df_question_line = df_question_bank[df_question_bank["Problem Name"] == dict_buggy_code["Problem Name"]]
    df_question_line.index = [0]
    problem_description = df_question_line["w_question_description"][0].replace("\\n", "\n")
    # Extract useful code pieces from prepared data
    buggy_code = dict_buggy_code["CF (Code)"].replace("\\n", "\n")
    default_start_code = df_question_line["Default_Starting_Code"][0].replace("\\n", "\n")
    default_test_code = df_question_line["Default_Test_Code"][0].replace("\\n", "\n")
    most_common_code = df_question_line["Example_student_solution"][0].replace("\\n", "\n")
    unittest_code = df_question_line["Unittest_Code"][0].replace("\\n", "\n")
    print("buggy_code\n", buggy_code, "\ndefault_start_code\n", default_start_code, "\ndefault_test_code\n", default_test_code, "\nmost_common_code\n", most_common_code, "\nunittest_code\n", unittest_code)
    if personalization == True:
        cleaned_fixed_code = generate_personalized_fixed_code(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code)
        final_fixed_code = cleaned_fixed_code.lstrip()
        print('personalized_end_cleaned_fixed_code\n', cleaned_fixed_code)
    else:
        final_fixed_code = most_common_code.lstrip()
    # generate Parsons problems with personalization only at the solution level
    final_Parsons_block = generate_full_Parsons(final_fixed_code, problem_description)
    print("personalized_parsons_block\n", final_Parsons_block)
    return final_fixed_code, final_Parsons_block


#generate the fixed code
def request_fixed_code_from_openai(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code, solution_generation, old_fixed_code, attempt_type, situation, failure_reason, unittest_result = False):
    if solution_generation == 0:
        cleaned_buggy_code = clean_student_code(buggy_code, default_test_code)
        similarity_most_common = code_similarity_score(cleaned_buggy_code, most_common_code)
        return most_common_code
    
    fixed_code = get_fixed_code(df_question_line, buggy_code, default_test_code, attempt_type="new", situation="", old_fixed_code="")
    cleaned_buggy_code = clean_student_code(buggy_code, default_test_code)
    unittest_result, cleaned_fixed_code = unittest_evaluation(buggy_code, fixed_code, default_start_code, default_test_code, unittest_case=unittest_code)
    print("solution_generation", solution_generation, "fixed_code", fixed_code)
    
    if unittest_result:
        similarity_personalized = code_similarity_score(buggy_code, cleaned_fixed_code)
        similarity_most_common = code_similarity_score(buggy_code, most_common_code)
        if similarity_personalized >= similarity_most_common:
            print("add_personalized_code-cleaned_buggy_code", cleaned_buggy_code, "cleaned_fixed_code", cleaned_fixed_code)
            return cleaned_fixed_code.lstrip()
        else:
            print("not personalized")
            solution_generation -= 1
            return request_fixed_code_from_openai(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code, solution_generation, cleaned_fixed_code, attempt_type="repeat", situation="close enough", failure_reason="not personalized", unittest_result = False)
    else:
        print("not correct")
        solution_generation -= 1
        return request_fixed_code_from_openai(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code, solution_generation, cleaned_fixed_code, attempt_type="repeat", situation="a correct answer", failure_reason="not correct", unittest_result = False)

def generate_personalized_fixed_code(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code, API_attempt=0):
    # personalized_most_common_solution = change_variable_names(most_common_code, map_variable_names(buggy_code, most_common_code))
    if buggy_code_checker(buggy_code, default_start_code, default_test_code):
        # get the personalized solution
        while True & (API_attempt < 2):
            API_attempt += 1
            print("attempt", API_attempt)
            try:
                cleaned_fixed_code_info_package  = request_fixed_code_from_openai(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code, 3, "", "", "", "")
                print("cleaned_fixed_code_info_package", cleaned_fixed_code_info_package)
                return cleaned_fixed_code_info_package
            except Exception as e:
                traceback.print_exc()
                time.sleep(0.01)
                print(f"{API_attempt}-{e}-time_sleep")
                if API_attempt >= 2:
                    return most_common_code
    else: # return False
        return most_common_code


