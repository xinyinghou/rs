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
#from similarity_compare import *

with open("example_buggy_code.json", "r") as json_file:
    dict_buggy_code = json.load(json_file)

# Include: Problem Name, Question Description, Cluster
# Example_student_solution, Example_buggy_code, Example_fixed_code
df_question_bank = pd.read_csv("Evaluation_Material_STUDY.csv").fillna('')
print("start_to: get_personalized_parsons_help")

def personalized_help(student_code, problem_name):
    input_dict = {
        "Problem Name":problem_name,
        "CF (Code)":student_code
    }
    return get_personalized_parsons_help(input_dict, df_question_bank)

problem_name = "has_22_acop"
student_code = "def has22(nums):\n    for num in nums:\n        if num == 2 and flag == 0:\n            flag = 1\n            return True\n        elif num != 2:\n            flag = 0\n            return False"
        

personalized_code_solution, personalized_Parsons_block = personalized_help(student_code, problem_name)

# personalized_code_solution, personalized_Parsons_block = get_personalized_parsons_help(dict_buggy_code, df_question_bank)

print("Control Condition: personalized_code_solution\n", personalized_code_solution)

print("Experimental Condition: personalized_Parsons_block\n", personalized_Parsons_block)

# put personalized_Parsons_block into a txt file
with open("personalized_Parsons_block.txt", "w") as text_file:
    text_file.write(personalized_Parsons_block)