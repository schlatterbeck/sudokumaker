#!/usr/bin/python

from soduko import Puzzle
from pga    import PGA, PGA_STOP_TOOSIMILAR, PGA_STOP_MAXITER \
                 , PGA_REPORT_STRING, PGA_POPREPL_BEST
import sys

class Soduko_Maker (PGA) :
    def __init__ (self, srand = 42) :
        PGA.__init__ \
            ( self
            , type (2) # integer allele
            , 9 * 9
            , init        = [[0, 52]] * (9 * 9)
            , maximize    = False
            , random_seed = srand
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
        puzzle.display ()
        print count,
        if puzzle.possible () :
            print "possible"
            sys.stdout.flush ()
            puzzle.solve (0, 0)
        print puzzle.solvecount
        sys.stdout.flush ()
        if puzzle.solvecount :
            return puzzle.solvecount * count
        return 50 * count
    # end def evaluate
# end class Soduko_Maker

if __name__ == "__main__" :
    maker = Soduko_Maker ()
    maker.run ()
