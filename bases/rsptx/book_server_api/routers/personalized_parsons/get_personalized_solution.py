import openai

openai.api_key = "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"
#openai.organization = "org-YEK3YQ7BAM9Ag39zqbbXyRnS"

system_message = """
Fix the provided Python [user-code] based on the provided [task-description] and [sample-solution] and generate [fixed-code]. 
The [fixed-code] should follow the existing solution path in [user-code] and be as similar as possible to the [user-code].

[task-description]: '{question_description}'

[sample-solution]: '{Example_student_solution}'
[end-solution]
"""

# user message here is the example student answer
user_message = """[user-code]:
{Example_buggy_code}
[end-user-code]"""


assistant_message = """[fixed-code]:
{Example_fixed_code}
[end-fixed-code]"""

def build_code_prompt(question_line, buggy_code, system_message=system_message,user_message=user_message,assistant_message=assistant_message):
    system_message = system_message.format(
        question_description = question_line["w_question_description"],
        Example_student_solution = question_line["Example_student_solution"]
    )
    user_message = user_message.format(
        Example_buggy_code = question_line["Example_buggy_code"]
    )
    assistant_message = assistant_message.format(
        Example_fixed_code = question_line["Example_fixed_code"]
    )
    prompt_code = "[user-code]:\n" + buggy_code + "\n[end-user-code]"

    prompt_messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": prompt_code},
            ]
    print("prompt_messages here: \n", prompt_messages)
    return prompt_messages

def get_fixed_code(prompt_messages):
    completion = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = prompt_messages,
            stop = ["[end-fixed-code]"],
        )
    fixed_code = completion["choices"][0]["message"]["content"]
    print("fixed_code here: \n", fixed_code)
    return fixed_code

       