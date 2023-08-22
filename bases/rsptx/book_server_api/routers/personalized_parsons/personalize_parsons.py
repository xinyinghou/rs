import difflib
import pandas as pd
from collections import namedtuple
from .get_parsons_code_distractors import *
from .generate_parsons_blocks import *
from .token_compare import *
# compare the similarity between the student code and the fixed code

#  It prints the difference between the two code snippets line by line using a loop. It also prints the similarity ratio.

# Please note that the difflib module compares lines based on their content, 
# so it may not capture more complex differences, such as code structure or logic.

CodeComparison = namedtuple('CodeComparison', ['student_removed', 'fixed_modified', 'line_similarity'])


def compare_code(buggy_code, fixed_code, default_start_code):

    #print(fixed_code)
    code_comparison_pairs = []

    # Split the code into lines
    student_lines = buggy_code.splitlines(keepends=True)
    fixed_lines = fixed_code.splitlines(keepends=True)

    # Perform a line-based comparison
    diff = list(difflib.Differ().compare(student_lines, fixed_lines))

    # Calculate similarity ratio without the starting line
    buggy_code_no_starting = '\n'.join([line for line in buggy_code.split('\n') if line != default_start_code])
    fixed_code_no_starting = '\n'.join([line for line in fixed_code.split('\n') if line != default_start_code])

    total_similarity = code_similarity_score(buggy_code_no_starting, fixed_code_no_starting)

    #print("diff here\n", diff)
    # Get the line similarity pairs
    line_similarity_pairs = []
    fixed_lines = []
    removed_lines = []
    unchanged_lines = []
    discarded_lines = []
    for i, line in enumerate(diff):
        if line.startswith('+'):
            fixed_lines.append((i, len(line[1:].strip()), line[2:]))
        elif line.startswith('-'):
            removed_lines.append((i, len(line[1:].strip()), line[2:]))
        elif line.startswith('?'):
            discarded_lines.append((i, len(line[1:].strip()), line[2:]))
        else:
            unchanged_lines.append((i, len(line[1:].strip()), line[2:]))
    #print("compare_code", fixed_lines, removed_lines, unchanged_lines)
    # Pair up the added and removed lines
    max_len = max(len(fixed_lines), len(removed_lines))

    for i in range(max_len):
        try:
            line_similarity_pairs.append((['student', removed_lines[i]], ['fixed', fixed_lines[i]]))
        except IndexError:
            if len(fixed_lines) > len(removed_lines):
                line_similarity_pairs.append((['student', (0, '', '')], ['fixed', fixed_lines[i]]))
            else:
                line_similarity_pairs.append((['student', removed_lines[i]], ['fixed', (0, '', '')]))
            
    # one line similarity > 30%
    # Calculate similarity ratio only for different lines
    for i, pair in enumerate(line_similarity_pairs):
        if pair[0][1] != pair[1][1]:
            similarity = code_similarity_score(pair[0][1][2], pair[1][1][2])
            pair = CodeComparison(pair[0][1], pair[1][1], similarity)
            code_comparison_pairs.append(pair)
     
    return code_comparison_pairs, fixed_lines, removed_lines, unchanged_lines, total_similarity

def normalize_and_compare_lines(line1, line2):
    # Normalize indentation
    indentation1 = re.match(r'^(\s*)', line1).group(1)
    indentation2 = re.match(r'^(\s*)', line2).group(1)
    line1_normalized = line1.replace(indentation1, '')
    line2_normalized = line2.replace(indentation2, '')

    # Remove extra whitespaces
    line1_cleaned = re.sub(r'\s+', '', line1_normalized).strip()
    line2_cleaned = re.sub(r'\s+', '', line2_normalized).strip()

    # Compare normalized lines, highlight the indentation differences
    if line1_cleaned != line2_cleaned:
        return False
    elif (line1_cleaned == line2_cleaned) and (indentation1!=indentation2):
        return False
    elif (line1_cleaned == line2_cleaned) and (indentation1 == indentation2):
        return True

def find_distractor(fixed_line, removed_lines):
    removed_lines = [tup[2] for tup in removed_lines]
    highest_similarity = 0.7
    distractor_line = False
    print("removed_lines",removed_lines)
    # check whether there is any line achieved a high similarity than the line of comparable location
    for student_line in removed_lines:
        similarity = code_similarity_score(fixed_line, student_line)
        if similarity > highest_similarity:
            highest_similarity = similarity
            distractor_line = student_line
            
    return highest_similarity, distractor_line



def generate_unique_distractor_dict(distractor_dict):
    # Group values by value[1]
    value_groups = {}
    for key, value in distractor_dict.items():
        _, code = value
        if code not in value_groups:
            value_groups[code] = []
        value_groups[code].append((key, value))

    # Select the highest similarity value for each value[1]
    result_distractor_dict = {}
    for code, group in value_groups.items():
        highest_similarity = max(group, key=lambda x: x[1][0])
        result_distractor_dict[highest_similarity[0]] = highest_similarity[1][1]    

    return result_distractor_dict

# Decide which type of Parsons problem we will generate and generate the corresponding distractors
def personalize_Parsons_block(df_question_line, code_comparison_pairs, buggy_code, fixed_lines, removed_lines, unchanged_lines, total_similarity):
    #print(code_comparison_pairs, total_similarity)
    distractors = {}
    distractor_candidates = []
    print("code_comparison_pairs\n", len(code_comparison_pairs), code_comparison_pairs, "total_similarity\n", total_similarity)
    if total_similarity < 0.30:
        return "Full", {}, []
    else:
        # if has 3 or more than 3 fixed lines (movable blocks)
        if len(code_comparison_pairs)>=3:
            # use students' own buggy code as resource to build distractors
            for pair in code_comparison_pairs:
                normalize_and_compare = normalize_and_compare_lines(pair[0][2], pair[1][2])
                if normalize_and_compare == False:
                    # if the student code is wrong (not just a different way to write the same code), generate a distractor using student buggy code
                    distractor_similarity, distractor = find_distractor(pair[1][2], removed_lines)
                    if distractor != False:
                        distractors[pair[1]] =  (distractor_similarity, distractor)
                    else:
                        continue 
            # check to make sure all the paired distractors are different, if some are same, pop up the key value with the least similarity - leave it as a movable line
            if len(distractors) > 0:
                distractors = generate_unique_distractor_dict(distractors)
            else:
                distractors = {}

            return "Partial_Own", distractors, distractor_candidates
        # if the movable blocks are less than 3, then still generate distractors from student code first, and use LLM-generated code to make up
        elif (len(code_comparison_pairs)<3) and (len(code_comparison_pairs)> 0):
            for pair in code_comparison_pairs:
                normalize_and_compare = normalize_and_compare_lines(pair[0][2], pair[1][2])
                if normalize_and_compare == False:
                    # if the student code is wrong (not just a different way to write the same code), generate a distractor using student buggy code
                    distractor_similarity, distractor = find_distractor(pair[1][2], removed_lines)
                    if distractor != False:
                        distractors[pair[1]] =  (distractor_similarity, distractor)
                    else:
                        continue 
            # check to make sure all the paired distractors are different, if some are same, pop up the key value with the least similarity
            if len(distractors) > 0:
                distractors = generate_unique_distractor_dict(distractors)
            else:
                distractors = {}

            # given that we need to provide at least three distractors for them
            # check whether need to generate distractors from the top N longest lines
            if len(distractors) > 0:
                distractor_keys = [key[2] for key in distractors.keys()]
            else:
                distractor_keys = []

            # pass to the LLM distractor generation station
            distractor_candidate_depot = [item for item in fixed_lines + unchanged_lines if item[2] not in distractor_keys]
            print("distractor_candidate_depot", distractor_candidate_depot)
            candidate_num = 3 - len(distractors)
            
            distractor_candidates = sorted(distractor_candidate_depot, key=lambda x: x[1], reverse=True)[:candidate_num]

            for distractor_candidate in distractor_candidates:
                print("distractor_candidate", distractor_candidate)
                #def build_distractor_prompt(question_line, correct_line, regeneration_message, system_message=system_message,user_message=user_message,assistant_message=assistant_message):
                distractor = get_personalized_distractor(build_distractor_prompt(df_question_line, distractor_candidate[2],""), distractor_candidate[2],"")
                # the keys should be tuple (location, length, code) instead of only the actual code
                while distractor in distractors.values():
                    print("regenerate a distractor", distractor)
                    distractor = get_personalized_distractor(build_distractor_prompt(df_question_line, distractor_candidate[2],distractor), distractor_candidate[2],distractor)
                
                distractors[distractor_candidate] = distractor
        
            return "Partial_Own_Random", distractors, distractor_candidates


