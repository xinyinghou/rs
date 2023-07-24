# import necessary packages
import time
# import necessary functions from other files
from .buggy_code_checker import buggy_code_checker
from .get_personalized_solution import *
from .evaluate_fixed_code import *
from .generate_parsons_blocks import *
from .get_parsons_code_distractors import *
from .personalize_parsons import *

# Include: Problem Name, Question Description, Cluster
# Example_student_solution, Example_buggy_code, Example_fixed_code

def get_personalized_parsons_help(dict_buggy_code, df_question_bank):
    df_question_line = df_question_bank[df_question_bank["Problem Name"] == dict_buggy_code["Problem Name"]]
    df_question_line.index = [0]
    # Extract useful code pieces from prepared data
    buggy_code = dict_buggy_code["CF (Code)"].replace("\\n", "\n")
    default_start_code = df_question_line["Default_Starting_Code"][0].replace("\\n", "\n")
    default_test_code = df_question_line["Default_Test_Code"][0].replace("\\n", "\n")
    most_common_code = df_question_line["Example_student_solution"][0].replace("\\n", "\n")
    unittest_code = df_question_line["Unittest_Code"][0].replace("\\n", "\n")

    cleaned_fixed_code = generate_personalized_fixed_code(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code)
    print('end_cleaned_fixed_code\n', cleaned_fixed_code)
    personalized_Parsons_block = generate_personalized_Parsons_blocks(df_question_line, buggy_code, cleaned_fixed_code, default_start_code, default_test_code, unittest_code)
    print("personalized_parsons_block\n", personalized_Parsons_block)
    return cleaned_fixed_code, personalized_Parsons_block

#generate the fixed code
def request_fixed_code_from_openai(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code, unittest_result = False, solution_generation = 0):
    fixed_code = get_fixed_code(build_code_prompt(df_question_line, buggy_code))
    while (solution_generation <3) & (unittest_result != True):
        print("solution_generation", solution_generation, "unittest_result", unittest_result, "fixed_code", fixed_code)
        # evaluate the fixed code
        unittest_result, cleaned_fixed_code = unittest_evaluation(fixed_code, default_start_code, default_test_code, unittest_code)
        if unittest_result == True:
            print("solution_generation", solution_generation, "unittest_result", unittest_result, "fixed_code", cleaned_fixed_code.lstrip())
            # Remove leading whitespace from the first line
            return cleaned_fixed_code.lstrip()
        else:
            fixed_code = get_fixed_code(build_code_prompt(df_question_line, buggy_code))
            solution_generation += 1
            
    if solution_generation >= 3:
        print("solution_generation", solution_generation, "unittest_result", unittest_result, "final_generated_fixed_code\n", cleaned_fixed_code)
        return most_common_code

def generate_personalized_fixed_code(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code):
    if buggy_code_checker(buggy_code, default_start_code, default_test_code):
        # get the personalized solution
        while True:
            try:
                cleaned_fixed_code = request_fixed_code_from_openai(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code)
                return cleaned_fixed_code
            except:
                time.sleep(0.5)
    else: # return False
        return most_common_code
    
def generate_personalized_Parsons_blocks(df_question_line, buggy_code, cleaned_fixed_code, default_start_code, default_test_code, unittest_code):
    buggy_code_for_blocks = clean_student_code(buggy_code, default_test_code)
    # generate the Parsons blocks
    # add paired distractors on their code when there are some meaningful comparison (one line similarity > 30%)
    code_comparison_pairs, fixed_lines, unchanged_lines, total_similarity = compare_code(buggy_code_for_blocks, cleaned_fixed_code)

    #print(code_comparison_pairs, fixed_lines, unchanged_lines, total_similarity)
    # decide the types of Parsons problems and generate correspoding distractors
    Parsons_type, distractors = personalize_Parsons_block(df_question_line, code_comparison_pairs, fixed_lines, unchanged_lines, total_similarity)
    #print("distractions\n", distractors)
    unittest_flag = True
    if (Parsons_type == "Partial")&(distractors!={}):
        # Prepare the code with distractors for unittest evaluation - cannot pass the tests this time
        code_with_distrator = generate_code_with_distrator(unchanged_lines, fixed_lines, distractors)
        #print("code_with_distractors\n", code_with_distrator)
        unittest_flag, cleaned_code_with_distractors = code_distractor_unittest_evaluation(code_with_distrator, default_start_code, default_test_code, unittest_code)
        #print("cleaned_code_with_distractors\n", cleaned_code_with_distractors)
        while unittest_flag == True:
            Parsons_type, distractors = personalize_Parsons_block(df_question_line, code_comparison_pairs, fixed_lines, unchanged_lines, total_similarity)
            code_with_distrator = generate_code_with_distrator(unchanged_lines, fixed_lines, distractors)
            #print("code_with_distractors\n", code_with_distrator)
            unittest_flag, cleaned_code_with_distractors = code_distractor_unittest_evaluation(code_with_distrator, default_start_code, default_test_code, unittest_code)
            #print("cleaned_code_with_distractors\n", cleaned_code_with_distractors)

    personalized_Parsons_block = generate_Parsons_block(Parsons_type, df_question_line, cleaned_fixed_code, unchanged_lines, fixed_lines, distractors)

    return personalized_Parsons_block





