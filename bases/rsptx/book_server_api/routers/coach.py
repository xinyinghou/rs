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

# Third-party imports
# -------------------
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pyflakes import checker as pyflakes_checker
from .personalized_parsons.end_to_end import get_personalized_parsons_help
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
    req_bytes = await request.body()
    req = req_bytes.decode("utf-8")
    student_code = req.split("|||sep|||")[0]
    problem_name = req.split("|||sep|||")[1]
    df_question_bank = pd.read_csv("./Evaluation_Material_STUDY.csv").fillna('')
    print("start_to: get_personalized_parsons_help")
    def personalized_help(student_code, problem_name):
        input_dict = {
            "Problem Name":problem_name,
            "CF (Code)":student_code
        }
        return get_personalized_parsons_help(input_dict, df_question_bank)

    personalized_code_solution, personalized_Parsons_block = personalized_help(student_code, problem_name)

    parsons_html = """
        <pre  class="parsonsblocks" data-question_label="1"    data-noindent="true"  data-numbered="left"    style="visibility: hidden;">
        """ + personalized_Parsons_block + """
        </pre>
"""


    return personalized_code_solution + "||split||" + parsons_html 
