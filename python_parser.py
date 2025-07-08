import ast

class SimplePythonParser(ast.NodeVisitor):
    def __init__(self):
        self.functions = []         # Store function definitions
        self.main_body = []         # Store statements inside main()
        self.uses_string = False    # Flag to include <string> if needed
        self.uses_vector = False
        self.uses_algorithm = False
        self.uses_cctype = False
    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            value_node = node.value
            print(f"DEBUG: Visiting assignment for variable {var_name}")
            value_type = self._infer_type(value_node)

            # ✅ Handle: List (vector)
            if isinstance(value_node, ast.List):
                elements = self._get_expr(value_node)
                self.uses_vector = True
                self.main_body.append(f"{value_type} {var_name} = {elements};")
                return

            # ✅ Handle: input()
            if isinstance(value_node, ast.Call):
                func_id = getattr(value_node.func, 'id', '')

                # case: name = input("Enter name")
                if func_id == 'input':
                    if value_type == 'string':
                        self.uses_string = True
                    if value_node.args and isinstance(value_node.args[0], ast.Constant):
                        prompt = value_node.args[0].value
                        self.main_body.append(f'cout << "{prompt}";')
                    self.main_body.append(f"{value_type} {var_name};")
                    self.main_body.append(f"cin >> {var_name};")
                    return

                # case: age = int(input("Enter age"))
                elif func_id in ['int', 'float'] and len(value_node.args) == 1:
                    inner_call = value_node.args[0]
                    if isinstance(inner_call, ast.Call) and getattr(inner_call.func, 'id', '') == 'input':
                        if inner_call.args and isinstance(inner_call.args[0], ast.Constant):
                            prompt = inner_call.args[0].value
                            self.main_body.append(f'cout << "{prompt}";')
                        self.main_body.append(f"{value_type} {var_name};")
                        self.main_body.append(f"cin >> {var_name};")  # ✅ FIX: direct input as int
                        return


            # ✅ Default assignment
            expr = self._get_expr(value_node)
            if value_type == "string":
                self.uses_string = True
            elif "vector" in value_type:
                self.uses_vector = True

            self.main_body.append(f"{value_type} {var_name} = {expr};")



    def visit_Expr(self, node):
        value = node.value

        # Case: print(...)
        if isinstance(value, ast.Call) and getattr(value.func, 'id', '') == 'print':
            args = value.args
            cpp_print = ' << '.join([self._get_expr(arg) for arg in args])
            self.main_body.append(f'cout << {cpp_print} << endl;')
            return

        # Case: append() ➝ push_back()
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            obj = self._get_expr(value.func.value)
            method = value.func.attr

            if method == "append":
                arg = self._get_expr(value.args[0])
                self.main_body.append(f"{obj}.push_back({arg});")
                return

            # Add more method handlers if needed

        # Case: len() ➝ x.size()
        if isinstance(value, ast.Call) and getattr(value.func, 'id', '') == 'len':
            arg = self._get_expr(value.args[0])
            self.main_body.append(f"cout << {arg}.size() << endl;")
            return

        # Default: treat as expression
        expr = self._get_expr(value)
        self.main_body.append(f"{expr};")

    def visit_If(self, node):
        test = self._get_condition(node.test)
        self.main_body.append(f"if ({test}) {{")
        self._visit_block(node.body)
        self.main_body.append("}")

        current_else = node.orelse
        while len(current_else) == 1 and isinstance(current_else[0], ast.If):
            elif_node = current_else[0]
            test = self._get_condition(elif_node.test)
            self.main_body.append(f"else if ({test}) {{")
            self._visit_block(elif_node.body)
            self.main_body.append("}")
            current_else = elif_node.orelse

        if current_else:
            self.main_body.append("else {")
            self._visit_block(current_else)
            self.main_body.append("}")
    def visit_For(self, node):
        if isinstance(node.iter, ast.Call) and getattr(node.iter.func, 'id', '') == 'range':
            var = node.target.id
            args = node.iter.args

            start = "0"
            end = None
            step = "1"

            if len(args) == 1:
                end = self._get_expr(args[0])
            elif len(args) == 2:
                start = self._get_expr(args[0])
                end = self._get_expr(args[1])
            elif len(args) == 3:
                start = self._get_expr(args[0])
                end = self._get_expr(args[1])
                step = self._get_expr(args[2])

            # Determine condition based on step sign
            cmp_op = "<" if step.startswith("-") == False else ">"
            self.main_body.append(f"for (int {var} = {start}; {var} {cmp_op} {end}; {var} += {step}) {{")

            for stmt in node.body:
                self.visit(stmt)

            self.main_body.append("}")
        elif isinstance(node.iter, ast.Name):  # e.g., for num in numbers:
            iterable = self._get_expr(node.iter)
            var = node.target.id
            self.main_body.append(f"for (auto {var} : {iterable}) {{")
            for stmt in node.body:
                self.visit(stmt)
            self.main_body.append("}")
            return

        else:
            self.main_body.append("/* unsupported for-loop */")


    def visit_FunctionDef(self, node):
        func_name = node.name
        params = [arg.arg for arg in node.args.args]
        cpp_params = ", ".join([f"int {p}" for p in params])  # TODO: infer type per param

        # Prepare a new visitor for the function body
        func_visitor = SimplePythonParser()
        for stmt in node.body:
            func_visitor.visit(stmt)

        # Infer return type from return statement
        return_type = "void"
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                return_type = func_visitor._infer_type(stmt.value)
                break

        if func_name == "main":
            self.main_body.extend(func_visitor.main_body)
        else:
            func_lines = []
            func_lines.append(f"{return_type} {func_name}({cpp_params}) " + "{")
            func_lines.extend(["    " + line for line in func_visitor.main_body])
            func_lines.append("}")
            self.functions.extend(func_lines)



    def visit_Return(self, node):
        return_expr = self._get_expr(node.value)
        self.main_body.append(f"return {return_expr};")


    def _visit_block(self, statements):
        original_body = self.main_body
        temp_body = []
        self.main_body = temp_body

        for stmt in statements:
            self.visit(stmt)

        indented = ["    " + line for line in self.main_body]
        original_body.extend(indented)
        self.main_body = original_body

    def _get_condition(self, test):
        if isinstance(test, ast.Compare):
            left = self._get_expr(test.left)
            right = self._get_expr(test.comparators[0])
            op = self._get_operator(test.ops[0])
            return f"{left} {op} {right}"
        elif isinstance(test, ast.BoolOp):
            op = '&&' if isinstance(test.op, ast.And) else '||'
            values = [self._get_condition(v) for v in test.values]
            return f"({f' {op} '.join(values)})"
        elif isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            return f"!({self._get_condition(test.operand)})"
        return "/* unsupported condition */"


    def _get_expr(self, expr):
        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
            return f"-{self._get_expr(expr.operand)}"

        elif isinstance(expr, ast.Name):
            return expr.id

        elif isinstance(expr, ast.Constant):
            return f'"{expr.value}"' if isinstance(expr.value, str) else str(expr.value)

        elif isinstance(expr, ast.BinOp):
            left = self._get_expr(expr.left)
            right = self._get_expr(expr.right)
            op = self._get_operator(expr.op)
            return f"({left} {op} {right})"

        elif isinstance(expr, ast.List):
            elements = [self._get_expr(e) for e in expr.elts]
            return "{" + ", ".join(elements) + "}"

        elif isinstance(expr, ast.Subscript):  # e.g. nums[0]
            target = self._get_expr(expr.value)
            index = self._get_expr(expr.slice.value if hasattr(expr.slice, 'value') else expr.slice)
            return f"{target}[{index}]"

        elif isinstance(expr, ast.Call):
            # Handle method calls (like name.upper())
            if isinstance(expr.func, ast.Attribute):
                obj = self._get_expr(expr.func.value)
                method = expr.func.attr

                if method == 'append':
                    return f"{obj}.push_back({self._get_expr(expr.args[0])})"
                elif method == 'upper':
                    self.uses_algorithm = True
                    self.uses_cctype = True
                    return f"(transform({obj}.begin(), {obj}.end(), {obj}.begin(), ::toupper), {obj})"
                elif method == 'lower':
                    self.uses_algorithm = True
                    self.uses_cctype = True
                    return f"(transform({obj}.begin(), {obj}.end(), {obj}.begin(), ::tolower), {obj})"
                else:
                    return f"/* unsupported string method {method} */"

            # Handle len(x) ➝ x.size()
            elif isinstance(expr.func, ast.Name) and expr.func.id == "len":
                if len(expr.args) == 1:
                    return f"{self._get_expr(expr.args[0])}.size()"

            # Regular function call (like int(a), print(a))
            func = self._get_expr(expr.func)
            args = ", ".join([self._get_expr(arg) for arg in expr.args])
            return f"{func}({args})"

        return "/* unsupported expr */"


    def _get_operator(self, op):
        if isinstance(op, ast.Add): return "+"
        if isinstance(op, ast.Sub): return "-"
        if isinstance(op, ast.Mult): return "*"
        if isinstance(op, ast.Div): return "/"
        if isinstance(op, ast.Gt): return ">"
        if isinstance(op, ast.Lt): return "<"
        if isinstance(op, ast.Eq): return "=="
        if isinstance(op, ast.NotEq): return "!="
        if isinstance(op, ast.GtE): return ">="
        if isinstance(op, ast.LtE): return "<="
        return "/* op */"

    def _infer_type(self, value_node):
        # List handling with element type inference
        if isinstance(value_node, ast.List):
            if value_node.elts:
                first_elt = value_node.elts[0]
                if isinstance(first_elt, ast.Constant):
                    if isinstance(first_elt.value, int):
                        self.uses_vector = True
                        return "vector<int>"
                    elif isinstance(first_elt.value, float):
                        self.uses_vector = True
                        return "vector<float>"
                    elif isinstance(first_elt.value, str):
                        self.uses_vector = True
                        self.uses_string = True
                        return "vector<string>"
            # Default fallback if empty or unknown types
            self.uses_vector = True
            return "vector<auto>"

        # Constant handling
        if isinstance(value_node, ast.Constant):
            if isinstance(value_node.value, int):
                return "int"
            elif isinstance(value_node.value, float):
                return "float"
            elif isinstance(value_node.value, str):
                self.uses_string = True
                return "string"

        # input(), int(input()), float(input()) handling
        elif isinstance(value_node, ast.Call):
            func_id = getattr(value_node.func, 'id', '')
            if func_id == 'input':
                self.uses_string = True
                return "string"
            elif func_id == 'int':
                return "int"
            elif func_id == 'float':
                return "float"

        return "auto"


def parse_python_code(filepath):
    with open(filepath, 'r') as file:
        code = file.read()

    tree = ast.parse(code)
    parser = SimplePythonParser()
    parser.visit(tree)

    cpp_output = []
    cpp_output.append("#include <iostream>")
    if parser.uses_string:
        cpp_output.append("#include <string>")
        cpp_output.append("using namespace std;\n")
    else:
        cpp_output.append("using namespace std;\n")
    if parser.uses_vector:
        cpp_output.insert(1, "#include <vector>")
    if parser.uses_algorithm:
        cpp_output.insert(1, "#include <algorithm>")
    if parser.uses_cctype:
        cpp_output.insert(1, "#include <cctype>")

    cpp_output.extend(parser.functions)
    cpp_output.append("int main() {")
    cpp_output.extend(["    " + line for line in parser.main_body])
    cpp_output.append("    return 0;")
    cpp_output.append("}")

    with open("code_samples/output.cpp", "w") as f:
        f.write("\n".join(cpp_output))

    return cpp_output
def parse_python_code_from_string(code_str):
    tree = ast.parse(code_str)
    parser = SimplePythonParser()
    parser.visit(tree)

    cpp_output = []
    cpp_output.append("#include <iostream>")
    if parser.uses_string:
        cpp_output.append("#include <string>")
    if parser.uses_vector:
        cpp_output.append("#include <vector>")
    if parser.uses_algorithm:
        cpp_output.append("#include <algorithm>")
    if parser.uses_cctype:
        cpp_output.append("#include <cctype>")
    cpp_output.append("using namespace std;\n")

    cpp_output.extend(parser.functions)
    cpp_output.append("int main() {")
    cpp_output.extend(["    " + line for line in parser.main_body])
    cpp_output.append("    return 0;")
    cpp_output.append("}")

    return "\n".join(cpp_output)
