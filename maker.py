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


from __future__ import print_function

import sys
import pga
from sudokumaker.sudoku  import Puzzle
from sudokumaker.Version import VERSION
from rsclib.autosuper    import autosuper
from argparse            import ArgumentParser


class Sudoku_Maker (pga.PGA, autosuper):
    def __init__ \
        ( self
        , srand            = 42
        , do_time          = False
        , colorconstrained = False
        , diagonal         = False
        ):
        stop_on = \
            [ pga.PGA_STOP_NOCHANGE
            , pga.PGA_STOP_MAXITER
            , pga.PGA_STOP_TOOSIMILAR
            ]
        self.do_time          = do_time
        self.diagonal         = diagonal
        self.colorconstrained = colorconstrained
        pga.PGA.__init__ \
            ( self
            , int # integer allele
            , 9 * 9
            , init                = [[0, 9]] * (9 * 9)
            , maximize            = False
            , pop_size            = 500
            , num_replace         = 250
            , random_seed         = srand
            , print_options       = [pga.PGA_REPORT_STRING]
            , stopping_rule_types = stop_on
            , randomize_select    = True
            )
        self.cache_hits = 0
    # end def __init__

    cache = {}

    def endofgen (self):
        pop = pga.PGA_NEWPOP
        for p in range (self.pop_size):
            assert self.get_evaluation_up_to_date (p, pop)
            puzzle, vals = self.phenotype (p, pop)
            if vals not in self.cache:
                self.cache [vals] = self.get_evaluation (p, pop)
    # end def endofgen

    def evaluate (self, p, pop):
        puzzle, vals = self.phenotype (p, pop)
        puzzle.solve ()
        if puzzle.solvecount:
            if puzzle.solvecount == 1:
                eval = puzzle.count
            else:
                eval = 1000 - puzzle.count + puzzle.solvecount
        else:
            eval = 1000 * puzzle.count * puzzle.count
        return eval
    # end def evaluate

    def phenotype (self, p, pop):
        puzzle = Puzzle \
            ( verbose          = False
            , solvemax         = 50
            , do_time          = self.do_time
            , colorconstrained = self.colorconstrained
            , diagonal         = self.diagonal
            )
        vals   = []
        for x in range (9):
            for y in range (9):
                val    = self.get_allele (p, pop, 9 * x + y)
                if val > 9:
                    val = 0
                puzzle.set (x, y, val)
                vals.append (val)
        vals = tuple (vals)
        return puzzle, vals
    # end def phenotype

    def pre_eval (self, pop):
        for p in range (self.pop_size):
            if self.get_evaluation_up_to_date (p, pop):
                continue
            puzzle, vals = self.phenotype (p, pop)
            if vals in self.cache:
                self.set_evaluation (p, pop, self.cache [vals])
                self.set_evaluation_up_to_date (p, pop, True)
                self.cache_hits += 1
    # end def pre_eval

    def print_string (self, file, p, pop):
        self.file = file
        print ('Cache hits: %d' % self.cache_hits, file = file)
        assert self.get_evaluation_up_to_date (p, pop)
        puzzle, vals = self.phenotype (p, pop)
        e = self.get_evaluation (p, pop)
        if e >= 2000:
            assert puzzle.count * puzzle.count * 1000 == e
            solvecount = 0
        elif e > 81:
            solvecount = int (e - 1000 + puzzle.count)
            assert solvecount == e - 1000 + puzzle.count
        else:
            assert e == puzzle.count
            solvecount = 1
        print \
            ( 'Non-empty tiles: %d, solvecount: %d' % (puzzle.count, solvecount)
            , file = file
            )
        puzzle.display (file)
        self.file.flush ()
    # end def print_string

# end class Sudoku_Maker

def main ():
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
        , help    = "Numeric random seed, default=%(default)s"
        , type    = int
        , default = 42
        )
    cmd.add_argument \
        ( "-t", "--time"
        , dest    = "do_time"
        , help    = "Runtime measurement"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-v", "--version"
        , help    = "Display version"
        , action  = "version"
        , version = "%%(prog)s %s" % VERSION
        )
    args = cmd.parse_args ()
    maker = Sudoku_Maker \
        ( srand            = args.random_seed
        , do_time          = args.do_time
        , colorconstrained = args.colorconstrained
        , diagonal         = args.diagonal
        )
    maker.run ()

if __name__ == "__main__":
    main ()
