import os
from os import listdir
from os.path import isfile, join
import json
import randomname
import operator
import itertools
import re
import random

from formula_gen.utils import ArithOPS, AggOPS, EqualOPS, Types 
from formula_gen.utils import equalOps, arithOps, aggOps
from formula_gen.utils import FORMULA_PARSER, FORMULA_LANGUAGE

from Microsoft.Formula.CommandLine import CommandInterface, CommandLineProgram
from System.IO import StringWriter
from System import Console  

example_path = '/Users/stephen/git/formula/Doc/Samples'
symbolic_path = '/Users/stephen/git/formula/Tst/Tests/Symbolic'

def get_random_decimal(type_rand):
    match type_rand:
        case Types.Integer:
            return str(random.randint(-1000,1000))
        case Types.Real:
            return str(round(random.uniform(-1000.0, 1000.0), 2))
        case _:
            raise Exception("Type not found in utils.formulaTypes.")

def accumulate(l):
    it = itertools.groupby(sorted(l), operator.itemgetter(0))
    d = {}
    for key, subiter in it:
        if key.text.decode() not in d:
            d[key.text.decode()] = [item[0].text.decode() for item in subiter if item[0].text.decode() == key.text.decode()]
        else:
            d[key.text.decode()] += [item[0].text.decode() for item in subiter if item[0].text.decode() == key.text.decode()]

    return d

def generate_domain(file_txt):
    relops_query = FORMULA_LANGUAGE.query("""
    (constraint (func_term) (relop) @rel_op (func_term (atom (constant (_) @num))))
    (constraint (func_term) (relop) (func_term (func_term) (binop) @binop (func_term (atom (constant (_) @num))))) 
    """)

    name_query = FORMULA_LANGUAGE.query("""
    (model_sig_config (model_sig (model_intro (bareid) @pm_name (mod_ref (mod_ref_no_rename (bareid) @dom_name)))))
    (domain (domain_sig_config (domain_sig (bareid) @dom_name)))
    (type_decl (bareid) @type_name)
    (constraint (id) (func_term (atom (id) @type_name)))
    (rule (func_term_list (func_or_compr (func_term (atom (id) @rule_name)))))
    (dom_sentence (body_list (body (constraint (func_term (atom (id) @rule_name))))))
    (rule (func_term_list (func_or_compr (func_term (id) @rule_name))))
    (rule (body_list (body (constraint (func_term (id) @rule_name)))))
    (rule (body_list (body (constraint (func_term (atom (id) @rule_name))))))
    """)
    tree = FORMULA_PARSER.parse(bytes(file_txt, 'utf8'), keep_text=True)

    cap = name_query.captures(tree.root_node)
    print(accumulate(cap))
    
    cap = relops_query.captures(tree.root_node)
    for node in cap:
        n, t = node
        newtxt = ""
        if t == 'rel_op':
            newtxt = equalOps[EqualOPS(random.randint(0,3))]
        elif t == 'num':
            newtxt = get_random_decimal(Types.Integer)
        elif t == 'binop':
            newtxt = arithOps[ArithOPS(random.randint(0,1))]

        if len(newtxt) > 0:
            file_txt = file_txt.replace(n.text.decode(), newtxt)
    
    file = open("./temp.4ml", 'w')
    try:
        file.write(file_txt)
    finally:
        file.close()
    
    return FORMULA_PARSER.parse(bytes(file_txt, 'utf8'), tree, keep_text=True)

def generate_solution():
    sw = StringWriter()
    Console.SetOut(sw)
    Console.SetError(sw)

    sink = CommandLineProgram.ConsoleSink()
    chooser = CommandLineProgram.ConsoleChooser()
    ci = CommandInterface(sink, chooser)

    dataList = []

    if not ci.DoCommand("wait on"):
        raise Exception("Wait on command failed.")
    
    example_files = [join(example_path, f) for f in listdir(example_path) if isfile(join(example_path, f)) and f.endswith(".4ml") and not f.startswith("arm")]
    symbolic_files = [join(symbolic_path, f) for f in listdir(symbolic_path) if isfile(join(symbolic_path, f))and f.endswith(".4ml")]
    total_files = example_files + symbolic_files

    for i in range(1):
        if not ci.DoCommand("unload *"):
            raise Exception("Unload command failed.")
        if not ci.DoCommand("tunload *"):
            raise Exception("tunload command failed.")
        
        temp_file = random.choice(total_files)

        file = open("/Users/stephen/git/formula/Tst/Tests/Symbolic/Simple.4ml", 'r')
        file_txt = ""
        try:
            file_txt = file.read()
        finally:
            file.close()

        tree = generate_domain(file_txt)

        if not ci.DoCommand("load " + os.path.abspath("./temp.4ml")):
            return

        name_query = FORMULA_LANGUAGE.query("""
        (model_sig_config (model_sig (model_intro (bareid) @pm_name (mod_ref (mod_ref_no_rename (bareid) @dom_name)))))
        """)

        cap = name_query.captures(tree.root_node)
        domain = ""
        partial_model = ""

        for node in cap:
            n, t = node
            if t == 'dom_name':
                domain = n.text.decode()
            elif t == 'pm_name':
                partial_model = n.text.decode()
        print(domain)
        print(partial_model)
        solve_cmd = "solve " + partial_model + " 10 " + domain + ".conforms"

        if not ci.DoCommand(solve_cmd):
            raise Exception("Solve command failed.")

        sw.GetStringBuilder().Clear()
        if not ci.DoCommand("extract 0 0 test"):
            raise Exception("Extract command failed.")
        output_list = sw.ToString().split("\n")
        conflict_str = ""
        solution_str = ""
        print(output_list)
        entry = {}
        for idx, line in enumerate(output_list):
            if "Model not solvable." in line:
                print("Model not solvable")
                print(conflict_str)
                entry["instruction"] = "Explain why this model is not solvable"
                for subline in output_list:
                    if "Conflicts:" in subline:
                        conflict_str += subline.strip().replace("Conflicts: ", "")
                entry["input"] = file_txt + "," + conflict_str
                '''output = "This model cannot be solved because it requires a goodModel and a badModel.\n"
                output += "A goodModel is derived if a B(x) exists. A B(x) exists only if an A(x) exists where x " + equalOps_str[0] + " " + num_str[0] + ". "
                output += "A badModel is derived if a C(x) exists. A C(x) exists only if an A(x) exists where x " + equalOps_str[1] + " " + num_str[1] + ". "
                output += "The original model contains only one A(x), and x cannot be both " + equalOps_str[0] + " " + num_str[0] + " and " + equalOps_str[1] + " " + num_str[1] + "."
                entry["output"] = output'''
                dataList.append(entry)
            elif "Solution number" in line:
                entry["instruction"] = "Explain why this model is solvable"
                start = idx + 1
                nextstr = "Solution"
                while len(nextstr) > 0:
                    nextstr = output_list[start]
                    solution_str += " " + nextstr
                    start += 1
                print("Model solvable")
                print(solution_str)
                entry["input"] = file_txt + ", " + solution_str.strip()
                '''output = "This model can be solved because both goodModel and badModel are derived where x " + equalOps_str[0] + " " + num_str[0] + " and "
                output += "where x " + equalOps_str[1] + " " + num_str[1] + ". "
                output += "The original model has one A(x), and x can be solved with " + solution_str.strip() + "."
                entry["output"] = output'''
                dataList.append(entry)

    f = open(os.path.abspath("./data.json"), 'w')
    f.write(json.dumps(dataList, indent=4))
    f.close()