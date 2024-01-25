# import necessary packages
import time
import traceback
# import necessary functions from other files
from .buggy_code_checker import buggy_code_checker
from .get_personalized_solution import *
from .evaluate_fixed_code import *
from .generate_parsons_blocks import *
from .get_parsons_code_distractors import *
from .personalize_parsons import *
from .personalize_common_solution import *
from .token_compare import *


# Include: Problem Name, Question Description, Cluster
# Example_student_solution, Example_buggy_code, Example_fixed_code

def get_personalized_parsons_help(dict_buggy_code, df_question_bank):
    df_question_line = df_question_bank[df_question_bank["Problem Name"] == dict_buggy_code["Problem Name"]]
    print("df_question_line\n", df_question_line)
    df_question_line.index = [0]
    # Extract useful code pieces from prepared data
    buggy_code = dict_buggy_code["CF (Code)"].replace("\\n", "\n")
    default_start_code = df_question_line["Default_Starting_Code"][0].replace("\\n", "\n")
    default_test_code = df_question_line["Default_Test_Code"][0].replace("\\n", "\n")
    most_common_code = df_question_line["Example_student_solution"][0].replace("\\n", "\n")
    unittest_code = df_question_line["Unittest_Code"][0].replace("\\n", "\n")
    print("buggy_code\n", buggy_code, "\ndefault_start_code\n", default_start_code, "\ndefault_test_code\n", default_test_code, "\nmost_common_code\n", most_common_code, "\nunittest_code\n", unittest_code)
    cleaned_fixed_code = generate_personalized_fixed_code(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code)
    print('end_cleaned_fixed_code\n', cleaned_fixed_code)
    personalized_Parsons_block = generate_personalized_Parsons_blocks(df_question_line, buggy_code, cleaned_fixed_code, default_start_code, default_test_code, unittest_code)
    print("personalized_parsons_block\n", personalized_Parsons_block)
    return cleaned_fixed_code, personalized_Parsons_block




#generate the fixed code
def request_fixed_code_from_openai(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code, unittest_result = False, similarity_personalized = 0, similarity_most_common = 1, solution_generation = 0):
    personalized_most_common_solution = change_variable_names(most_common_code, map_variable_names(buggy_code, most_common_code))
    print("buggy_code", buggy_code)
    fixed_code = get_fixed_code(df_question_line, buggy_code, attempt_type="new", situation="", old_fixed_code="")
    print("solution_generation", solution_generation, "fixed_code", fixed_code)
    while (solution_generation <=2) & ((unittest_result != True) or (similarity_personalized < similarity_most_common)):
        #print("solution_generation", solution_generation, "unittest_result", unittest_result, "fixed_code", fixed_code)
        # evaluate the fixed code
        unittest_result, cleaned_fixed_code = unittest_evaluation(fixed_code, default_start_code, default_test_code, unittest_code)
        similarity_personalized = code_similarity_score(buggy_code, cleaned_fixed_code)
        similarity_most_common = code_similarity_score(buggy_code, personalized_most_common_solution)

        if (unittest_result == True) & (similarity_personalized >= similarity_most_common):
            print("solution_generation", solution_generation, "unittest_result", unittest_result, "fixed_code", cleaned_fixed_code.lstrip(), "similarity_personalized", similarity_personalized, "similarity_most_common", similarity_most_common)
            # Remove leading whitespace from the first line
            # store this cleaned_fixed_code in the database
            add_personalized_code(buggy_code, cleaned_fixed_code)
            return cleaned_fixed_code.lstrip()
        elif (unittest_result == True) & (similarity_personalized < similarity_most_common):
            fixed_code = get_fixed_code(df_question_line, buggy_code, attempt_type="repeat", situation="close enough", old_fixed_code=cleaned_fixed_code)
            solution_generation += 1
        else:
            fixed_code = get_fixed_code(df_question_line, buggy_code, attempt_type="repeat", situation="a correct answer", old_fixed_code=cleaned_fixed_code)
            solution_generation += 1
            
    if solution_generation > 2:
        print("retuen: personalized_most_common_solution \n solution_generation", solution_generation, "unittest_result", unittest_result, "final_generated_fixed_code\n", cleaned_fixed_code, "similarity_personalized", similarity_personalized, "similarity_most_common", similarity_most_common)
        print("personalized_most_common_solution", personalized_most_common_solution)
        return personalized_most_common_solution

def generate_personalized_fixed_code(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code, API_attempt = 0):
    personalized_most_common_solution = change_variable_names(most_common_code, map_variable_names(buggy_code, most_common_code))
    if buggy_code_checker(buggy_code, default_start_code, default_test_code):
        # get the personalized solution
        while True & (API_attempt < 2):
            API_attempt += 1
            print("API_attempt", API_attempt)
            try:
                cleaned_fixed_code  = request_fixed_code_from_openai(df_question_line, buggy_code, default_start_code, default_test_code, most_common_code, unittest_code)
                return cleaned_fixed_code
            except Exception as e:
                traceback.print_exc()
                time.sleep(0.01)
                print(f"{API_attempt}-{e}-time_sleep")
                if API_attempt >= 2:
                    return personalized_most_common_solution
    else: # return False
        return personalized_most_common_solution
    
def generate_personalized_Parsons_blocks(df_question_line, buggy_code, cleaned_fixed_code, default_start_code, default_test_code, unittest_code, attempt = 0):
    buggy_code_for_blocks = clean_student_code(buggy_code, default_test_code)
    # generate the Parsons blocks
    # add paired distractors on their code when there are some meaningful comparison (one line similarity > 30%)
    code_comparison_pairs, fixed_lines, removed_lines, unchanged_lines, total_similarity = compare_code(buggy_code_for_blocks, cleaned_fixed_code, default_start_code)

    #print(code_comparison_pairs, fixed_lines, unchanged_lines, total_similarity)
    # decide the types of Parsons problems and generate correspoding distractors
    Parsons_type, distractors, distractor_candidates = personalize_Parsons_block(df_question_line, code_comparison_pairs, buggy_code, fixed_lines, removed_lines, unchanged_lines, total_similarity)
    unittest_flag = True
    if len(distractors) > 0:
        for distractor in distractors.copy().items():
            unittest_True = 0
            distractor_correct_line = distractor[0]
            # Prepare the code with distractors for unittest evaluation - cannot pass the tests this time
            code_with_distrator = generate_code_with_distrator(unchanged_lines, fixed_lines, distractor)
            #print("code_with_distractors\n", code_with_distrator)
            unittest_flag, cleaned_code_with_distractors = code_distractor_unittest_evaluation(code_with_distrator, default_start_code, default_test_code, unittest_code)
            while (unittest_flag == True) & (unittest_True <= 2):
                print("unittest_True", unittest_True)
                unittest_True += 1
                print("unittest_True", unittest_True)
                #def build_distractor_prompt(question_line, correct_line, regeneration_message, system_message=system_message,user_message=user_message,assistant_message=assistant_message):
                # new_distractor = get_personalized_distractor(build_distractor_prompt(df_question_line, distractor_correct_line[2],distractor[1]), distractor_correct_line[2],distractor[1])
                new_distractor = ""
                print("new_distractor",new_distractor,distractor_correct_line[2],distractor[1])
                if (new_distractor == "") or (new_distractor is None):
                    distractors.pop(distractor_correct_line)
                    print("break")
                    break
                else:
                    print("new_distractor", new_distractor)
                    print("distractors[distractor_correct_line]", distractors[distractor_correct_line])
                    print("distractors_with_new", distractors)
                    # Prepare the code with distractors for unittest evaluation - cannot pass the tests this time
                    code_with_distrator = generate_code_with_distrator(unchanged_lines, fixed_lines, (distractor_correct_line, new_distractor))
                    #print("code_with_distractors\n", code_with_distrator)
                    unittest_flag, cleaned_code_with_distractors = code_distractor_unittest_evaluation(code_with_distrator, default_start_code, default_test_code, unittest_code)
            
            if unittest_True > 2:
                print("pop-distractor")
                distractors.pop(distractor_correct_line)
                continue

    print("cleaned_fixed_code\n", cleaned_fixed_code)
    personalized_Parsons_block = generate_Parsons_block(Parsons_type, df_question_line, cleaned_fixed_code, unchanged_lines, fixed_lines, distractors)
    print("personalized_Parsons_block\n", personalized_Parsons_block)
    return personalized_Parsons_block





