# ***********************************
# |docname| - Provide code advice
# ***********************************
# Endpoints to provide various kinds of advice (syntax/style/etc...)
# about code samples
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import ast
# import json
import pandas as pd
import re
import os

# Third-party imports
# -------------------
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pyflakes import checker as pyflakes_checker
from .personalized_parsons.end_to_end import get_parsons_help
# from .personalized_parsons.test import test_import_personalized

# Local application imports
# -------------------------

# .. _APIRouter config:
#
# Routing
# =======
# Setup the router object for the endpoints defined in this file.  These will
# be `connected <included routing>` to the main application in `../main.py`.
router = APIRouter(
    # shortcut so we don't have to repeat this part
    prefix="/coach",
    tags=["coach"],
)


@router.post("/python_check")
async def python_check(request: Request):
    """
    Takes a chunk of Python code and runs a syntax checker (currently
    Pyflakes) on it to provide more detailed advice than is available
    via Skulpt.
    """
    code_bytes = await request.body()
    code = code_bytes.decode("utf-8")

    filename = "program.py"

    resultMessage = ""
    try:
        tree = ast.parse(code, filename=filename)
        w = pyflakes_checker.Checker(tree, filename=filename)
        w.messages.sort(key=lambda m: m.lineno)
        for m in w.messages:
            resultMessage = resultMessage + str(m) + "\n"
    except SyntaxError as e:
        resultMessage = f"{filename}:{str(e.lineno)}:{str(e.offset)}: {e.args[0]}\n"

    return resultMessage

@router.post("/parsons_scaffolding")
async def parsons_scaffolding(request: Request):
    """
    Takes in student code, generate a personalized Parsons problems with openAI,
    then converts the generated problem to .rst, and returns the .rst string.
    """
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Adjust path to navigate directly to personalized_parsons from routers
    csv_dir = os.path.join(script_dir, "personalized_parsons")

    # Build the full path to the CSV file
    csv_path = os.path.join(csv_dir, "Classroom_Evaluation_Material.csv")

    df_question_bank = pd.read_csv(csv_path).fillna('')

    req_bytes = await request.body()
    req = req_bytes.decode("utf-8")
    student_code = req.split("|||sep|||")[0]
    problem_name = req.split("|||sep|||")[1]
    # df_question_bank = pd.read_csv("./Classroom_Evaluation_Material.csv").fillna('')
    print("start_to: get_parsons_help")
    def parsons_help(student_code, problem_name, personalization):
        input_dict = {
            "Problem Name":problem_name,
            "CF (Code)":student_code
        }
        return get_parsons_help(input_dict, df_question_bank, personalization)

    personalized_code_solution, personalized_Parsons_block = parsons_help(student_code, problem_name, personalization=True)

    common_code_solution, common_Parsons_block = parsons_help(student_code, problem_name, personalization=False)
    
    common_Parsons_block = re.sub(r'<(?=\S)', '< ', common_Parsons_block)
    personalized_Parsons_block = re.sub(r'<(?=\S)', '< ', personalized_Parsons_block)
    adaptive_text = ' data-adaptive="true" '

    personalized_parsons_html = """
        <pre  class="parsonsblocks" data-question_label="1"   data-numbered="left"  %s  style="visibility: hidden;">
        """ % adaptive_text + personalized_Parsons_block + """
        </pre>
"""
    common_parsons_html = """
        <pre  class="parsonsblocks" data-question_label="1"   data-numbered="left"  %s  style="visibility: hidden;">
        """ % adaptive_text + common_Parsons_block + """
        </pre>
"""

    return personalized_code_solution + "||split||" + personalized_parsons_html  + "||split||" + common_code_solution + "||split||" + common_parsons_html
