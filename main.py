import os

from formula_gen.formula import generate_solution

def main():
    if os.path.isfile(os.path.abspath("./temp.4ml")):
        generate_solution()
    else:
        raise Exception("temp.4ml missing from formula_gen directory.")

if __name__ == "__main__":
    main()