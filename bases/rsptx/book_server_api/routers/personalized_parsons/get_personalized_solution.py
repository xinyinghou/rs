import os
import openai
import re
from dotenv import dotenv_values
import time

#Load environment file for secrets.
secrets = dotenv_values(".env")  

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

# Global variables
api_key_list_str = secrets["LST_OPENAI_API_KEY"]
api_key_list = api_key_list_str.split(',')
api_key_list = [api_key.strip() for api_key in api_key_list]
print("api_key_list: ", api_key_list)
current_index = 0
request_count = 0
reset_time = time.time() + 60  # Set initial reset time to one minute from now

def current_time():
    return time.time()

def get_actual_fixed_code(prompt_messages):
    current_api_key = api_key_list[current_index]
    print(f"Making API request with key: {current_api_key}-{current_index}")

    completion = openai.ChatCompletion.create(
            api_key = current_api_key,
            organization = secrets['OPENAI_organization'],
            api_base= secrets['openai_api_base'],
            api_type = secrets['openai_api_type'],
            api_version = secrets['API_VERSION'],
            engine = secrets['model'],
            temperature=0,  # Adjust this value to control randomness
            messages = prompt_messages,
            stop = ["[end-fixed-code]"],
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
        )
    fixed_code = completion["choices"][0]["message"]["content"]
    
    return fixed_code

def get_fixed_code(prompt_messages):
    global current_index, request_count, reset_time

    if current_time() >= reset_time:
        # Reset counters if one minute has passed
        request_count = 0
        reset_time = current_time() + 60

    if request_count == 30:
        # Switch to the next API key in the list
        current_index = (current_index + 1) % len(api_key_list)
        request_count = 0
        
    # Make the API request using the current_api_key
    fixed_code_response = get_actual_fixed_code(prompt_messages)

    # Update counters
    request_count += 1
    print(f"Request count of the key: {request_count}")

    return fixed_code_response


def get_fixed_code_repeat(prompt_messages, old_fixed_code, situation):
    attachment = f"""
    This [old-fixed-code] is not {situation} to the [user-code]. Again, please try to generate a [fixed-code] that is {situation} to the [user-code]. You can use [sample-solution] as a reference when generating the [fixed-code].
    [old-fixed-code]: '{old_fixed_code}'
    [end-old-fixed-code]
    """
    prompt_messages[0]["content"] = prompt_messages[0]["content"] + attachment
    #print("prompt_messages[0]", prompt_messages[0]["content"])
    completion = openai.ChatCompletion.create(
            model = "gpt-4-1106-preview",
            messages = prompt_messages,
            stop = ["[end-fixed-code]"],
        )
    fixed_code = completion["choices"][0]["message"]["content"]
    #print("fixed_code here: \n", fixed_code)
    return fixed_code

