#!/usr/bin/python3
# Copyright (C) 2005-2022 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# ****************************************************************************
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
# ****************************************************************************

import sys
import os
from   argparse            import ArgumentParser
from   sudokumaker.sudoku  import Puzzle
from   sudokumaker.Version import VERSION

def main (argv = None):
    cmd    = ArgumentParser ()
    cmd.add_argument \
        ( "file"
        , help    = "File name of sudoku file, default stdin"
        , nargs   = '?'
        )
    cmd.add_argument \
        ( "-a", "--author"
        , dest    = "author"
        , help    = "Change default author info"
        )
    cmd.add_argument \
        ( "-c", "--colorconstrained"
        , dest    = "colorconstrained"
        , help    = "Add color constraint"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-d", "--diagonal"
        , dest    = "diagonal"
        , help    = "Add diagonality coloring"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-k", "--kikagaku"
        , dest    = "kikagaku"
        , help    = "Kikagaku with color areas, read additional color defs"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-t", "--title"
        , dest    = "title"
        , help    = "Change default title info (defaults to given filename)"
        , default = ''
        )
    cmd.add_argument \
        ( "-v", "--version"
        , help    = "Display version"
        , action  = "version"
        , version = "%%(prog)s %s" % VERSION
        )
    args = cmd.parse_args (argv)
    file = sys.stdin
    name = ''
    if args.file:
        file = open (args.file)
        name = args.file
    if args.title:
        name = args.title

    x = Puzzle  \
        ( diagonal         = args.diagonal
        , colorconstrained = args.colorconstrained
        , kikagaku         = args.kikagaku
        )
    x.from_file (file)
    x.as_tex    (title = name, author = args.author)
# end def main

if __name__ == '__main__':
    main (sys.argv [1:])
