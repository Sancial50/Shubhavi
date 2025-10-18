import sympy

def solve_math_problem(problem):
    try:
        # Try to evaluate as an expression
        result = sympy.sympify(problem)
        return result
    except Exception:
        try:
            # Try to solve as an equation
            x = sympy.symbols('x')
            solutions = sympy.solve(problem, x)
            return solutions
        except Exception as e:
            return f"Could not solve the problem: {e}"

if __name__ == "__main__":
    problem = input("Enter a math problem (e.g., '2+2', 'x**2-4=0'): ")
    answer = solve_math_problem(problem)
    print("Solution:", answer)