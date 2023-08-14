import openai
import re
import time

openai.api_key = ""
#openai.organization = "org-YEK3YQ7BAM9Ag39zqbbXyRnS"

system_message = """Generate a one-line [distractor] from [correct-line] based on the provided [task-description] and [sample-solution]. 
This [distractor] should look samiliar as [correct-line] but contains one or two common syntax or semantic errors to highlight common misconceptions.
This [distractor] could not be the same as [correct-line].
This [distractor] should not be the [old-distractor].

[task-description]: '{question_description}'

[sample-solution]: '{Example_student_solution}'

[end-solution]

[old-distractor]: '{old_distractor}'
[end-old-distractor]
"""

# user message here is the example student answer
user_message = """[correct-line]:
{Example_correct_line}
[end-correct-line]"""


assistant_message = """[distractor]:
{Example_distractor}
[end-distractor]"""

def build_distractor_prompt(question_line, correct_line, old_distractor, system_message=system_message,user_message=user_message,assistant_message=assistant_message):
    system_message = system_message.format(
        question_description = question_line["w_question_description"].values[0],
        Example_student_solution = question_line["Example_student_solution"].values[0],
        old_distractor = old_distractor
    )
    user_message = user_message.format(
        Example_correct_line = question_line["Example_paired_distractor_correct"].values[0]
    )
    assistant_message = assistant_message.format(
        Example_distractor = question_line["Example_paired_distractor_wrong"].values[0]
    )
    prompt_code = "[correct-line]:\n" + correct_line + "\n[end-correct-line]"

    prompt_messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
                {"role": "user", "content": prompt_code},
            ]

    #print("prompt_messages here: \n", prompt_messages)
    
    return prompt_messages

def request_distractor_from_openai(prompt_messages):
    completion = openai.ChatCompletion.create(
            model = "gpt-4",
            messages = prompt_messages,
            stop = ["[end-distractor]"],
        )
    distractor = completion["choices"][0]["message"]["content"]
    distractor_pattern = r'\[distractor\]:\s*([\s\S]*)'

    if re.findall(distractor_pattern, distractor, re.DOTALL):
        distractor =  re.findall(distractor_pattern, distractor, re.DOTALL)[0].strip()
        # if the content inside of [fixed-code] does not start with def
    else:
        distractor = distractor
    return distractor

def get_personalized_distractor(prompt_messages, correct_line, distractor):
    while True:
        try:
            while (distractor.count('\n') != 0) or (distractor == "") or (distractor == correct_line):
                distractor = request_distractor_from_openai(prompt_messages)
                #print("distractor", distractor)
                if (distractor.count('\n') == 0) & (distractor != "") & (distractor != correct_line):
                    return distractor 
        except:
            time.sleep(0.1)


def generate_code_with_distrator(unchanged_lines, fixed_lines, distractor_tuple):
    print("distractor_tuple", distractor_tuple)
    # each distractor is like (corresponding_fixed_line, distractor)
    # (7, 18, '     def __str__(self):\n') location, length, actual code
    # for each element in unchanged_lines, add #settled to the end of the line
    unchanged_lines = [(line[0], line[1], line[2]) for line in unchanged_lines if line[2].strip()]
    fixed_lines = [(line[0], line[1], line[2]) for line in fixed_lines if line[2].strip()]
    key_fixed_line = distractor_tuple[0]
    fixed_line_code = key_fixed_line[2]
    line_indentation = fixed_line_code[:len(fixed_line_code) - len(fixed_line_code.lstrip())]
 
    # if distractor_dict[key_fixed_line] has a value, then remove the corresponding distractor_dict[key_fixed_line] from the fixed_lines
    for i, fixed_line in enumerate(fixed_lines):
        if key_fixed_line[2] == fixed_line[2]:
            #print("pop", key_fixed_line, fixed_line[2])
            fixed_lines.pop(i)
        else:
            continue
    blocks = fixed_lines + unchanged_lines + [(key_fixed_line[0]+0.5, key_fixed_line[0], line_indentation + distractor_tuple[1].strip())]

    print("All blocks", blocks)
    
    # Sort the blocks by their starting line number
    blocks = sorted(blocks, key=lambda x: x[0])

    # Extract the last element of each tuple and store them in a string
    actual_code_blocks = [t[-1] for t in blocks]
    code_with_distrator = '\n'.join(actual_code_blocks)

    print("code_with_single_distrator", code_with_distrator)
    return code_with_distrator