# import difflib
import pandas as pd
from collections import namedtuple
# import textwrap
# import json
import re
from collections import OrderedDict

def check_indentation_level(line):
    match = re.match(r'^(\s*)', line)
    indentation_level = len(match.group(1))
    return indentation_level

# generate corresponding Parsons problems for each type
def generate_Parsons_block(Parsons_type, df_question_line, cleaned_fixed_code, unchanged_lines, fixed_lines, distractors):
    problem_description = df_question_line["p_question_description"].values[0]
    # if total_similairity is less than 30%, return a fully movable Parsons problem
    if Parsons_type == "Full":
        return generate_full_Parsons(cleaned_fixed_code)
    else:
        return generate_partial_Parsons(Parsons_type, unchanged_lines, fixed_lines, distractors)
    
# Generate full Parsons problems
def generate_full_Parsons(fixed_code):
    # Remove empty lines
    fixed_code = re.sub(r'\n\s*\n', '\n', fixed_code)
    # Extract code blocks based on indentation patterns
    matches = re.findall(r'(?<=\n)(\s*)(.*)', fixed_code)
    # Remove empty and whitespace-only blocks and add four indentation spaces to each block
    blocks = ['    ' + block[0] + block[1] for block in matches if block[1].strip()]
    
    blocks = aggregate_code_to_full_Parsons_block(blocks)

    return convert_code_to_block(blocks)

# Generate the partial Parsons problem with unmovable blocks and distractors
def generate_partial_Parsons(Parsons_type, unchanged_lines, fixed_lines, distractor_tuple_dict):
    # each distractor is like (corresponding_fixed_line, distractor)
    # (7, 18, '     def __str__(self):\n') location, length, actual code
    # for each element in unchanged_lines, add #settled to the end of the line
    
    # Remove the empty lines in the fixed_lines and unchanged_lines - when the length are 0
    #print("distractor_tuple_dict", distractor_tuple_dict)
    fixed_lines = [(line[0], line[1], line[2].rstrip()+ '\n') for line in fixed_lines if line[2].strip()]
    unchanged_lines = [(line[0], line[1], line[2].rstrip() + ' #settled\n') for line in unchanged_lines if line[2].strip()]
    if Parsons_type == "Partial":
        blocks = fixed_lines + unchanged_lines
    else:
        longest_unchanged_line = max(unchanged_lines, key=lambda x: x[1])
        #print("longest_unchanged_line", longest_unchanged_line)
        unchanged_lines.remove(longest_unchanged_line)
        line_from_unchanged_to_fixed = (longest_unchanged_line[0], longest_unchanged_line[1], longest_unchanged_line[2].replace("#settled\n", "\n"))
        blocks = fixed_lines + [line_from_unchanged_to_fixed] + unchanged_lines
    
    for fixed_line_key in distractor_tuple_dict.keys():
        #print("key_fixed_line", fixed_line_key)
        blocks = [(line[0], line[1], line[2].rstrip() + ' #matched-fixed\n') if line[2].strip() == fixed_line_key[2].strip() else (line[0], line[1], line[2]) for line in blocks]
        fixed_line_code = fixed_line_key[2]
        line_indentation = fixed_line_code[:len(fixed_line_code) - len(fixed_line_code.lstrip())]
        #print("distractor_tuple_dict[key_fixed_line][2].strip()", distractor_tuple_dict[fixed_line_key])
        if type(distractor_tuple_dict[fixed_line_key]) == tuple:
            distractor_tuple_dict[fixed_line_key] = (fixed_line_key[0]+0.5, fixed_line_key[0], line_indentation + distractor_tuple_dict[fixed_line_key][2].strip() + " #paired")
        elif type(distractor_tuple_dict[fixed_line_key]) == str:
            distractor_tuple_dict[fixed_line_key] = (fixed_line_key[0]+0.5, fixed_line_key[0], line_indentation + distractor_tuple_dict[fixed_line_key].strip() + " #paired")
    # add both unchanged_lines and fixed_lines of the fixed solution to blocks
    # add distractors to blocks
    blocks = blocks + list(distractor_tuple_dict.values())

    # add the fourth value to each tuple in blocks
    # Iterate over the list and modify the tuples
    for i, tpl in enumerate(blocks):
        actual_code = tpl[2]
        indentation = check_indentation_level(actual_code)  # Modify the second value based on the length of the third value
        # Add four indentation spaces to each block
        blocks[i] = (tpl[0], tpl[1], indentation, '    ' + actual_code)
    #print(blocks)
    # # Extract the last element of each tuple (the actual code) and store them in a string
    # lst_blocks = [blocks[2] for blocks in blocks]
    # print("lst_blocks", lst_blocks)
    # # Add four indentation spaces to each block
    # lst_blocks = ['    ' + block for block in lst_blocks]
    blocks = aggregate_code_to_Parsons_block_with_distractor(blocks)
    #print("blocks after aggregate_code_to_Parsons_block_with_distractor", blocks)
    return convert_code_to_block(blocks)

def reset_distractor_flag(distractor_block):
    has_paired = False

    for i, item in enumerate(distractor_block):
        if "#paired" in item:
            distractor_block[i] = item.replace("#paired", "")
            has_paired = True
        else:
            distractor_block[i] = item.replace("#settled", "")

    if has_paired:
        print("distractor_block[-1] ", distractor_block[-1])
        distractor_block[-1] = distractor_block[-1].replace("\n", "") + " #paired" + "\n"

    return distractor_block

def extract_distractor_Parsons_block(blocks, distractor_index):
    # Find the line with #paired and extract the neighboring tuples with the same third value
    neighbor_tuples = []

    current_indentation = blocks[distractor_index][2]
    
    # Collect the neighboring tuples with the same third value until the third value changes
    for tpl in blocks[distractor_index::-1]:
        if tpl[2] == current_indentation:
            neighbor_tuples.insert(0, tpl)
        else:
            break

    for tpl in blocks[distractor_index+1:]:
        if tpl[2] == current_indentation:
            neighbor_tuples.append(tpl)
        else:
            break
    
    # Create two separate lists based on the extracted neighbor tuples
    fixed_line_block = reset_distractor_flag([tpl[3] for tpl in neighbor_tuples if "#paired" not in tpl[3]])
    fixed_line_block = '\n'.join([block.rstrip('\n') for block in fixed_line_block])
    distractor_block = reset_distractor_flag([tpl[3] for tpl in neighbor_tuples if "#matched-fixed" not in tpl[3]])
    distractor_block = '\n'.join([block.rstrip('\n') for block in distractor_block])
    print("fixed_line_block, distractor_block", fixed_line_block, distractor_block)
    return fixed_line_block, distractor_block

def aggregate_code_to_Parsons_block_with_distractor(blocks):
    # Sort the blocks by their starting line number and then indentation level
    blocks = sorted(blocks, key=lambda tpl: (tpl[0], tpl[1]))
    current_indent = blocks[0][2]
    distractor_indent = ""
    all_Parsons_blocks = {}
    Parsons_block = ""
    for block in blocks:
        this_indent = block[2]
        if '#matched-fixed' in block[3]:
            if Parsons_block != "":
                all_Parsons_blocks[block[0]-0.5] = Parsons_block
                Parsons_block = ""
            continue

        if '#paired' in block[3]:
            if Parsons_block != "":
                all_Parsons_blocks[block[0]-0.5] = Parsons_block
                Parsons_block = ""
            distractor_indent = this_indent
            current_indent = this_indent
            print(blocks, blocks.index(block))
            fixed_line_block, distractor_block = extract_distractor_Parsons_block(blocks, blocks.index(block))
            all_Parsons_blocks[block[0]+0.1] = fixed_line_block
            all_Parsons_blocks[block[0]+0.2] = distractor_block
            #print("fixed_line_block\n", fixed_line_block, "distractor_block\n", distractor_block)
        if (this_indent == current_indent) & (current_indent != distractor_indent):
            Parsons_block += str(block[3]) 

        if this_indent != current_indent:
            if Parsons_block != "":
                all_Parsons_blocks[block[0]] = Parsons_block
                Parsons_block = ""

            Parsons_block = str(block[3])
            current_indent = this_indent 
    if Parsons_block != "":
        all_Parsons_blocks[block[0]] = Parsons_block
    #print("all_Parsons_blocks", all_Parsons_blocks)
    all_Parsons_blocks = OrderedDict(sorted(all_Parsons_blocks.items()))
    all_Parsons_blocks = list(all_Parsons_blocks.values())
    #print(all_Parsons_blocks)
    all_Parsons_blocks = [item.replace('#matched-fixed', '') if '#matched-fixed' in item  else item for item in all_Parsons_blocks]
    return all_Parsons_blocks

def aggregate_code_to_full_Parsons_block(blocks):
    current_indent = check_indentation_level(blocks[0])
    all_Parsons_blocks = []
    Parsons_block = ""
    distractor_indent = 0
    for block in blocks:
        if not block.endswith('\n'):
                block += '\n'
        this_indent = check_indentation_level(block)
        if this_indent == current_indent:
            Parsons_block += block 
        else:
            all_Parsons_blocks.append(Parsons_block)
            Parsons_block = block
            current_indent = this_indent

    all_Parsons_blocks.append(Parsons_block)

    return all_Parsons_blocks

def convert_code_to_block(blocks):
    for i, block in enumerate(blocks):
            block = re.sub(r'\n+', '\n', block)

            # Add -----\n at the beginning of the first block
            if not block.endswith('\n'):
                block += '\n'

            if i == 0:
                blocks[0] = block + '---\n'

            # No ==== after the last block
            elif i == len(blocks) - 1:
                blocks[i] = block 
            # Add ===== after each block and then \n
            elif (i != 0) & (i < len(blocks) - 1):
                blocks[i] = block + '---\n'
    # Save the blocks into a string
    return ''.join(blocks)

