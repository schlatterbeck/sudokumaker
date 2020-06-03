#!/usr/bin/python3
# Copyright (C) 2005-2020 Dr. Ralf Schlatterbeck Open Source Consulting.
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


from __future__ import print_function

import sys
from sudokumaker.sudoku import Puzzle
from rsclib.autosuper   import autosuper
from pga                import PGA, PGA_STOP_TOOSIMILAR, PGA_STOP_MAXITER \
                             , PGA_STOP_NOCHANGE, PGA_REPORT_STRING \
                             , PGA_POPREPL_BEST

class Sudoku_Maker (PGA, autosuper) :
    def __init__ \
        ( self
        , srand            = 42
        , verbose          = False
        , do_time          = False
        , colorconstrained = False
        , diagonal         = False
        ) :
        stop_on = [PGA_STOP_NOCHANGE, PGA_STOP_MAXITER, PGA_STOP_TOOSIMILAR]
        self.verbose          = verbose
        self.do_time          = do_time
        self.diagonal         = diagonal
        self.colorconstrained = colorconstrained
        PGA.__init__ \
            ( self
            , int # integer allele
            , 9 * 9
            , init                = [[0, 9]] * (9 * 9)
            , maximize            = False
            , pop_size            = 500
            , num_replace         = 250
            , random_seed         = srand
            , print_options       = [PGA_REPORT_STRING]
            , stopping_rule_types = stop_on
            , randomize_select    = True
            )
    # end def __init__

    cache = {}

    def evaluate (self, p, pop) :
        puzzle = Puzzle \
            ( verbose          = False
            , solvemax         = 50
            , do_time          = self.do_time
            , colorconstrained = self.colorconstrained
            , diagonal         = self.diagonal
            )
        count  = 0
        vals   = []
        for x in range (9) :
            for y in range (9) :
                val    = self.get_allele (p, pop, 9 * x + y)
                if val > 9 : val = 0
                count += val != 0
                puzzle.set (x, y, val)
                vals.append (val)
        vals = tuple (vals)
        if self.verbose :
            puzzle.display (self.file)
            print (count, end = ' ', file = self.file)
            self.file.flush ()
        if vals in self.cache :
            if self.verbose :
                print ("H", end = ' ', file = self.file)
                self.file.flush ()
            solvecount = self.cache [vals]
        else :
            puzzle.solve ()
            solvecount = puzzle.solvecount
            self.cache [vals] = solvecount
        if self.verbose :
            print (solvecount, file = self.file)
            if puzzle.runtime :
                print ("runtime: %s" % puzzle.runtime, file = self.file)
            self.file.flush ()
        if solvecount :
            if solvecount == 1 :
                eval = count
            else :
                eval = 1000 - count + solvecount
        else :
            eval = 1000 * count * count
        return eval
    # end def evaluate

    def print_string (self, file, p, pop) :
        self.file    = file
        verbose      = self.verbose
        self.verbose = True
        self.evaluate (p, pop)
        self.verbose = verbose
        self.file.flush ()
        return self.__super.print_string (file, p, pop)
    # end def print_string

# end class Sudoku_Maker

def main () :
    from argparse import ArgumentParser
    from Version  import VERSION

    cmd = ArgumentParser ()
    cmd.add_argument \
        ( "-c", "--colorconstrained"
        , dest    = "colorconstrained"
        , help    = "Add color constraint"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-d", "--diagonal"
        , dest    = "diagonal"
        , help    = "Add diagonality constraint"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-r", "--random-seed"
        , dest    = "random_seed"
        , help    = "Numeric random seed, required argument"
        , type    = int
        )
    cmd.add_argument \
        ( "-t", "--time"
        , dest    = "do_time"
        , help    = "Runtime measurement"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-V", "--verbose"
        , dest    = "verbose"
        , help    = "Verbose output during search"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-v", "--version"
        , help    = "Display version"
        , action  = "version"
        , version = "%%(prog)s %s" % VERSION
        )
    args = cmd.parse_args ()
    if args.random_seed is None :
        cmd.error ("-r or --random-seed option is required")
    maker = Sudoku_Maker \
        ( srand            = args.random_seed
        , verbose          = args.verbose
        , do_time          = args.do_time
        , colorconstrained = args.colorconstrained
        , diagonal         = args.diagonal
        )
    maker.run ()

if __name__ == "__main__" :
    main ()
