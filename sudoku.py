#!/usr/bin/env python2.4

import sys
import time
from   sets             import Set
from   copy             import copy
from   rsclib.autosuper import autosuper
from   textwrap         import dedent

class Alternative (Set, autosuper) :
    def __init__ (self, row, col, iterator = None) :
        if iterator is None :
            iterator = range (1, 10)
        self.__super.__init__ (iterator)
        self.row = row
        self.col = col
    # end def __init__

    def key (self) :
        return len (self), self.row, self.col
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
    def __init__ (self, puzzle = None, sets = None, possible = True) :
        self.possible = possible
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
                if self.possible :
                    self.infer (puzzle)
        #print self
    # end def __init__

    def __repr__ (self) :
        s = ['Alternatives:']
        for v in self.values () :
            s.append (repr (v))
        return '\n'.join (s)
    # end def __repr__

    __str__ = __repr__

    def copy (self) :
        sets = {}
        for k, v in self.sets.iteritems () :
            sets [k] = v.copy ()
        return Alternatives (sets = sets, possible = self.possible)
    # end def copy

    def update (self, row, col, val) :
        if val not in self.sets [(row, col)] :
            self.sets [(row, col)].clear ()
            self.possible = False
            return
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
        v.sort (key = lambda x : x.key ())
        return v
    # end def iterator

    def infer (self, puzzle) :
        """ We check for quadrants with same x or y coordinates if we can
            infer numbers in the third quadrant with the same x or y
            coordinate, respectively.
            If we find a unique match, we set the alternatives for this
            match to the number found. If we find a discrepancy, we mark
            one of the coordinates with the empty set.
            For determining the coordinate of the third quadrant (and of
            the second coordinate in the third quadrant) we make use of
            the fact that quadrant coordinates are in the range [0:2] --
            summing all coordinates for a quadrant always yields the sum
            of 3, so we can determine the third quadrant by subtracting
            the other two coordinates from 3.
        """
        numbers = {}
        for c in range (9) :
            for r in range (9) :
                val = puzzle [r][c]
                if not val : continue
                if val not in numbers :
                    numbers [val] = []
                numbers [val].append ((r, c))
        #print numbers
        for n, v in numbers.iteritems () :
            for idx in (0, 1) :
                length = len (v)
                v.sort (key = lambda x : (int (x [idx] / 3), x [1 - idx]))
                #print "%s sorted: %s" % (n, v)
                for i in range (length) :
                    for j in range (i + 1, min (i + 2, length)) :
                        qbase = [int (v [k][idx    ] / 3) for k in (i, j)]
                        qoffs = [int (v [k][idx    ] % 3) for k in (i, j)]
                        quadr = [int (v [k][1 - idx] / 3) for k in (i, j)]
                        #print "idx: %s, qbase: %s, qoffs: %s, quadr: %s" % \
                        #    (idx, qbase, qoffs, quadr)
                        if qbase [0] != qbase [1] : continue
                        # violations:
                        if qoffs [0] == qoffs [1] or quadr [0] == quadr [1] :
                            continue
                        #print "Found: (%s,%s):%s, (%s,%s):%s" % \
                        #    ( v[i][0], v[i][1], puzzle [v[i][0]][v[i][1]]
                        #    , v[j][0], v[j][1], puzzle [v[j][0]][v[j][1]]
                        #    )
                        qbase = qbase [0] * 3
                        qn    = qbase + 3 - qoffs [0] - qoffs [1]
                        nq    =         3 - quadr [0] - quadr [1]
                        found = 0
                        row = col = -1
                        for x in range (3) :
                            r, c = qn, 3 * nq + x
                            if idx :
                                r, c = c, r
                            #print "check: (%s,%s):%s:" % (r, c, puzzle [r][c]),
                            if not puzzle [r][c] :
                                if n in self.sets [(r, c)] :
                                    found += 1
                                    row = r
                                    col = c
                            elif puzzle [r][c] == n :
                                found = -1
                                break
                            #print found
                        if not found :
                            #print "NOT FOUND: %s" % n
                            assert v [i] not in self.sets
                            self.sets [(v [i])] = Alternative (v [0], v [1], [])
                        if found == 1 :
                            self.sets [(row, col)].clear ()
                            self.sets [(row, col)].add   (n)
    # end def infer
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

    def as_tex (self, date = None, title = "", author = None) :
        if not author :
            author = 'Sudoku-Maker by Ralf Schlatterbeck'
        if not date :
            date = time.strftime ('%Y-%m-%d')
        print dedent \
            (   r"""
                \documentclass[12pt]{article}
                \date{%s}
                \author{%s}
                \title{%s}
                \begin{document}
                \maketitle
                \thispagestyle{empty}
                \Huge
                \begin{center}
                \newlength{\w}\setlength{\w}{1.5ex}
                \begin{tabular}%%
                 {|p{\w}|p{\w}|p{\w}||p{\w}|p{\w}|p{\w}||p{\w}|p{\w}|p{\w}|}
                """ % (date, author, title)
            )
        for r in range (9) :
            print r"\hline"
            if r % 3 == 0 and r :
                print r"\hline"
            print '&'.join \
                ([r"\hfil%s\hfil" % [p, ''][not p] for p in self.puzzle [r]]),
            print r"\\"
        print dedent \
            (   r"""
                \hline
                \end{tabular}
                \end{center}
                \end{document}
                """
            )
    # end def as_tex

    def solve (self) :
        self.solvecount = 0
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
                print "Solved (%s):" % (self.solvecount + 1)
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
