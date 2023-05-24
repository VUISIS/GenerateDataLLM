from enum import Enum
import os
from tree_sitter import Language, Parser

from Microsoft.Formula.CommandLine import IMessageSink

Language.build_library(
  os.path.abspath('./libs/tree-sitter-formula/build/formula.so'),

  [
    os.path.abspath('./libs/tree-sitter-formula')
  ]
)

FORMULA_LANGUAGE = Language(os.path.abspath('./libs/tree-sitter-formula/build/formula.so'), 'formula')

FORMULA_PARSER = Parser()
FORMULA_PARSER.set_language(FORMULA_LANGUAGE)

class EqualOPS(Enum):
    GE = 0
    LE = 1
    GT = 2
    LT = 3

class ArithOPS(Enum):
    ADD = 0
    SUB = 1

class AggOPS(Enum):
    Count = 0
    Sum = 1
    Max = 2
    Min = 3
    MaxAll = 4
    MinAll = 5
    Or = 6
    OrAll = 7
    And = 8
    AndAll = 9

class Types(Enum):
    Integer = 0
    Real = 1

arithOps = {
    ArithOPS.ADD: "+",
    ArithOPS.SUB: "-"
}

equalOps = {
    EqualOPS.GE: ">=",
    EqualOPS.LE: "<=",
    EqualOPS.GT: ">",
    EqualOPS.LT: "<"
}

aggOps = {
    AggOPS.Count: "count",
    AggOPS.Sum: "sum",
    AggOPS.Max: "max",
    AggOPS.Min: "min",
    AggOPS.MinAll: "minAll",
    AggOPS.MaxAll: "maxAll",
    AggOPS.Or: "or",
    AggOPS.OrAll: "orAll",
    AggOPS.And: "and",
    AggOPS.AndAll: "andAll"
}

formulaTypes = {
    Types.Integer: "Integer",
    Types.Real: "Real"
} 