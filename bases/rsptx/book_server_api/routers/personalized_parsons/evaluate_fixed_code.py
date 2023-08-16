import unittest
import pandas as pd
import re
import difflib
from fuzzywuzzy import fuzz
from types import ModuleType
import difflib
import signal

class NullOutput:
    def write(self, _):
        pass

class TimeoutError(Exception):
    pass

def handler(signum, frame):
    raise TimeoutError("Test execution exceeded time limit")

def load_and_run_tests(unittest_case, code_to_test, time_limit=5):

    # Set up a signal handler for timeout
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(time_limit)

    try:
        # Create a dummy module to hold the test cases
        test_module = ModuleType("test_module")
        test_module.unittest = unittest

        print("test_module", test_module)
        # Execute the test cases string within the dummy module's namespace
        exec(unittest_case, test_module.__dict__)
        # Execute the code to test within the desired scope
        exec(code_to_test, test_module.__dict__)
        # Retrieve the loaded test cases
        test_suite = unittest.TestLoader().loadTestsFromModule(test_module)
        # Run the test suite
        test_results = unittest.TextTestRunner(verbosity=0, failfast=True, stream=NullOutput()).run(test_suite)
    except TimeoutError:
        return False
    finally:
        signal.alarm(0)

    print("test_results", test_results)
    return test_results


def fix_indentation(text):
    lines = text.split('\n')

    # Remove leading whitespace for the first line
    if lines:
        lines[0] = lines[0].lstrip()
    
    # Find the indentation of the first def/class line
    indentation = 0
    for line in lines:
        if line.strip().startswith(('def ', 'class ')):
            indentation = len(line) - len(line.lstrip())
            break
    
    # Remove indentation for subsequent lines
    for i in range(1, len(lines)):
        lines[i] = lines[i][indentation:]
    
    return '\n'.join(lines)

def contain_default_starting_code(default_code, code, similarity_threshold=0.90):
    if pd.isna(default_code)== True:
        return True
    else:
        # Remove leading whitespace from each line in the subset and code
        default_code = '\n'.join(line.lstrip() for line in default_code.split('\n') if line.strip())
        code_stripped = '\n'.join(line.lstrip() for line in code.split('\n') if line.strip())
        # Remove whitespace within strings
        default_code_no_whitespace = re.sub(r'(?<=\S)\s+(?=\S)', '', default_code)
        code_stripped_no_whitespace = re.sub(r'(?<=\S)\s+(?=\S)', '', code_stripped)

        if default_code_no_whitespace in code_stripped_no_whitespace:
            return True
        else:
            default_lines = [line.lstrip() for line in default_code.split('\n') if line.strip()]
            code_lines = [line.lstrip() for line in code.split('\n') if line.strip()]
            code_before_last_default_code_line = code_lines[: code_lines.index(default_lines[-1])]
            # Calculate similarity ratio using difflib
            similarity_ratio = difflib.SequenceMatcher(None, default_lines, code_before_last_default_code_line).ratio()
            return similarity_ratio >= similarity_threshold

def extract_code_line(code):
    ##print("code\n", code)
    fixed_pattern = r'\[fixed-code\]:\s*([\s\S]*)'

    if re.findall(fixed_pattern, code, re.DOTALL):
        fixed_code =  re.findall(fixed_pattern, code, re.DOTALL)[0].strip()
        # if the content inside of [fixed-code] does not start with def
    else:
        fixed_code = code

    fenced_pattern = r'```(.*?)```'

    if re.findall(fenced_pattern, fixed_code, flags=re.DOTALL):
        extracted_content = re.findall(fenced_pattern, fixed_code, flags=re.DOTALL)
        fixed_code =  '\n'.join(extracted_content)
    else:
        fixed_code = fixed_code

    if not fixed_code.startswith(('def', 'import', 'class')):
        if re.findall(r'(?:def|class|import)(.*)', fixed_code, re.DOTALL):
            match = re.search(r"(class|import|def)", fixed_code)
            if match:
                fixed_code = fixed_code[match.start():]
        else:
            fixed_code = fixed_code
    else:
        fixed_code = fixed_code

    return fixed_code
    

def remove_potential_default_lines(default_code, code):
    lines = code.split('\n')

    
    if pd.isna(default_code)== True:
        return  '\n'.join(filtered_lines)
    else:
        default_lines = default_code.split('\n')
        filtered_lines = []
        in_function = False
        for line in lines:
            similarity_scores = [fuzz.ratio(line, default_line) for default_line in default_lines]
            max_similarity = max(similarity_scores) if similarity_scores else 0
            if max_similarity > 80:
                if in_function:
                    if line.strip().startswith('def ') and line.strip().endswith(':'):
                        in_function = False
                else:
                    if any(line.strip() in default_line for default_line in default_lines):
                        in_function = True
                        continue
                    else:
                        filtered_lines.append(line)
            else:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

def remove_default_testline(code, default_test_code):
    # Split the lines to remove by newline
    default_test_code_list = default_test_code.strip().split('\n')
    # remove the leading whitespace in front of each item in default_test_code_list
    default_test_code_list = [line.lstrip() for line in default_test_code_list]
    # Remove the lines from the code snippet
    modified_code_snippet = ''
    for line in code.strip().split('\n'):
        if (line.strip() not in default_test_code_list) & ('print' not in line) & (not line.startswith('#')):
            modified_code_snippet += line + '\n'
    ##print("modified_code_snippet\n", modified_code_snippet)
    return modified_code_snippet

def remove_empty_lines(code):
    lines = code.splitlines()
    non_empty_lines = [line for line in lines if line.strip() != ""]
    return "\n".join(non_empty_lines)

def remove_explanation_lines(code):
    # Split each line and take the part before the "#" symbol
    cleaned_lines = [line.split('#', 1)[0] for line in code.split('\n')]

    # Join the modified lines back to form the cleaned code
    cleaned_code = '\n'.join(cleaned_lines)
    return cleaned_code

def unittest_evaluation(fixed_code, starting_code, default_test_code, unittest_case):
    try:
        fixed_code.split('\n')
        fixed_code = extract_code_line(fixed_code)
        fixed_code = remove_default_testline(fixed_code, default_test_code)
        fixed_code = remove_empty_lines(fixed_code)
        fixed_code = remove_explanation_lines(fixed_code)
        #print("cleaned_fixed_code\n", fixed_code)
    except Exception as e:
        return f"No enough code-{e}", fixed_code
    
    try:
        ##print("fixed_code_first attempt", fixed_code)
        results = load_and_run_tests(unittest_case, fixed_code)
        #print("results.wasSuccessful()\n", results.wasSuccessful())
        if contain_default_starting_code(starting_code, fixed_code):
            #print("results.wasSuccessful()\n", results.wasSuccessful())
            return results.wasSuccessful(), fixed_code
        else:
            return "No starting code", fixed_code
    except Exception as e:
        #print(e)
        fixed_code = remove_potential_default_lines(default_test_code, fixed_code)
        try:
            results = load_and_run_tests(unittest_case, fixed_code)
            if contain_default_starting_code(starting_code, fixed_code):
                ##print("results.wasSuccessful()\n", results.wasSuccessful())
                return results.wasSuccessful(), fixed_code
            else:
                return "No starting code", fixed_code
        except:
            try:
                fixed_code = fix_indentation(fixed_code)
                results = load_and_run_tests(unittest_case, fixed_code)
                if contain_default_starting_code(starting_code, fixed_code):
                    #print("results.wasSuccessful()\n", results.wasSuccessful())
                    return results.wasSuccessful(), fixed_code
                else:
                    return "No starting code", fixed_code
            except Exception as e:
                return f"We got errors, {e}", fixed_code

def code_distractor_unittest_evaluation(code_with_distrator, starting_code, default_test_code, unittest_case):
    # try:
    #     code_with_distrator.split('\n')
    # except Exception as e:
    #     return "No enough code", code_with_distrator
    print("distractor_unittest_evaluation")
    try:
        print("unittest_case", unittest_case, "code_with_distrator", code_with_distrator)
        results = load_and_run_tests(unittest_case, code_with_distrator)
        print("distractor_results.wasSuccessful()\n", results.wasSuccessful())
        if contain_default_starting_code(starting_code, code_with_distrator):
            return results.wasSuccessful(), code_with_distrator
        else:
            return "No starting code", code_with_distrator
    except:
        print("remove_potential_default_lines")
        code_with_distrator = remove_potential_default_lines(default_test_code, code_with_distrator)
        try:
            results = load_and_run_tests(unittest_case, code_with_distrator)
            if contain_default_starting_code(starting_code, code_with_distrator):
                return results.wasSuccessful(), code_with_distrator
            else:
                return "No starting code", code_with_distrator
        except:
            try:
                print("fix_indentation")
                code_with_distrator = fix_indentation(code_with_distrator)
                results = load_and_run_tests(unittest_case, code_with_distrator)
                print("distractor_results.wasSuccessful()\n", results.wasSuccessful())
                if contain_default_starting_code(starting_code, code_with_distrator):
                    return results.wasSuccessful(), code_with_distrator
                else:
                    return "No starting code", code_with_distrator
            except Exception as e:
                return False, code_with_distrator

def clean_student_code(student_code, default_test_code):
    try:
        student_code.split('\n')
        cleaned_student_code = remove_default_testline(student_code, default_test_code)
        cleaned_student_code = remove_empty_lines(cleaned_student_code)
        cleaned_student_code = remove_explanation_lines(cleaned_student_code)
    except:
        cleaned_student_code = student_code

    return cleaned_student_code

# code_with_distrator = """
#   class Cat:

#      def __init__(self, name, age):

#          self.name == name
#          self.age = age

#      def __str__(self):

#          return "name: " + self.name + ", age: " + str(self.age)

#      def make_sound(self):

#          return "Meow"
# """
#code_distractor_unittest_evaluation(code_with_distrator, default_start_code, default_test_code, unittest_code)

