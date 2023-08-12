import ast

code = ""
def extract_variable_names(code):
    variable_names = set()

    def visit_node(node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variable_names.add(target.id)

        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                variable_names.add(node.target.id)

        for child_node in ast.iter_child_nodes(node):
            visit_node(child_node)

    try:
        tree = ast.parse(code)
        visit_node(tree)
    except SyntaxError as e:
        print(f"SyntaxError: {e}")

    return variable_names