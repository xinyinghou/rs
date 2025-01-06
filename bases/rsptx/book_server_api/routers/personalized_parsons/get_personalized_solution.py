import os
from openai import OpenAI
import re
from dotenv import load_dotenv
from dotenv import dotenv_values
import time
import sqlite3
import random
from datetime import datetime
import sys
#from evaluate_fixed_code import *
from .evaluate_fixed_code import *

API_key = ""

system_message = """
Fix the provided Python [user-code] based on the provided [task-description] and [sample-solution] and generate the [fixed-code]. 
The [fixed-code] should pass the provided [unittest-code] and be more similar to the [user-code] than the [sample-solution].
When possible, the [fixed-code] should follow the existing solving strategy and solution path in [user-code], use the same type of [control_structures], use the same variable names as [user-code] and requires the least amount of edits from the [user-code].
For example, the [user-code] uses [control_structures], the [fixed-code] should also use these [control_structures] when establishing the solution.
The [fixed-code] should follow the Python style guide.
[task-description]: '{question_description}'
[end-task-description]

[sample-solution]: '{Example_student_solution}'
[end-solution]

[unittest-code]: '{Unittest_Code}'
[end-unittest-code]

[control-structures]: '{control_structures}'
[end-control-structures]
"""

# user message here is the example student answer
user_message = """[user-code]:
{Example_buggy_code}
[end-user-code]"""

assistant_message = """[fixed-code]:
{Example_fixed_code}
[end-fixed-code]"""

def find_control_structures(buggy_code):
    control_structures = []

    # Regular expressions for different control structures and loops
    regex_for = r'for\s+\w+\s+in\s+\w+\s*:'
    regex_while = r'while\s+\w+\s*:'
    regex_for_range = r'for\s+\w+\s+in\s+range\('
    regex_for_items = r'for\s+\w+\s*,\s*\w+\s+in\s+\w+\.items\(\)'
    regex_if_elif = r'if\s+\w+\s*:\s*|elif\s+\w+\s*:'
    regex_if_else = r'if\s+\w+\s*:\s*|else\s*:'

    # Check for each regex pattern in the code snippet
    if re.search(regex_for, buggy_code):
        control_structures.append("for-loop")
    if re.search(regex_while, buggy_code):
        control_structures.append("while-loop")
    if re.search(regex_for_range, buggy_code):
        control_structures.append("for-range-loop")
    if re.search(regex_for_items, buggy_code):
        control_structures.append("for-items-loop")
    if re.search(regex_if_elif, buggy_code):
        control_structures.append("if-or-elif-condition")
    if re.search(regex_if_else, buggy_code):
        control_structures.append("if-or-else-condition")

    return control_structures

def build_code_prompt(question_line, buggy_code, system_message=system_message,user_message=user_message,assistant_message=assistant_message):
    control_structures = find_control_structures(buggy_code)
    system_message = system_message.format(
        question_description = question_line["w_question_description"].values[0],
        Example_student_solution = question_line["Example_student_solution"].values[0],
        Unittest_Code = question_line["Unittest_Code"].values[0],
        control_structures = control_structures
    )
    user_message = user_message.format(
        Example_buggy_code = question_line["Example_buggy_code"].values[0]
    )
    assistant_message = assistant_message.format(
        Example_fixed_code = question_line["Example_fixed_code"].values[0]
    )
    prompt_code = "[user-code]:\n" + buggy_code + "\n[end-user-code]"
    prompt_messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": prompt_code},
            ]
    #print("prompt_messages here: \n", prompt_messages)
    return prompt_messages

        
def get_actual_fixed_code(prompt_messages, attempt_type, situation, old_fixed_code):
    if attempt_type == "new":
        prompt_messages = prompt_messages
    elif attempt_type == "repeat":
        attachment = f"""
        This [old-fixed-code] is not {situation} to the [user-code]. Again, please try to generate a [fixed-code] that is {situation} to the [user-code]. You can use [sample-solution] as a reference when generating the [fixed-code].
        [old-fixed-code]: '{old_fixed_code}'
        [end-old-fixed-code]
        """
        prompt_messages[0]["content"] = prompt_messages[0]["content"] + attachment

    client = OpenAI(api_key=API_key)

    raw_completion_response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,  # Adjust this value to control randomness
        messages = prompt_messages,
        stop = ["[end-fixed-code]"],
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        seed=1234,
        )
    
    completion = raw_completion_response.choices[0].message
    fixed_code = completion.content
    print(fixed_code)
    # response_headers = raw_completion_response.headers
    
    #print("response_headers", response_headers, "completion", completion)
    # x-ratelimit-remaining-requests, x-ratelimit-reset-requests
    # remaining_requests = response_headers['x-ratelimit-remaining-requests']
    # # remaining_requests = 30 - (40-int(response_headers['x-ratelimit-remaining-requests']))
    
    # print("remaining_requests", remaining_requests, "fixed_code", fixed_code)
    #reset_requests = response_headers['x-ratelimit-reset-requests']
    
    return fixed_code


def get_fixed_code(df_question_line, buggy_code, default_test_code, attempt_type, situation, old_fixed_code):
    # first check if the buggy code is in the cache
    cleaned_buggy_code = clean_student_code(buggy_code, default_test_code)
    print("get_fixed_code-cleaned_buggy_code", cleaned_buggy_code)

    prompt_messages = build_code_prompt(df_question_line, buggy_code)
    # Make the API request using the current_api_key
    fixed_code_response = get_actual_fixed_code(prompt_messages, attempt_type, situation, old_fixed_code)

    return fixed_code_response




