#!/usr/bin/env python

import sys
from   sets             import Set
from   copy             import copy
from   rsclib.autosuper import autosuper

class Alternative (Set, autosuper) :
    def __init__ (self, row, col, iterator = None) :
        if iterator is None :
            iterator = range (1, 10)
        self.__super.__init__ (iterator)
        self.row = row
        self.col = col
    # end def __init__

    def __cmp__ (self, other) :
        return \
            (  cmp (len (self), len (other))
            or cmp (self.row,   other.row)
            or cmp (self.col,   other.col)
            )
    # end def __cmp__

    def __repr__ (self) :
        return "Alternative (row = %s, col = %s, %s)" \
            % (self.row, self.col, [x for x in self])
    # end def __repr__

    def copy (self) :
        return self.__class__ (self.row, self.col, self)
    # end def copy

    __str__ = __repr__
# end class Alternative

class Alternatives :
    def __init__ (self, puzzle = None, sets = None) :
        if sets :
            self.sets = sets
        else :
            self.sets = {}
            for r in range (9) :
                for c in range (9) :
                    self.sets [(r, c)] = Alternative (r, c)
            if puzzle :
                for r in range (9) :
                    for c in range (9) :
                        if puzzle [r][c] :
                            self.update (r, c, puzzle [r][c])
    # end def __init__

    def __repr__ (self) :
        s = ['Alternatives:']
        for r in range (9) :
            sets = [repr (self.sets [(r, c)]) for c in range (9)]
            s.append (', '.join (sets))
        return '\n'.join (s)
    # end def __repr__

    __str__ = __repr__

    def copy (self) :
        sets = {}
        for k, v in self.sets.iteritems () :
            sets [k] = v.copy ()
        return Alternatives (sets = sets)
    # end def copy

    def update (self, row, col, val) :
        del self.sets [(row, col)]
        for x in range (9) :
            if x != row :
                if (x, col) in self.sets :
                    self.sets [(x, col)].difference_update ((val,))
            if x != col :
                if (row, x) in self.sets :
                    self.sets [(row, x)].difference_update ((val,))
        colstart = int (col / 3) * 3
        rowstart = int (row / 3) * 3
        for r in range (rowstart, rowstart + 3) :
            for c in range (colstart, colstart + 3) :
                if  (r != row and c != col and (r, c) in self.sets) :
                    self.sets [(r, c)].difference_update ((val,))
    # end def update

    def values (self) :
        v = self.sets.values ()
        v.sort ()
        return v
    # end def iterator
# end class Alternatives

class Puzzle :
    def __init__ (self, verbose = True, solvemax = 100) :
        x = [0] * 9
        self.puzzle     = [copy (x) for i in range (9)]
        self.solvecount = 0
        self.verbose    = verbose
        self.solvemax   = solvemax
    # end def __init__

    def set (self, x, y, value) :
        self.puzzle [x][y] = value
    # end def set

    def from_file (self, file) :
        for r in range (9) :
            line = file.readline ()
            for c in range (9) :
                self.puzzle [r][c] = ord (line [c]) - ord ('0')
    # end def from_file

    def display (self) :
        for r in range (9) :
            print ''.join \
                ([chr (self.puzzle [r][c] + ord ('0')) for c in range (9)])
        print
    # end def display

    def is_ok (self, row, col) :
        assert (self.puzzle [row][col])
        # print "Try %d,%d to %d" % (row, col, self.puzzle [row][col]),
        for x in range (9) :
            if x != row and self.puzzle [x][col] == self.puzzle [row][col] :
                #print "row No: %d,%d" % (x, col)
                return False
            if x != col and self.puzzle [row][x] == self.puzzle [row][col] :
                #print "col No: %d,%d" % (row, x)
                return False
        colstart = int (col / 3) * 3
        rowstart = int (row / 3) * 3
        #print "rowstart, colstart", rowstart, colstart
        for r in range (rowstart, rowstart + 3) :
            for c in range (colstart, colstart + 3) :
                if  (   r != row and c != col
                    and self.puzzle [r][c] == self.puzzle [row][col]
                    ) :
                    #print "rxc No: %d,%d" % (r, c)
                    return False
        #print
        return True
    # end def is_ok

    def solve (self) :
        self._solve (Alternatives (self.puzzle))
        if self.verbose :
            print "No (more) solutions"
    # end def solve

    def _solve (self, alt) :
        if self.solvecount >= self.solvemax :
            return
        v = None
        for x in alt.values () :
            if not x : return # no solution
            if len (x) == 1 and not self.puzzle [x.row][x.col] or len (x) > 1 :
                v = x
                break
        if v is None :
            if self.verbose :
                print "Solved:"
                self.display ()
            self.solvecount += 1
            if self.solvecount >= self.solvemax :
                if self.verbose :
                    print "Max. solutions (%d) reached" % self.solvemax
            return
        old = self.puzzle [v.row][v.col]
        for i in v :
            nalt = alt.copy ()
            self.puzzle [v.row][v.col] = i
            nalt.update (v.row, v.col, i)
            assert (self.is_ok (v.row, v.col))
            #print v.row, v.col
            #self.display ()
            self._solve (nalt)
        self.puzzle [v.row][v.col] = old
    # end def _solve
# end class Puzzle

if __name__ == "__main__" :
    file = sys.stdin
    if len (sys.argv) > 1 :
        file = open (sys.argv [1])
    x = Puzzle  ()
    x.from_file (file)
    #x.display   ()
    x.solve     ()
