# import necessary packages
import pandas as pd
import json

# import necessary functions from other files
from .buggy_code_checker import *
from .get_personalized_solution import *
from .evaluate_fixed_code import *
from .generate_parsons_blocks import *
from .get_parsons_code_distractors import *
from .personalize_parsons import *
from .end_to_end import *

# from buggy_code_checker import *
# from get_personalized_solution import *
# from evaluate_fixed_code import *
# from generate_parsons_blocks import *
# from get_parsons_code_distractors import *
# from personalize_parsons import *
# from end_to_end import *

# with open("example_buggy_code.json", "r") as json_file:
#     dict_buggy_code = json.load(json_file)

# Include: Problem Name, Question Description, Cluster
# Example_student_solution, Example_buggy_code, Example_fixed_code
df_question_bank = pd.read_csv("Classroom_Evaluation_Material.csv").fillna('')
print("start_to: get_personalized_parsons_help")

def parsons_help(student_code, problem_name, personalization):
    input_dict = {
        "Problem Name":problem_name,
        "CF (Code)":student_code
    }
    return get_parsons_help(input_dict, df_question_bank, personalization)

problem_name = "table_reservation_oc"
student_code = "def table_reservation(reservation_dict, guest_num):   for , value in reservation_dict():        for item in value:            for key,value in item.values():                if value == guest_num:                    number + 1    return count"
print('here_student_code\n', student_code)
personalized_code_solution, personalized_Parsons_block = parsons_help(student_code, problem_name, personalization=True)
common_code_solution, common_Parsons_block = parsons_help(student_code, problem_name, personalization=False)
# personalized_code_solution, personalized_Parsons_block = get_personalized_parsons_help(dict_buggy_code, df_question_bank)

print("Experimental Condition: personalized_Parsons_block\n", personalized_code_solution, "\n", personalized_Parsons_block)
print("Control Condition: most_common_Parsons_block\n", common_code_solution, "\n", common_Parsons_block)

