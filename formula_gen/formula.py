import os
import json
import re
import random

from formula_gen.utils import ArithOPS, EqualOPS, Types, equalOps, formulaTypes, arithOps

from Microsoft.Formula.CommandLine import CommandInterface, CommandLineProgram
from System.IO import StringWriter
from System import Console  

def get_random_decimal(type_rand):
    match type_rand:
        case Types.Integer:
            return str(random.randint(0,10000))
        case Types.Real:
            return str(round(random.uniform(0.0, 10000.0), 2))
        case _:
            raise Exception("Type not found in utils.formulaTypes.")

def generate_domain():
    type_rand = random.randint(0,1)
    type_str = formulaTypes[Types(type_rand)]

    num_str = []
    num_eq = []
    arithOps_str = []
    equalOps_str = []

    for i in range(2):
        num_str.append(get_random_decimal(Types(type_rand)))
        num_eq.append(get_random_decimal(Types(type_rand)))
        ops_str = arithOps[ArithOPS(random.randint(0,1))]
        eops_str = equalOps[EqualOPS(random.randint(0,3))]
        if i > 0:
            while ops_str in arithOps_str[0]:
                ops_str = arithOps[ArithOPS(random.randint(0,1))]
            while eops_str in equalOps_str[0]:
                eops_str = equalOps[EqualOPS(random.randint(0,3))]
        arithOps_str.append(ops_str)
        equalOps_str.append(eops_str)
    # Randomize names of domain, partial model, and constructors. 
    domain = "domain DOM"
    domain += "\n"
    domain += "{"
    domain += "\n"
    domain += "\tA ::= new (id1: " + type_str + ")."
    domain += "\n"
    domain += "\tB ::= (id1: " + type_str + ")."
    domain += "\n"
    domain += "\tC ::= (id1: " + type_str + ")."
    domain += "\n"
    domain += "\tB(y) :- A(x), x " + equalOps_str[0] + " " + num_str[0] + ", y = x " + arithOps_str[0] + " " + num_eq[0] + "."
    domain += "\n"
    domain += "\tC(y) :- A(x), x " + equalOps_str[1] + " " + num_str[1] + ", y = x " + arithOps_str[1] + " " + num_eq[1] + "."
    domain += "\n"
    domain += "\tgoodModel :- B(x)."
    domain += "\n"
    domain += "\tbadModel :- C(x)."
    domain += "\n"
    domain += "\tconforms goodModel, badModel."
    domain += "\n"
    domain += "}"
    return domain, equalOps_str, num_str

def generate_partial_model():
    partial_model = "partial model pm of DOM"
    partial_model += "\n"
    partial_model += "{"
    partial_model += "\n"
    partial_model += "\tA(x)."
    partial_model += "\n"
    partial_model += "}"
    return partial_model

def generate_4ml():
    temp_path = os.path.abspath("./temp.4ml")
    if os.path.isfile(temp_path):
        file = open(temp_path, 'w')
        domain, equalOps_str, num_str = generate_domain()
        file.write(domain)
        file.write("\n\n")
        file.write(generate_partial_model())
        file.close()
        return domain, equalOps_str, num_str
    else:
        raise Exception("temp.4ml missing from formula_gen directory.")

def generate_solution():
    sw = StringWriter()
    Console.SetOut(sw)
    Console.SetError(sw)

    sink = CommandLineProgram.ConsoleSink()
    chooser = CommandLineProgram.ConsoleChooser()
    ci = CommandInterface(sink, chooser)

    dataList = []

    if not ci.DoCommand("wait on"):
        return

    for i in range(100):
        if not ci.DoCommand("unload *"):
            return
        if not ci.DoCommand("tunload *"):
            return
        
        domain, equalOps_str, num_str = generate_4ml()

        file = open(os.path.abspath("./temp.4ml"), 'r')
        file_lines = file.readlines()
        file_joined = ""
        for line in file_lines:
            file_joined += " " + line.strip().replace("\n", " ")
        file.close()

        if not ci.DoCommand("load " + os.path.abspath("./temp.4ml")):
            return

        domain = "DOM"
        partial_model = "pm"
        solve_cmd = "solve " + partial_model + " 1 " + domain + ".conforms"
        domain_match = re.search("domain\s+" + domain + "\s*\{(.*?)\}", file_joined)
        domain_str = domain_match.group()
        partial_match = re.search("partial\s+model\s+" + partial_model + "\s+of\s+" + domain + "\s*\{(.*?)\}", file_joined)
        partial_str = partial_match.group()

        if not ci.DoCommand(solve_cmd):
            return 

        sw.GetStringBuilder().Clear()
        if not ci.DoCommand("extract 0 0 0"):
            return
        output_list = sw.ToString().split("\n")
        conflict_str = ""
        solution_str = ""

        entry = {}
        for idx, line in enumerate(output_list):
            if "Model not solvable." in line:
                entry["instruction"] = "Explain why this model is not solvable"
                for subline in output_list:
                    if "Conflicts:" in subline:
                        conflict_str += subline.strip().replace("Conflicts: ", "")
                entry["input"] = domain_str + ", " + partial_str + "," + conflict_str
                output = "This model cannot be solved because it requires a goodModel and a badModel.\n"
                output += "A goodModel is derived if a B(x) exists. A B(x) exists only if an A(x) exists where x " + equalOps_str[0] + " " + num_str[0] + ". "
                output += "A badModel is derived if a C(x) exists. A C(x) exists only if an A(x) exists where x " + equalOps_str[1] + " " + num_str[1] + ". "
                output += "The original model contains only one A(x), and x cannot be both " + equalOps_str[0] + " " + num_str[0] + " and " + equalOps_str[1] + " " + num_str[1] + "."
                entry["output"] = output
                dataList.append(entry)
            elif "Solution number" in line:
                entry["instruction"] = "Explain why this model is solvable"
                start = idx + 1
                nextstr = "Solution"
                while len(nextstr) > 0:
                    nextstr = output_list[start]
                    solution_str += " " + nextstr
                    start += 1
                entry["input"] = domain_str + ", " + partial_str + ", " + solution_str.strip()
                output = "This model can be solved because both goodModel and badModel are derived where x " + equalOps_str[0] + " " + num_str[0] + " and "
                output += "where x " + equalOps_str[1] + " " + num_str[1] + ". "
                output += "The original model has one A(x), and x can be solved with " + solution_str.strip() + "."
                entry["output"] = output
                dataList.append(entry)

    f = open(os.path.abspath("./data.json"), 'w')
    f.write(json.dumps(dataList, indent=4))
    f.close()