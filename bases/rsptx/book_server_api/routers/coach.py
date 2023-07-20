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
import json

# Third-party imports
# -------------------
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pyflakes import checker as pyflakes_checker

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
    code_bytes = await request.body()
    code = code_bytes.decode("utf-8")
    lines = code.split('\n')
    data_order = " ".join(str(x) for x in range(len(lines)))
    
    # html = '\n        <pre  class="parsonsblocks" data-question_label="1"   data-adaptive="true"  data-order="' + data_order + '"      style="visibility: hidden;">\n        '
    # html = html + "\n---\n   ".join(lines) + "\n        </pre>"

    html = """
        <pre  class="parsonsblocks" data-question_label="1"   data-adaptive="true"   data-order="0 1 2 3 4"      style="visibility: hidden;">
        def fib(num):
---
   if num == 0:
       return 0:
---
   if num == 1:
       return 1:
---
   return fib(num - 1) + fib(num - 2)
---
   return fib(num - 1) * fib(num - 2) #paired
        </pre>
"""

    return html
