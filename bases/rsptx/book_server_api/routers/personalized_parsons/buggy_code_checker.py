# buggy_code_checker.py

# 0%: Check if the file only contains the default code
def buggy_code_checker(buggy_code, default_start_code, default_test_code):
    if buggy_code.strip() == default_start_code.strip() or \
        buggy_code.strip() == default_test_code.strip() or \
        buggy_code.strip() == default_start_code.strip() + default_test_code.strip() or \
        buggy_code.strip() == default_start_code.strip() + default_test_code.strip() or\
        len(buggy_code.strip()) == 0:
        # get to the most common solution
        return False
    else:
        # get to the openai personalization part
        return True

