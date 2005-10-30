#!/usr/bin/python2.4

import sys
from sudoku           import Puzzle
from rsclib.autosuper import autosuper
from pga              import PGA, PGA_STOP_TOOSIMILAR, PGA_STOP_MAXITER \
                           , PGA_STOP_NOCHANGE, PGA_REPORT_STRING \
                           , PGA_POPREPL_BEST
import sys

class Sudoku_Maker (PGA, autosuper) :
    def __init__ (self, srand = 42, verbose = False) :
        stop_on = [PGA_STOP_NOCHANGE, PGA_STOP_MAXITER, PGA_STOP_TOOSIMILAR]
        self.verbose = verbose
        PGA.__init__ \
            ( self
            , type (2) # integer allele
            , 9 * 9
            , init                = [[0, 9]] * (9 * 9)
            , maximize            = False
            , pop_size            = 500
            , num_replace         = 250
            , random_seed         = srand
            , print_options       = [PGA_REPORT_STRING]
            , stopping_rule_types = stop_on
            )
    # end def __init__

    def evaluate (self, p, pop) :
        puzzle = Puzzle (verbose = False, solvemax = 50)
        count  = 0
        for x in range (9) :
            for y in range (9) :
                val    = self.get_allele (p, pop, 9 * x + y)
                if val > 9 : val = 0
                count += val != 0
                puzzle.set (x, y, val)
        if self.verbose :
            puzzle.display ()
            print count,
            sys.stdout.flush ()
        puzzle.solve ()
        if self.verbose :
            print puzzle.solvecount
            sys.stdout.flush ()
        if puzzle.solvecount :
            if puzzle.solvecount == 1 :
                return count
            return 1000 - count + puzzle.solvecount
        return 1000 * count * count
    # end def evaluate

    def print_string (self, file, p, pop) :
        verbose      = self.verbose
        self.verbose = True
        self.evaluate (p, pop)
        self.verbose = verbose
        return self.__super.print_string (file, p, pop)
    # end def print_string
# end class Sudoku_Maker

if __name__ == "__main__" :
    srand = 42
    if len (sys.argv) > 1 :
        srand = int (sys.argv [1])
    maker = Sudoku_Maker (srand = srand, verbose = True)
    maker.run ()
