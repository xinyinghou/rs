import os
from openai import AzureOpenAI
import re
from dotenv import load_dotenv
from dotenv import dotenv_values
import time
import sqlite3
import random
from .store_solution_cache import *
from datetime import datetime
import sys
#from evaluate_fixed_code_evaluation import *
from .evaluate_fixed_code import *

#Sets the current working directory to be the same as the file.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# request rate limit:
request_rate_limit = 30
#Load environment file for secrets.
try:
    if load_dotenv('.env') is False:
        raise TypeError
except TypeError:
    print('Unable to load .env file.')
    quit() 

# Global variables
api_key_list_str = dotenv_values(".env")['LST_OPENAI_API_KEY']
api_key_list = api_key_list_str.split(',')
api_key_list = [api_key.strip() for api_key in api_key_list]

print("api_key_list", api_key_list)


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


# def initialize_database(api_keys, db_path="request_counts.csv"):
#     # Create CSV file and write header if it doesn't exist
#     if not os.path.isfile(db_path):
#         with open(db_path, 'w', newline='') as csvfile:
#             fieldnames = ['api_key', 'remaining_requests', 'total_count', 'last_update']
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#             writer.writeheader()

#         # Write data to CSV
#         with open(db_path, 'a', newline='') as csvfile:
#             fieldnames = ['api_key', 'remaining_requests', 'total_count', 'last_update']
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#             for key in api_keys:
#                 writer.writerow({
#                     'api_key': key,
#                     'remaining_requests': request_rate_limit,
#                     'total_count': 0,
#                     'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                 })

#         print("CSV file created/updated.")

# def get_current_key(db_path="request_counts.csv"):
#     initialize_database(api_key_list, db_path)
#     with open(db_path, 'r') as csvfile:
#         reader = csv.DictReader(csvfile)

#         # Sort CSV data by last_update in descending order and get the first row
#         sorted_data = sorted(reader, key=lambda x: x['last_update'], reverse=True)
#         if sorted_data:
#             return sorted_data[0]['api_key']
#         else:
#             return None


# def switch_api_key(api_keys):
    # initialize_database(api_key_list, db_path)
    # current_key = get_current_key(db_path)

    # Reset request counts at the beginning of each minute - can be done using OpenAI's rate limit headers
    # with open(db_path, 'r') as csvfile:
    #     fieldnames = ['api_key', 'remaining_requests', 'total_count', 'last_update']
    #     reader = csv.DictReader(csvfile, fieldnames=fieldnames)
    #     rows = list(reader)

    # current_time = datetime.now()

    # for row in rows:
    #     last_update_time = datetime.strptime(row['last_update'], '%Y-%m-%d %H:%M:%S')
    #     time_difference = (current_time - last_update_time).total_seconds()

    #     if time_difference > 60:
    #         row['remaining_requests'] = request_rate_limit
    #         row['last_update'] = current_time.strftime('%Y-%m-%d %H:%M:%S')

    # # Write the updated data back to the CSV file
    # with open(db_path, 'w', newline='') as csvfile:
    #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #     writer.writeheader()
    #     writer.writerows(rows)

    # print("Request counts reset for the beginning of each minute.")

        # # Check the request count for the current key
        # cursor.execute('''
        #     SELECT remaining_requests, total_count FROM api_key_counts WHERE api_key = ?
        # ''', (current_key,))
        # result = cursor.fetchone()

        # if result:
        #     current_remaining_requests, total_count = result
        #     if current_remaining_requests > 0:
        #         # Current key's request count is still less than 30, keep using it
        #         return current_key, current_remaining_requests, total_count

        # Current key's request count has reached the limit, switch to the key with the least count
        # cursor.execute('''
        #     SELECT api_key, remaining_requests, total_count
        #     FROM api_key_counts
        #     WHERE remaining_requests < ?
        #     ORDER BY remaining_requests DESC
        #     LIMIT 1
        # ''', (40,))
        # result = cursor.fetchone()
        # if result:
        # Filter keys with remaining requests > 0
    # filtered_keys = [row for row in rows if int(row['remaining_requests']) > 0]

    # # Sort filtered keys by remaining_requests in descending order and total_count in ascending order
    # sorted_keys = sorted(filtered_keys, key=lambda x: (int(x['remaining_requests']), int(x['total_count'])))

    # if sorted_keys:
    #     result = sorted_keys[0]
    #     api_key = result['api_key']
    #     remaining_requests = int(result['remaining_requests'])
    #     total_count = int(result['total_count'])
    #     return api_key, remaining_requests, total_count
    # else:
    #     print("No API key available. Please try again later.")
    #     return None, None, None
        
def get_actual_fixed_code(prompt_messages, current_api_key, attempt_type, situation, old_fixed_code):
    if attempt_type == "new":
        prompt_messages = prompt_messages
    elif attempt_type == "repeat":
        attachment = f"""
        This [old-fixed-code] is not {situation} to the [user-code]. Again, please try to generate a [fixed-code] that is {situation} to the [user-code]. You can use [sample-solution] as a reference when generating the [fixed-code].
        [old-fixed-code]: '{old_fixed_code}'
        [end-old-fixed-code]
        """
        prompt_messages[0]["content"] = prompt_messages[0]["content"] + attachment

    # client = OpenAI(
    #     api_key = current_api_key
    # )
    client = AzureOpenAI(
        api_key=current_api_key,  
        api_version=os.environ['API_VERSION'],
        azure_endpoint = os.environ['openai_api_base'],
        organization = os.environ['OPENAI_organization']
    )
    raw_completion_response = client.chat.completions.with_raw_response.create(
        model = os.environ['model'],
        temperature=0,  # Adjust this value to control randomness
        messages = prompt_messages,
        stop = ["[end-fixed-code]"],
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        seed=1234,
    )
    response_headers = raw_completion_response.headers
    completion = raw_completion_response.parse()
    #print("response_headers", response_headers, "completion", completion)
    # x-ratelimit-remaining-requests, x-ratelimit-reset-requests
    #remaining_requests = response_headers['x-ratelimit-remaining-requests']
    remaining_requests = 30 - (40-int(response_headers['x-ratelimit-remaining-requests']))
    fixed_code = completion.choices[0].message.content
    print("remaining_requests", remaining_requests, "fixed_code", fixed_code)
    #reset_requests = response_headers['x-ratelimit-reset-requests']
    
    return fixed_code, remaining_requests

# def get_min_reset_time(db_path):
#     # Query the database to retrieve reset times for all keys
#     # try:
#     #     with sqlite3.connect(db_path) as conn:
#     #             cursor = conn.cursor()
#     #             cursor.execute('SELECT MIN(reset_requests) FROM api_key_counts')
#     #             min_reset_time = cursor.fetchone()[0]
#     # except:
#     min_reset_time = None

#     if min_reset_time:
#         min_reset_time = datetime.strptime(min_reset_time, '%Y-%m-%d %H:%M:%S')
#         return min_reset_time
#     else:
#         # If no reset time found, return a default value
#         return datetime.now()
    

def get_fixed_code(df_question_line, buggy_code, default_test_code, attempt_type, situation, old_fixed_code, api_keys=api_key_list):
    # first check if the buggy code is in the cache
    cleaned_buggy_code = clean_student_code(buggy_code, default_test_code)
    print("get_fixed_code-cleaned_buggy_code", cleaned_buggy_code)
    if get_solution_from_cache(cleaned_buggy_code) != None:
        print("Solution found in cache.",get_solution_from_cache(cleaned_buggy_code))
        return get_solution_from_cache(cleaned_buggy_code)

    prompt_messages = build_code_prompt(df_question_line, buggy_code)
    
    #initialize_database(api_keys, db_path)
    #new_key, remaining_requests, total_count = switch_api_key(api_keys, db_path)

    while True:
        try:
            new_key = random.choice(api_keys)
            print(f"Switched to API Key: {new_key}")
            #Make the API request using the current_api_key
            fixed_code_response, remaining_requests = get_actual_fixed_code(prompt_messages, new_key, attempt_type, situation, old_fixed_code)
            print(f"Making API request with Key: {new_key}-Request Count: {remaining_requests}")
            return fixed_code_response
        except Exception as e:
            print(e)
            print("Retrying...")
            time.sleep(0.1)
    # if new_key is not None:
    #     print(f"Switched to API Key: {new_key}")
    #     # Make the API request using the current_api_key
    #     fixed_code_response, remaining_requests = get_actual_fixed_code(prompt_messages, new_key, attempt_type, situation, old_fixed_code)
    #     # Find the row corresponding to the API key
    #     with open(db_path, 'r') as csvfile:
    #         fieldnames = ['api_key', 'remaining_requests', 'total_count', 'last_update']
    #         reader = csv.DictReader(csvfile, fieldnames=fieldnames)
    #         rows = list(reader)

    #     for row in rows:
    #         if row['api_key'] == new_key:
    #             # Update the fields
    #             row['remaining_requests'] = remaining_requests
    #             row['total_count'] = str(int(row['total_count']) + 1)
    #             row['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    #     # Write the updated data back to the CSV file
    #     with open(db_path, 'w', newline='') as csvfile:
    #         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #         writer.writeheader()
    #         writer.writerows(rows)

    #     print(f"Making API request with Key: {new_key}-Request Count: {remaining_requests}")
    # else:
    #     print("No API key available.")
    #     # Sleep until the minimum reset time of all keys
    #     # Calculate the time until the next reset
    #     current_time = datetime.now()
    #     min_reset_time = get_min_reset_time()
    #     time_until_reset = max(2, (min_reset_time - current_time).total_seconds())
    #     print(f"Sleeping for {time_until_reset} seconds.")
    #     time.sleep(time_until_reset)
    #     # Retry the API request after the sleep
    #     get_fixed_code(df_question_line, buggy_code, attempt_type, situation, old_fixed_code, api_keys=api_key_list, db_path="request_counts.csv")
        
    #return fixed_code_response



