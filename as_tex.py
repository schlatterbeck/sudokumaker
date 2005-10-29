#!/usr/bin/python2.4

import sys
from   sudoku import Puzzle

file = sys.stdin
if len (sys.argv) > 1 :
    file = open (sys.argv [1])
x = Puzzle  ()
x.from_file (file)
x.as_tex     ()

