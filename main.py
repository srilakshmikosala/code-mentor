import ast
import io
import difflib
import subprocess
import sys
import tempfile
import os
from contextlib import redirect_stdout


# =========================================================
# SYNTAX CHECK
# =========================================================

def check_syntax(code):

    print("\n========== SYNTAX CHECK ==========")

    try:
        ast.parse(code)

        print("✓ No syntax errors found.")
        print("Your Python code is syntactically correct.")

    except SyntaxError as error:

        print("✗ Syntax error found!")
        print("Line:", error.lineno)
        print("Column:", error.offset)
        print("Error:", error.msg)

        if "was never closed" in error.msg:
            print("Explanation: You may have forgotten to close a bracket.")

        elif "expected ':'" in error.msg:
            print("Explanation: A colon ':' may be missing.")

        elif "unterminated string" in error.msg:
            print("Explanation: A string may not have been closed with a quote.")

        elif "invalid syntax" in error.msg:
            print("Explanation: Check the syntax near the mentioned line.")

        else:
            print("Explanation: Check the mentioned line carefully.")


# =========================================================
# RUNTIME ERROR CHECK
# =========================================================

def check_runtime_errors(code):

    print("\n========== RUNTIME ERROR CHECK ==========")

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return

    defined = set()
    used = set()
    variables = {}

    for node in ast.walk(tree):

        if isinstance(node, ast.Assign):

            if isinstance(node.value, ast.Constant):

                for target in node.targets:

                    if isinstance(target, ast.Name):
                        variables[target.id] = node.value.value

        if isinstance(node, ast.Name):

            if isinstance(node.ctx, ast.Store):
                defined.add(node.id)

            elif isinstance(node.ctx, ast.Load):
                used.add(node.id)

    # ---------- Division by Zero ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):

            if isinstance(node.right, ast.Constant):

                if node.right.value == 0:

                    print("\n⚠ Possible runtime error:")
                    print("ZeroDivisionError: division by zero")

            elif isinstance(node.right, ast.Name):

                variable_name = node.right.id

                if variables.get(variable_name) == 0:

                    print("\n⚠ Possible runtime error:")
                    print("ZeroDivisionError: division by zero")

    # ---------- Simple Type Errors ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.BinOp):

            left_type = None
            right_type = None

            if isinstance(node.left, ast.Constant):
                left_type = type(node.left.value)

            elif isinstance(node.left, ast.Name):

                if node.left.id in variables:
                    left_type = type(variables[node.left.id])

            if isinstance(node.right, ast.Constant):
                right_type = type(node.right.value)

            elif isinstance(node.right, ast.Name):

                if node.right.id in variables:
                    right_type = type(variables[node.right.id])

            if left_type == int and right_type == str:

                print("\n⚠ Possible runtime error:")
                print("TypeError: unsupported operation between int and str")

            elif left_type == str and right_type == int:

                print("\n⚠ Possible runtime error:")
                print("TypeError: unsupported operation between str and int")

    # ---------- Undefined Names ----------

    builtins = {
        "print",
        "input",
        "len",
        "range",
        "int",
        "float",
        "str",
        "list",
        "dict",
        "set",
        "tuple",
        "sum",
        "min",
        "max",
        "abs",
        "round",
        "enumerate",
        "zip",
        "sorted"
    }

    undefined = used - defined - builtins

    if undefined:

        print("\n⚠ Possible runtime error:")

        for name in sorted(undefined):

            print(f"NameError: '{name}' is not defined")

            print(
                f"Suggestion: Check whether '{name}' "
                f"is spelled correctly."
            )

            print(
                f"Suggestion: Make sure '{name}' "
                f"is defined before using it."
            )


# =========================================================
# CODE EXPLANATION
# =========================================================

def explain_code(code):

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return

    print("\n========== CODE EXPLANATION ==========")

    for node in tree.body:

        if isinstance(node, ast.Assign):

            if isinstance(node.targets[0], ast.Name):

                variable = node.targets[0].id

                if isinstance(node.value, ast.Constant):

                    value = node.value.value

                    print(f"• {variable} = {value}")

                    print(
                        f"  Explanation: Stores {value} "
                        f"in the variable '{variable}'."
                    )

                elif isinstance(node.value, ast.BinOp):

                    print(f"• {variable}")

                    print(
                        f"  Explanation: Calculates a value "
                        f"and stores it in '{variable}'."
                    )

        elif isinstance(node, ast.Expr):

            if isinstance(node.value, ast.Call):

                if isinstance(node.value.func, ast.Name):

                    function = node.value.func.id

                    if function == "print":

                        print("• print()")

                        print(
                            "  Explanation: Displays output "
                            "on the screen."
                        )

                    elif function == "input":

                        print("• input()")

                        print(
                            "  Explanation: Takes input "
                            "from the user."
                        )

        elif isinstance(node, ast.If):

            print("• if statement")

            print(
                "  Explanation: Checks a condition and "
                "executes code when it is true."
            )

        elif isinstance(node, ast.For):

            print("• for loop")

            print(
                "  Explanation: Repeats a block of code "
                "for each item in a sequence."
            )

        elif isinstance(node, ast.While):

            print("• while loop")

            print(
                "  Explanation: Repeats a block of code "
                "while a condition is true."
            )

        elif isinstance(node, ast.FunctionDef):

            print(f"• Function: {node.name}()")

            print(
                "  Explanation: Defines a reusable "
                "block of code."
            )


# =========================================================
# CODE QUALITY
# =========================================================

def check_code_quality(code):

    print("\n========== CODE QUALITY ==========")

    try:
        tree = ast.parse(code)

    except SyntaxError:

        print("Fix syntax errors first to analyze code quality.")
        return

    lines = code.splitlines()

    variables = [
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
    ]

    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    ]

    loops = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.For, ast.While))
    ]

    conditions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
    ]

    # ---------- Variable Naming ----------

    short_names = [
        name
        for name in variables
        if len(name) == 1
        and name not in {"i", "j", "x", "y"}
    ]

    if short_names:

        print("⚠ Variable naming:")

        print(
            "Consider using more descriptive names:",
            ", ".join(sorted(set(short_names)))
        )

    else:

        print("✓ Variable naming looks reasonable.")

    # ---------- Long Lines ----------

    long_lines = [
        index + 1
        for index, line in enumerate(lines)
        if len(line) > 80
    ]

    if long_lines:

        print("⚠ Long lines detected:")
        print("Lines:", ", ".join(map(str, long_lines)))

    else:

        print("✓ Line lengths are reasonable.")

    # ---------- Magic Numbers ----------

    magic_numbers = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Constant):

            if isinstance(node.value, (int, float)):

                if node.value not in {0, 1}:

                    magic_numbers.append(node.value)

    if magic_numbers:

        print("⚠ Magic numbers detected:")

        print(
            "Consider storing important numeric values "
            "in named constants."
        )

    else:

        print("✓ No major magic-number issues found.")

    # ---------- Print Statements ----------

    print_count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    )

    if print_count > 5:

        print("⚠ Many print() statements detected.")

        print(
            "Consider organizing output or using functions."
        )

    else:

        print("✓ print() usage is reasonable.")

    # ---------- Function Length ----------

    for function in functions:

        if hasattr(function, "end_lineno"):

            length = (
                function.end_lineno
                - function.lineno
                + 1
            )

            if length > 30:

                print(
                    f"⚠ Function '{function.name}' "
                    f"is quite long ({length} lines)."
                )

    # ---------- Branches ----------

    branch_count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.If, ast.For, ast.While)
        )
    )

    if branch_count > 8:

        print(
            "⚠ Code has many branches or loops. "
            "Consider breaking it into smaller functions."
        )

    else:

        print("✓ Control flow complexity is manageable.")

    print("\n✓ Code quality analysis completed.")


# =========================================================
# SMART FIX
# =========================================================

def smart_fix(code):

    print("\n========== SMART FIX ==========")

    try:
        tree = ast.parse(code)

    except SyntaxError as error:

        print("⚠ Syntax issue detected.")

        if "expected ':'" in error.msg:

            print(
                "Fix: Add ':' after if, for, while, "
                "function or class definitions."
            )

        elif "was never closed" in error.msg:

            print(
                "Fix: Check missing ), ], or } brackets."
            )

        elif "unterminated string" in error.msg:

            print(
                "Fix: Check missing quotation marks."
            )

        else:

            print(
                "Fix: Check the syntax near "
                f"line {error.lineno}."
            )

        return

    defined = set()
    used = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Name):

            if isinstance(node.ctx, ast.Store):
                defined.add(node.id)

            elif isinstance(node.ctx, ast.Load):
                used.add(node.id)

    builtins = {
        "print",
        "input",
        "len",
        "range",
        "int",
        "float",
        "str",
        "list",
        "dict",
        "set",
        "tuple",
        "sum",
        "min",
        "max",
        "abs",
        "round",
        "enumerate",
        "zip",
        "sorted"
    }

    undefined = used - defined - builtins

    if undefined:

        for name in sorted(undefined):

            suggestions = difflib.get_close_matches(
                name,
                defined,
                n=1,
                cutoff=0.6
            )

            print(
                f"⚠ '{name}' may be undefined."
            )

            if suggestions:

                print(
                    f"Smart suggestion: Did you mean "
                    f"'{suggestions[0]}'?"
                )

    # ---------- Division by Zero ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.BinOp):

            if isinstance(node.op, ast.Div):

                if isinstance(node.right, ast.Constant):

                    if node.right.value == 0:

                        print(
                            "⚠ Division by zero detected."
                        )

                        print(
                            "Smart fix: Make sure the "
                            "divisor is not zero."
                        )

    # ---------- == None ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.Compare):

            for comparator in node.comparators:

                if (
                    isinstance(comparator, ast.Constant)
                    and comparator.value is None
                ):

                    print(
                        "⚠ Style improvement: "
                        "Use 'is None' instead of '== None'."
                    )

    # ---------- Boolean Comparison ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.Compare):

            for comparator in node.comparators:

                if isinstance(comparator, ast.Constant):

                    if comparator.value is True:

                        print(
                            "⚠ Style improvement: "
                            "Use the condition directly "
                            "instead of '== True'."
                        )

                    elif comparator.value is False:

                        print(
                            "⚠ Style improvement: "
                            "Use 'not condition' instead "
                            "of '== False'."
                        )

    # ---------- Bare Except ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.ExceptHandler):

            if node.type is None:

                print(
                    "⚠ Avoid bare 'except:'."
                )

                print(
                    "Smart fix: Catch a specific "
                    "exception type."
                )

    # ---------- Wildcard Imports ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.ImportFrom):

            for alias in node.names:

                if alias.name == "*":

                    print(
                        "⚠ Avoid wildcard imports."
                    )

                    print(
                        "Smart fix: Import only the "
                        "names you need."
                    )

    # ---------- Mutable Default Arguments ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.FunctionDef):

            defaults = node.args.defaults

            for default in defaults:

                if isinstance(
                    default,
                    (ast.List, ast.Dict, ast.Set)
                ):

                    print(
                        f"⚠ Function '{node.name}' "
                        "uses a mutable default argument."
                    )

                    print(
                        "Smart fix: Use None as the "
                        "default and create the object inside."
                    )

    # ---------- Built-in Shadowing ----------

    python_builtins = {
        "list",
        "str",
        "int",
        "float",
        "dict",
        "set",
        "tuple",
        "input",
        "print",
        "sum",
        "max",
        "min",
        "id",
        "type",
        "range"
    }

    for name in defined:

        if name in python_builtins:

            print(
                f"⚠ '{name}' shadows a Python built-in."
            )

            print(
                f"Smart fix: Choose another variable "
                f"name instead of '{name}'."
            )

    # ---------- range(len()) ----------

    for node in ast.walk(tree):

        if isinstance(node, ast.For):

            if isinstance(node.iter, ast.Call):

                if (
                    isinstance(node.iter.func, ast.Name)
                    and node.iter.func.id == "range"
                ):

                    if node.iter.args:

                        first_arg = node.iter.args[0]

                        if (
                            isinstance(first_arg, ast.Call)
                            and isinstance(
                                first_arg.func,
                                ast.Name
                            )
                            and first_arg.func.id == "len"
                        ):

                            print(
                                "⚠ Improvement: "
                                "Consider using enumerate() "
                                "instead of range(len(...))."
                            )

    print("\n✓ Smart Fix analysis completed.")


# =========================================================
# PROFESSIONAL COMPLEXITY ANALYSIS
# =========================================================

def complexity_analysis(code):

    print("\n========== COMPLEXITY ANALYSIS ==========")

    try:
        tree = ast.parse(code)

    except SyntaxError:

        print("Fix syntax errors first.")
        return

    # -----------------------------------------------------
    # BASIC CODE STATISTICS
    # -----------------------------------------------------

    lines = [
        line
        for line in code.splitlines()
        if line.strip()
    ]

    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    ]

    classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]

    loops = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.For, ast.While))
    ]

    conditions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
    ]

    try_blocks = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Try)
    ]

    boolean_conditions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.BoolOp)
    ]

    print("📊 Code Structure")
    print("------------------------------")
    print("Lines of code:", len(lines))
    print("Functions:", len(functions))
    print("Classes:", len(classes))
    print("Loops:", len(loops))
    print("Conditions:", len(conditions))
    print("Try blocks:", len(try_blocks))

    # -----------------------------------------------------
    # CYCLOMATIC COMPLEXITY
    # -----------------------------------------------------

    decision_points = 0

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.While,
                ast.Try,
                ast.ExceptHandler,
                ast.IfExp
            )
        ):

            decision_points += 1

    boolean_points = 0

    for node in boolean_conditions:

        boolean_points += len(node.values) - 1

    cyclomatic = 1 + decision_points + boolean_points

    print("\n🔢 Cyclomatic Complexity")
    print("------------------------------")
    print(
        "Estimated cyclomatic complexity:",
        cyclomatic
    )

    if cyclomatic <= 5:

        print("Complexity level: Simple")
        print(
            "✓ Code is easy to understand and test."
        )

    elif cyclomatic <= 10:

        print("Complexity level: Moderate")
        print(
            "⚠ Consider simplifying some conditions "
            "or splitting logic into functions."
        )

    else:

        print("Complexity level: High")
        print(
            "⚠ Code may be difficult to test and maintain."
        )

    # -----------------------------------------------------
    # NESTING DEPTH
    # -----------------------------------------------------

    def get_nesting_depth(node, current_depth=0):

        max_depth = current_depth

        for child in ast.iter_child_nodes(node):

            if isinstance(
                child,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.Try,
                    ast.With
                )
            ):

                child_depth = current_depth + 1

            else:

                child_depth = current_depth

            deeper_depth = get_nesting_depth(
                child,
                child_depth
            )

            if deeper_depth > max_depth:
                max_depth = deeper_depth

        return max_depth

    max_nesting = get_nesting_depth(tree)

    print("\n🏗 Nesting Analysis")
    print("------------------------------")
    print("Maximum nesting depth:", max_nesting)

    if max_nesting <= 2:

        print("✓ Nesting depth is easy to follow.")

    elif max_nesting <= 4:

        print(
            "⚠ Moderate nesting detected."
        )

        print(
            "Suggestion: Consider simplifying "
            "deeply nested logic."
        )

    else:

        print(
            "⚠ Deep nesting detected."
        )

        print(
            "Suggestion: Extract nested logic "
            "into separate functions."
        )

    # -----------------------------------------------------
    # NESTED LOOP DETECTION
    # -----------------------------------------------------

    class LoopDepthVisitor(ast.NodeVisitor):

        def __init__(self):

            self.current_depth = 0
            self.max_depth = 0
            self.nested_loop_found = False

        def visit_For(self, node):

            self.current_depth += 1

            if self.current_depth > 1:
                self.nested_loop_found = True

            self.max_depth = max(
                self.max_depth,
                self.current_depth
            )

            self.generic_visit(node)

            self.current_depth -= 1

        def visit_While(self, node):

            self.current_depth += 1

            if self.current_depth > 1:
                self.nested_loop_found = True

            self.max_depth = max(
                self.max_depth,
                self.current_depth
            )

            self.generic_visit(node)

            self.current_depth -= 1

    loop_visitor = LoopDepthVisitor()
    loop_visitor.visit(tree)

    print("\n🔁 Loop Analysis")
    print("------------------------------")
    print("Total loops:", len(loops))
    print(
        "Maximum nested loop depth:",
        loop_visitor.max_depth
    )

    if loop_visitor.nested_loop_found:

        print(
            "⚠ Nested loops detected."
        )

        print(
            "Nested loops can increase execution time."
        )

    elif loops:

        print(
            "✓ No nested loops detected."
        )

    else:

        print(
            "✓ No loops detected."
        )

    # -----------------------------------------------------
    # TIME COMPLEXITY ESTIMATE
    # -----------------------------------------------------

    print("\n⏱ Time Complexity Estimate")
    print("------------------------------")

    if loop_visitor.max_depth >= 3:

        time_complexity = "Potentially O(n³) or higher"

        print(
            "Estimated time complexity:",
            time_complexity
        )

        print(
            "Reason: Three or more levels of "
            "nested loops may be present."
        )

    elif loop_visitor.max_depth == 2:

        time_complexity = "Potentially O(n²)"

        print(
            "Estimated time complexity:",
            time_complexity
        )

        print(
            "Reason: Nested loops can cause "
            "quadratic growth."
        )

    elif loop_visitor.max_depth == 1:

        time_complexity = "Potentially O(n)"

        print(
            "Estimated time complexity:",
            time_complexity
        )

        print(
            "Reason: A loop may process "
            "input elements sequentially."
        )

    elif functions or conditions:

        time_complexity = "Potentially O(1) for basic operations"

        print(
            "Estimated time complexity:",
            time_complexity
        )

        print(
            "Reason: No loops were detected."
        )

    else:

        time_complexity = "O(1)"

        print(
            "Estimated time complexity:",
            time_complexity
        )

        print(
            "Reason: Basic constant-time operations detected."
        )

    # -----------------------------------------------------
    # SPACE COMPLEXITY ESTIMATE
    # -----------------------------------------------------

    print("\n💾 Space Complexity Estimate")
    print("------------------------------")

    list_creations = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.List)
    )

    dict_creations = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Dict)
    )

    set_creations = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Set)
    )

    comprehensions = sum(
        1
        for node in ast.walk(tree)
        if isinstance(
            node,
            (
                ast.ListComp,
                ast.SetComp,
                ast.DictComp
            )
        )
    )

    if comprehensions > 0:

        print(
            "Estimated space complexity: O(n)"
        )

        print(
            "Reason: Collection comprehensions "
            "may store multiple elements."
        )

    elif (
        list_creations > 0
        or dict_creations > 0
        or set_creations > 0
    ):

        print(
            "Estimated space complexity: O(n)"
        )

        print(
            "Reason: Collection objects are created."
        )

    else:

        print(
            "Estimated space complexity: O(1)"
        )

        print(
            "Reason: No major dynamic collections "
            "were detected."
        )

    # -----------------------------------------------------
    # FUNCTION-WISE COMPLEXITY
    # -----------------------------------------------------

    if functions:

        print("\n🧩 Function Complexity")
        print("------------------------------")

        for function in functions:

            function_decisions = 0

            function_loops = 0

            for node in ast.walk(function):

                if isinstance(
                    node,
                    (
                        ast.If,
                        ast.For,
                        ast.While,
                        ast.Try,
                        ast.ExceptHandler
                    )
                ):

                    function_decisions += 1

                if isinstance(
                    node,
                    (ast.For, ast.While)
                ):

                    function_loops += 1

            function_complexity = (
                1 + function_decisions
            )

            if function_complexity <= 5:

                level = "Simple"

            elif function_complexity <= 10:

                level = "Moderate"

            else:

                level = "High"

            print(
                f"• {function.name}(): "
                f"complexity {function_complexity} "
                f"({level})"
            )

            print(
                f"  Loops inside function: "
                f"{function_loops}"
            )

    # -----------------------------------------------------
    # OPTIMIZATION SUGGESTIONS
    # -----------------------------------------------------

    print("\n🚀 Optimization Suggestions")
    print("------------------------------")

    suggestions = []

    if loop_visitor.nested_loop_found:

        suggestions.append(
            "Try to reduce nested loops where possible."
        )

    if max_nesting > 3:

        suggestions.append(
            "Reduce deep nesting by extracting "
            "logic into separate functions."
        )

    if cyclomatic > 10:

        suggestions.append(
            "Reduce the number of decision points "
            "to make testing easier."
        )

    if len(functions) == 0 and len(lines) > 15:

        suggestions.append(
            "Consider dividing larger code into functions."
        )

    if len(loops) > 3:

        suggestions.append(
            "Review repeated loops and look for "
            "more efficient approaches."
        )

    if not suggestions:

        suggestions.append(
            "Current code structure looks manageable."
        )

        suggestions.append(
            "Continue testing with different inputs."
        )

    for suggestion in suggestions:

        print("•", suggestion)

    # -----------------------------------------------------
    # FINAL SUMMARY
    # -----------------------------------------------------

    print("\n🏆 Complexity Summary")
    print("------------------------------")

    print(
        f"Overall complexity: {cyclomatic}"
    )

    print(
        f"Nesting depth: {max_nesting}"
    )

    print(
        f"Loop depth: {loop_visitor.max_depth}"
    )

    print(
        f"Estimated time: {time_complexity}"
    )

    print(
        "\nNote: Complexity values are static "
        "estimates based on code structure. "
        "Actual performance depends on input size "
        "and the operations performed."
    )

    print(
        "\n✓ Professional complexity analysis completed."
    )


# =========================================================
# PROGRAM EXECUTION
# =========================================================

def execute_code(code):

    print("\n========== PROGRAM OUTPUT ==========")

    blocked_modules = {
        "os",
        "subprocess",
        "socket",
        "shutil",
        "pathlib",
        "requests",
        "urllib",
        "ctypes"
    }

    blocked_functions = {
        "exec",
        "eval",
        "compile",
        "__import__",
        "open",
        "input"
    }

    try:

        tree = ast.parse(code)

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:

                    if alias.name.split(".")[0] in blocked_modules:

                        print(
                            "⚠ Execution blocked for safety."
                        )

                        return

            elif isinstance(node, ast.ImportFrom):

                if node.module:

                    if node.module.split(".")[0] in blocked_modules:

                        print(
                            "⚠ Execution blocked for safety."
                        )

                        return

            elif isinstance(node, ast.Call):

                if isinstance(node.func, ast.Name):

                    if node.func.id in blocked_functions:

                        print(
                            f"⚠ Execution blocked: "
                            f"{node.func.id}() is not allowed."
                        )

                        return

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        ) as file:

            file.write(code)
            file_path = file.name

        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.stdout:

            print(result.stdout)

        if result.stderr:

            print("Runtime error:")
            print(result.stderr)

        if not result.stdout and not result.stderr:

            print("Program executed successfully.")
            print("No output was produced.")

    except subprocess.TimeoutExpired:

        print(
            "⚠ Program stopped because it took "
            "too long to finish."
        )

    except Exception as error:

        print("Execution error:", error)

    finally:

        try:

            if "file_path" in locals():
                os.remove(file_path)

        except Exception:
            pass


# =========================================================
# PROFESSIONAL MENTOR FEEDBACK
# =========================================================

def mentor_feedback(code):

    print("\n========== MENTOR FEEDBACK ==========")

    try:

        tree = ast.parse(code)

    except SyntaxError:

        print(
            "⚠ Mentor advice: Fix the syntax errors first."
        )

        print(
            "Once the syntax is corrected, Code Mentor "
            "can provide detailed feedback."
        )

        return

    # ---------- Basic Statistics ----------

    lines = [
        line
        for line in code.splitlines()
        if line.strip()
    ]

    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    ]

    loops = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.For, ast.While))
    ]

    conditions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
    ]

    variables = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
    ]

    print("📊 Code Overview")
    print("------------------------------")
    print("Lines:", len(lines))
    print("Variables:", len(variables))
    print("Functions:", len(functions))
    print("Loops:", len(loops))
    print("Conditions:", len(conditions))

    # ---------- Learning Level ----------

    print("\n🎯 Learning Feedback")

    if len(lines) <= 10:

        print(
            "• Your program is small and beginner-friendly."
        )

        print(
            "• Focus on understanding each statement clearly."
        )

    elif len(lines) <= 30:

        print(
            "• Your program has a moderate amount of code."
        )

        print(
            "• Start organizing repeated logic into functions."
        )

    else:

        print(
            "• Your program is becoming larger."
        )

        print(
            "• Divide the program into smaller reusable functions."
        )

    # ---------- Functions ----------

    if functions:

        print("\n🧩 Functions")

        print(
            f"• You created {len(functions)} function(s)."
        )

        print(
            "• Good practice: Keep each function responsible "
            "for one clear task."
        )

    else:

        print("\n🧩 Functions")

        print(
            "• No user-defined functions were detected."
        )

        if len(lines) > 10:

            print(
                "• Consider creating functions to make "
                "the code easier to maintain."
            )

    # ---------- Loops ----------

    if loops:

        print("\n🔁 Loops")

        print(
            f"• Your code contains {len(loops)} loop(s)."
        )

        print(
            "• Make sure each loop has a clear purpose "
            "and a condition that eventually finishes."
        )

    else:

        print("\n🔁 Loops")

        print(
            "• No loops were detected."
        )

    # ---------- Conditions ----------

    if conditions:

        print("\n🔀 Conditions")

        print(
            f"• Your code contains {len(conditions)} "
            "condition(s)."
        )

        print(
            "• Keep conditions simple and readable."
        )

    else:

        print("\n🔀 Conditions")

        print(
            "• No if conditions were detected."
        )

    # ---------- Coding Habits ----------

    print("\n💡 Coding Habits")

    if len(variables) > 10:

        print(
            "• You are using many variables. "
            "Group related data when possible."
        )

    else:

        print(
            "• Variable usage looks manageable."
        )

    if len(lines) > 50:

        print(
            "• Large program detected. "
            "Break it into smaller modules or functions."
        )

    else:

        print(
            "• Program size is manageable."
        )

    # ---------- Improvement Advice ----------

    print("\n🚀 Mentor Suggestions")

    suggestions = [
        "Use meaningful variable names.",
        "Keep functions short and focused.",
        "Avoid repeating the same code.",
        "Handle possible errors using appropriate exceptions.",
        "Test your program with different inputs.",
        "Write simple code first, then improve it step by step."
    ]

    for suggestion in suggestions:

        print("•", suggestion)

    # ---------- Final Mentor Message ----------

    print("\n🏆 Mentor Summary")

    if len(functions) > 0 and len(loops) > 0:

        print(
            "Nice work! Your program already uses "
            "important programming concepts."
        )

        print(
            "Next goal: improve readability, "
            "reusability and error handling."
        )

    elif len(loops) > 0:

        print(
            "Good progress! You are practicing "
            "repetition and program flow."
        )

        print(
            "Next goal: learn functions and "
            "organize your code better."
        )

    elif len(functions) > 0:

        print(
            "Good job! Using functions is an important "
            "step toward writing reusable programs."
        )

        print(
            "Next goal: improve function design "
            "and error handling."
        )

    else:

        print(
            "Good start! Keep practicing basic Python "
            "statements and gradually add functions, "
            "loops and conditions."
        )

    print(
        "\n⭐ Mentor Tip: "
        "Write simple code first, understand it completely, "
        "then improve it step by step."
    )


# =========================================================
# RUN COMPLETE ANALYSIS
# =========================================================

def _run_analysis(code):

    print("========== CODE MENTOR ANALYSIS ==========")

    print(
        "\nCode Mentor is analyzing your Python program..."
    )

    check_syntax(code)

    check_runtime_errors(code)

    explain_code(code)

    check_code_quality(code)

    smart_fix(code)

    complexity_analysis(code)

    execute_code(code)

    mentor_feedback(code)

    print("\n========== ANALYSIS COMPLETED ==========")


# =========================================================
# API FUNCTION
# =========================================================

def analyze_code(code):

    output = io.StringIO()

    with redirect_stdout(output):

        _run_analysis(code)

    return output.getvalue()


# =========================================================
# TERMINAL MODE
# =========================================================

if __name__ == "__main__":

    print("== Code Mentor is Ready ==")

    print("\nEnter your Python code.")
    print("Type END when your code is finished.\n")

    lines = []

    while True:

        line = input()

        if line.strip() == "END":
            break

        lines.append(line)

    code = "\n".join(lines)

    print("\nYou entered code is:")
    print(code)

    result = analyze_code(code)

    print("\n" + result)