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
            d[key.text.decode()] = [item[0] for item in subiter if item[0].text.decode() == key.text.decode()]
        else:
            d[key.text.decode()] += [item[0] for item in subiter if item[0].text.decode() == key.text.decode()]

    return d

def generate_domain(file_txt):
    relops_query = FORMULA_LANGUAGE.query("""
    (constraint (func_term) (relop) (func_term (atom (constant (_))))) @rel_constraint
    (constraint (func_term) (relop) (func_term (func_term) (binop) (func_term (atom (constant (_)))))) @bin_constraint 
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
    (rule (body_list (body (constraint (func_term (atom (id) @rule_name)) .))))
    """)
    tree = FORMULA_PARSER.parse(bytes(file_txt, 'utf8'), keep_text=True)

    cap = name_query.captures(tree.root_node)
    names = accumulate(cap)
    for item in names.items():
        k, v = item
        name = randomname.get_name()
        ns = name.split("-")
        if random.randint(0,1):
            name = ns[0]
            if random.randint(0,1):
                name = name.capitalize()
        else:
            ns[1] = ns[1].capitalize()
            name = ns[0] + ns[1]

        file_txt = re.sub("([^\w])"+k+"([^\w])", r'\1' + name + r'\2', file_txt)
    
    cap = relops_query.captures(tree.root_node)
    for node in cap:
        n, t = node
        if t == 'rel_constraint':
            newtxt = equalOps[EqualOPS(random.randint(0,3))]
            newnum = get_random_decimal(Types.Integer)
            const_list = n.text.decode().split(' ')
            if len(const_list) == 3:
                file_txt = re.sub("([^\w\d]" + const_list[0] + ")\s*" + const_list[1] + "\s*" + const_list[2]  + "([^\w\d])", r'\1' + " " + newtxt + " " + newnum + r'\2', file_txt, 1)
        elif t == 'bin_constraint':
            newtxt = arithOps[ArithOPS(random.randint(0,1))]
            newnum = get_random_decimal(Types.Integer)
            const_list = n.text.decode().split(' ')
            if len(const_list) == 3:
                file_txt = re.sub("([^\w\d]" + const_list[0] + ")\s*" + const_list[1] + "\s*" + const_list[2]  + "([^\w\d])", r'\1' + " " + newtxt + " " + newnum + r'\2', file_txt, 1)
    
    file = open(os.path.abspath("./temp.4ml"), 'w')
    try:
        file.write(file_txt)
    finally:
        file.close()
    
    return file_txt

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
    
    symbolic_files = [join(symbolic_path, f) for f in listdir(symbolic_path) if isfile(join(symbolic_path, f))and f.endswith(".4ml")]

    for ftxt in symbolic_files:
        print(ftxt)
        file = open(ftxt, 'r')
        orig_file_txt = ""
        try:
            orig_file_txt = file.read()
        finally:
            file.close()

        for idx in range(1000):
            file_txt = ""
            if not ci.DoCommand("unload *"):
                raise Exception("Unload command failed.")
            if not ci.DoCommand("tunload *"):
                raise Exception("tunload command failed.")


            if idx > 0:
                file_txt = generate_domain(orig_file_txt)

                if not ci.DoCommand("load " + os.path.abspath("./temp.4ml")):
                    return
            else:
                file_txt = orig_file_txt
                if not ci.DoCommand("load " + ftxt):
                    return
                
            tree = FORMULA_PARSER.parse(bytes(file_txt, 'utf8'), keep_text=True)

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

            solve_cmd = "solve " + partial_model + " 1 " + domain + ".conforms"

            rule_query = FORMULA_LANGUAGE.query('''
            (domain (domain_sig_config (domain_sig (bareid) @dom_name (#eq? @dom_name "''' + domain + '''"))) 
            (dom_sentences (dom_sentence_config (dom_sentence (rule) @rule))))
            (domain (domain_sig_config (domain_sig (bareid) @dom_name (#eq? @dom_name "''' + domain + '''"))) 
            (dom_sentences (dom_sentence_config (dom_sentence (body_list) @conforms))))
            ''')

            cap = rule_query.captures(tree.root_node)
            rules = {}
            conforms = []
            for node in cap:
                n, t = node
                if t == 'rule':
                    rule = n.text.decode()
                    match = re.search(r'(.+):-\s*(.*)', rule, re.DOTALL)
                    rules[match.group(1).strip()] = match.group(2).strip()
                elif t == 'conforms':
                    forms = n.text.decode()
                    if "," in forms:
                        form_list = forms.split(",")
                        for f in form_list:
                            conforms.append(f.strip())
                    else:
                        conforms.append(n.text.decode())
            if not ci.DoCommand(solve_cmd):
                raise Exception("Solve command failed.")

            sw.GetStringBuilder().Clear()
            if not ci.DoCommand("extract 0 0 test"):
                raise Exception("Extract command failed.")
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
                    entry["input"] = file_txt + "," + conflict_str
                    output = "This model cannot be solved because it requires the conformity of the following rules " 
                    output += ", ".join(conforms) + ".\n"
                    for k,v in rules.items():
                        output += "A " + k + " exists only if the following constraints are satisfied " + v + "\n"
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
                    entry["input"] = file_txt + ", " + solution_str.strip()
                    output = "This model can be solved because of the conformity of the folloeing rules "
                    output += ", ".join(conforms) + ".\n"
                    for k,v in rules.items():
                        output += "A rule " + k + " is derived because these constraints are satisfied " + v + "\n"
                    entry["output"] = output
                    dataList.append(entry)

    f = open(os.path.abspath("./data.json"), 'w')
    f.write(json.dumps(dataList, indent=4))
    f.close()