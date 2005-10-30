#!/usr/bin/python2.4

import sys
import os
from   sudoku import Puzzle

file   = sys.stdin
name   = ''
author = None
if len (sys.argv) > 1 :
    file = open (sys.argv [1])
    name = os.path.splitext (sys.argv [1])[0]
if len (sys.argv) > 2 :
    author = sys.argv [2]
x = Puzzle  ()
x.from_file (file)
x.as_tex     (title = name, author = author)

