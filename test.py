from component import Processor
from component import ProcessorOptimization
import sys

file = open("trace1.txt")
line = file.readline()
while line:
    info = line.split()
    line = file.readline()
a = [None]