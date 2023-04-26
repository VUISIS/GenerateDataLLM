import os
from pythonnet import load
load("coreclr", runtime_config=os.path.abspath('./runtimeconfig.json'))
import clr
clr.AddReference(os.path.abspath('./CommandLine/CommandLine.dll'))