import openai
import re

openai.api_key = ""
#openai.organization = "org-YEK3YQ7BAM9Ag39zqbbXyRnS"

system_message = """
Fix the provided Python [user-code] based on the provided [task-description] and [sample-solution] and generate [fixed-code]. 
The [fixed-code] should follow the existing solving strategy and solution path in [user-code], use the same type of [control_structures], use the same variable names as [user-code] and requires the least amount of edits from the [user-code].
For example, the [user-code] uses [control_structures], the [fixed-code] should also these [control_structures].
The [fixed-code] should pass the provided [unittest-code] and be more similar to the [user-code] than the [sample-solution].
The [fixed-code] should follow the Python style guide.
[task-description]: '{question_description}'
[end-task-description]

[sample-solution]: '{Example_student_solution}'
[end-solution]

[unittest-code]: '{Unittest_Code}'
[end-unittest-code]

[control-structures]: '{control_structures}'
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

def get_fixed_code(prompt_messages):
    completion = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = prompt_messages,
            stop = ["[end-fixed-code]"],
        )
    fixed_code = completion["choices"][0]["message"]["content"]
    #print("fixed_code here: \n", fixed_code)
    return fixed_code

def get_fixed_code_repeat(prompt_messages, old_fixed_code, situation):
    attachment = f"""
    The [old-fixed-code] is not {situation} to the [user-code]. Again, please try to generate a [fixed-code] that is more similar to the [user-code] than the [sample-solution] above.
    [old-fixed-code]: '{old_fixed_code}'
    [end-old-fixed-code]
    """
    prompt_messages[0]["content"] = prompt_messages[0]["content"] + attachment
    #print("prompt_messages[0]", prompt_messages[0]["content"])
    completion = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = prompt_messages,
            stop = ["[end-fixed-code]"],
        )
    fixed_code = completion["choices"][0]["message"]["content"]
    #print("fixed_code here: \n", fixed_code)
    return fixed_code

