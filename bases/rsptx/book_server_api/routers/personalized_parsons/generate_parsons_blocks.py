import difflib
import pandas as pd
from collections import namedtuple
import textwrap
import json
import re
from collections import OrderedDict

def check_indentation_level(line):
    match = re.match(r'^(\s*)', line)
    indentation_level = len(match.group(1))
    return indentation_level

# generate corresponding Parsons problems for each type
def generate_Parsons_block(Parsons_type, df_question_line, cleaned_fixed_code, unchanged_lines, fixed_lines, distractors):
    problem_description = df_question_line["w_question_description"][0].replace("\\n", "\n")
    # if total_similairity is less than 30%, return a fully movable Parsons problem
    if Parsons_type == "Full":
        return generate_full_Parsons(cleaned_fixed_code, problem_description)
    else:
        return generate_partial_Parsons(Parsons_type, problem_description, unchanged_lines, fixed_lines, distractors)

def break_and_indent(text, max_line_length, indent=4):
    lines = []
    current_line = ""
    
    words = text.split()
    
    for word in words:
        if len(current_line) + len(word) + 1 > max_line_length:
            lines.append(" " * indent + current_line)
            current_line = word
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
    
    if current_line:
        lines.append(" " * indent + current_line)
    
    return '\n'.join(lines)


# Generate full Parsons problems
def generate_full_Parsons(fixed_code, problem_description):
    # Remove empty lines
    fixed_code = re.sub(r'\n\s*\n', '\n', fixed_code)
    print("fixed_code", fixed_code)
    # Extract code blocks based on indentation patterns
    matches = re.findall(r'(?<=\n)(\s*)(.*)', fixed_code)
    matches = [('',fixed_code.split('\n')[0])] + matches
    # if no indentation, add to matches as ("", code_line)
    # Remove empty and whitespace-only blocks and add four indentation spaces to each block
    blocks = ['    ' + block[0] + block[1] for block in matches if block[1].strip()]
    print("full_blocks",blocks)
    blocks = aggregate_code_to_full_Parsons_block(blocks)
    print("full_blocks_aggregate_code_to_full_Parsons_block",blocks)
    problem_description = break_and_indent(problem_description, max_line_length=80)
    Parsons_problem = convert_code_to_block(blocks)
    return Parsons_problem

# Generate the partial Parsons problem with unmovable blocks and distractors
def generate_partial_Parsons(Parsons_type, problem_description, unchanged_lines, fixed_lines, distractor_tuple_dict):
    # each distractor is like (corresponding_fixed_line, distractor)
    # (7, 18, '     def __str__(self):\n') location, length, actual code
    # for each element in unchanged_lines, add #settled to the end of the line
    
    # Remove the empty lines in the fixed_lines and unchanged_lines - when the length are 0
    #print("distractor_tuple_dict", distractor_tuple_dict)
    fixed_lines = [(line[0], line[1], line[2].rstrip()+ '\n') for line in fixed_lines if line[2].strip()]
    matched_fixed_lines = []
    print("Parsons_type", Parsons_type, "unchanged_lines", unchanged_lines, "fixed_lines", fixed_lines, "distractor_tuple_dict", distractor_tuple_dict)
    if (Parsons_type ==  "Partial_Own"):
        unchanged_lines = [(line[0], line[1], line[2].rstrip() + ' #settled\n') for line in unchanged_lines if line[2].strip()]
        print("blocks", unchanged_lines)
    # some unchanged lines might be moved to the distractor list
    elif (Parsons_type ==  "Partial_Own_Random"):
        # check whether the unchanged lines appear in distrctor_tuple_dict, if so, remove them from unchanged_lines
        for fixed_line_key in distractor_tuple_dict.keys():
            for line in unchanged_lines:
                if line[2].strip() == fixed_line_key[2].strip():
                    unchanged_lines.remove(line)
                    matched_fixed_lines.append(line)
        unchanged_lines = [(line[0], line[1], line[2].rstrip() + ' #settled\n') for line in unchanged_lines if line[2].strip()]           
    
    blocks = fixed_lines + unchanged_lines + matched_fixed_lines
    print("blocks", blocks)
    for fixed_line_key in distractor_tuple_dict.keys():
        print("key_fixed_line", fixed_line_key)
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
    print("blocks after adding distractors", blocks)
    # add the fourth value to each tuple in blocks
    # Iterate over the list and modify the tuples
    for i, tpl in enumerate(blocks):
        actual_code = tpl[2]
        indentation = check_indentation_level(actual_code)  # Modify the second value based on the length of the third value
        # Add four indentation spaces to each block
        blocks[i] = (tpl[0], tpl[1], indentation, '    ' + actual_code)
    print("blocks after adding indentations", blocks)
    # # Extract the last element of each tuple (the actual code) and store them in a string
    # lst_blocks = [blocks[2] for blocks in blocks]
    # print("lst_blocks", lst_blocks)
    # # Add four indentation spaces to each block
    # lst_blocks = ['    ' + block for block in lst_blocks]
    blocks = aggregate_code_to_Parsons_block_with_distractor(blocks)
    #print("blocks after aggregate_code_to_Parsons_block_with_distractor", blocks)
    problem_description = break_and_indent(problem_description, max_line_length=80)
    Parsons_problem = convert_code_to_block(blocks)
    return Parsons_problem

def keep_last_hash_tag_lines(input_string, hash_tag):
    lines = input_string.split('\n')
    output_lines = []
    found_last_settled = False
    for line in reversed(lines):
        if (hash_tag in line) & (not found_last_settled):
            output_lines.append(line)
            found_last_settled = True
        elif (hash_tag in line) & (found_last_settled == True):
            line = line.replace(hash_tag, "")
            output_lines.append(line)
        else:
            output_lines.append(line)
    return '\n'.join(reversed(output_lines))

def reset_distractor_flag(distractor_block):
    distractor_block = list(filter(None, distractor_block))
    has_paired = False

    for i, item in enumerate(distractor_block):
        if "#paired" in item:
            distractor_block[i] = item.replace("#paired", "")
            has_paired = True
        else:
            distractor_block[i] = item.replace("#settled", "")

    if has_paired:
        #print("distractor_block[-1] ", distractor_block[-1])
        distractor_block[-1] = distractor_block[-1].replace("\n", "") + " #paired" + "\n"
            
    print("distractor_block_all ", distractor_block)

    return distractor_block


def extract_distractor_Parsons_block(distractor_block_stack):
    # Count how many #paired in distractor_block_stack
    print("distractor_block_stack", distractor_block_stack)
    count_distractor = sum(1 for block_tuple in distractor_block_stack if "#paired" in block_tuple[1])

    if count_distractor == 1:
        # Create two separate lists based on the extracted neighbor tuples
        fixed_line_block = reset_distractor_flag([tpl[1] for tpl in distractor_block_stack if "#paired" not in tpl[1]])
        fixed_line_block = '\n'.join([block.rstrip('\n') for block in fixed_line_block])
        distractor_line_block = reset_distractor_flag([tpl[1] for tpl in distractor_block_stack if "#matched-fixed" not in tpl[1]])
        distractor_line_block = '\n'.join([block.rstrip('\n') for block in distractor_line_block])
        #print("fixed_line_block, distractor_block", fixed_line_block, distractor_block)
        #print("fixed_line_block", fixed_line_block, "distractor_block", distractor_line_block)
        return fixed_line_block, distractor_line_block
    # If more than one match-paired distractors in a distractor block stack
    # then create fixed_line and distractor block (include more than one match-paired distractors)
    else: 
        # only keep the last line that has "#paired", one is settled + all paired; one is settled + all match-fixed
        d_stack_remove_matched_lines = [tup for tup in distractor_block_stack if '#matched-fixed' not in tup[1]]
        print("d_stack_remove_matched_lines", d_stack_remove_matched_lines)
        d_blocks = ''.join(str(block[1]) for block in d_stack_remove_matched_lines)
        print("d_blocks", d_blocks)
        d_block_keep_last_distractor = keep_last_hash_tag_lines(d_blocks, "#paired")
        print("d_block_keep_last_distractor", d_block_keep_last_distractor)
        d_blocks_list = reset_distractor_flag(d_block_keep_last_distractor.split('\n'))
        print("d_blocks_list", d_blocks_list)
        distractor_line_block = '\n'.join([block.rstrip('\n') for block in d_blocks_list])

        f_stack_remove_matched_lines = [tup for tup in distractor_block_stack if '#paired' not in tup[1]]
        print("f_stack_remove_matched_lines", f_stack_remove_matched_lines)
        f_blocks = ''.join(str(block[1]) for block in f_stack_remove_matched_lines)
        f_block_keep_last_distractor = keep_last_hash_tag_lines(f_blocks, "#matched-fixed")
        f_blocks_list = reset_distractor_flag(f_block_keep_last_distractor.split('\n'))
        fixed_line_block = '\n'.join([block.rstrip('\n') for block in f_blocks_list])

        print("fixed_line_block_multi", fixed_line_block, "distractor_block_multi", distractor_line_block)
        return fixed_line_block, distractor_line_block

def aggregate_code_to_Parsons_block_with_distractor(blocks):
    blocks = [(tup[0], tup[1], tup[2], tup[3] if tup[3].endswith('\n') else tup[3] + '\n') for tup in blocks]
    # Sort the blocks by their starting line number and then indentation level
    blocks = sorted(blocks, key=lambda tpl: (tpl[0], tpl[1]))
    current_indent_in_block_stack = blocks[0][2]
    distractor_indent = False
    all_Parsons_blocks = {}
    block_stack = []
    match_fixed_verification = False
    print("all_original_blocks\n", blocks)
    for index, block in enumerate(blocks):
        this_indent = block[2]
        # check wehther the current stack will be marked as a distractor block stack
        if ('#paired' in block[3]):
            print("#paired-#matched-fixed", block[3])
            distractor_indent = this_indent
        print("index", index, len(blocks), "block", block,"all_Parsons_blocks", all_Parsons_blocks,"current_indent_in_block_stack", current_indent_in_block_stack, "this_indent", this_indent, "distractor_indent", distractor_indent, "current_block_stack", block_stack)

        # store the current block into the block stack
        if this_indent == current_indent_in_block_stack:
            block_stack.append((index, block[3]))
        elif (distractor_indent == False) & (this_indent != current_indent_in_block_stack):
            # use the first line number of the block as the line sequence number
            all_Parsons_blocks[block_stack[0][0]] = ''.join(str(block[1]) for block in block_stack)
            #print("all_Parsons_blocks", all_Parsons_blocks)
            block_stack = [(index, block[3])]
            current_indent_in_block_stack = this_indent
        # distractor_indent != "" means that detected that this is an end of a distractor block stack  or a start of a distractor block stack -- how to distinguish?
        # this_indent != current_indent_in_block_stack means that we have finished building a block stack
        # so we have stored all the related lines in this distractor block stack
        # now we need to do some special processing for the distractor block stack
        elif (distractor_indent != False) & (this_indent != current_indent_in_block_stack):
            # if this, then we have finished building a distractor block stack
            count_fixed= sum(1 for block in block_stack if "#matched-fixed" in block[1])
            print("count_fixed", count_fixed, "block_stack", block_stack)
            if (count_fixed == 0):
                #then this is just a start of a distractor block stack, moved what we have stored in the block stack to the all_Parsons_blocks first
                all_Parsons_blocks[block_stack[0][0]] = block_stack
            # then continue
            fixed_line_block, distractor_block = extract_distractor_Parsons_block(block_stack)
            all_Parsons_blocks[block_stack[0][0]+0.20] = fixed_line_block
            all_Parsons_blocks[block_stack[0][0]+0.22] = distractor_block
            # prepare for the next loop
            distractor_indent = False
            block_stack = [(index, block[3])]
            current_indent_in_block_stack = this_indent
            # if it is the last item, then no loop anymore, just store the last block stack           

        if index == len(blocks)-1:
            if (distractor_indent == False):
                # use the first line number of the block as the line sequence number
                all_Parsons_blocks[block_stack[0][0]] = ''.join(str(block[1]) for block in block_stack)
            elif (distractor_indent != False):
                count_fixed= sum(1 for block in block_stack if "#matched-fixed" in block[1])
                print("count_fixed", count_fixed, "block_stack", block_stack)
                if (count_fixed == 0):
                    #then this is just a start of a distractor block stack, moved what we have stored in the block stack to the all_Parsons_blocks first
                    all_Parsons_blocks[block_stack[0][0]] = block_stack
                # then continue
                fixed_line_block, distractor_block = extract_distractor_Parsons_block(block_stack)
                all_Parsons_blocks[block_stack[0][0]+0.20] = fixed_line_block
                all_Parsons_blocks[block_stack[0][0]+0.22] = distractor_block

    print("all_Parsons_blocks", all_Parsons_blocks)

    all_Parsons_blocks = OrderedDict(sorted(all_Parsons_blocks.items()))
    all_Parsons_blocks = list(all_Parsons_blocks.values())
    all_Parsons_blocks = [item.replace(' #matched-fixed', '') if '#matched-fixed' in item  else item for item in all_Parsons_blocks]
    # removing all occurrences of "#settled" lines except for the last one
    all_Parsons_blocks = [keep_last_hash_tag_lines(item, "#settled") for item in all_Parsons_blocks]

    print("all_Parsons_blocks", all_Parsons_blocks)
    return all_Parsons_blocks

def aggregate_code_to_full_Parsons_block(blocks):
    current_indent = check_indentation_level(blocks[0])
    all_Parsons_blocks = []
    Parsons_block = ""
    distractor_indent = ""
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


def reduce_whitespace(text):
    lines = text.split('\n')  # Split the text into lines based on '\n'
    processed_lines = []
    if len(lines) == 1:
        indentation = text[:len(text) - len(text.lstrip())][:-1]
        rest_of_string = re.sub(r'\s+', ' ', text.lstrip())
        return f"{indentation} {rest_of_string}"
    else:
        for line in lines:
            if line != '':
                indentation = text[:len(line) - len(line.lstrip())][:-1]
                rest_of_string = re.sub(r'\s+', ' ', line.lstrip())
                processed_lines.append(f"{indentation} {rest_of_string}")
            # Join the processed lines back using '\n'
            print("processed_lines",processed_lines)
        # Determine the join character based on whether the line ends with '\n'
        join_char = '\n' if processed_lines[-1] != '' else ''

        # Join the processed lines back using '\n' or '' as the join character
        processed_text = join_char.join(processed_lines)
        return processed_text

def convert_code_to_block(blocks):
    print("blocks-before", blocks)
    for i, block in enumerate(blocks):
        block = reduce_whitespace(block)
        print("block-reduce-whitespace", block)
        block = re.sub(r'\n+', '\n', block)
        print("block-remove_multiple\n", block)
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

    print(blocks)
    # Save the blocks into a string
    blocks = ''.join(blocks)
    return blocks




