#!/usr/bin/env python

import sys
from   copy import copy

class Puzzle :
    def __init__ (self, file) :
        x = [0] * 9
        self.puzzle = [copy (x) for i in range (9)]

        for r in range (9) :
            line = file.readline ()
            for c in range (9) :
                self.puzzle [r][c] = ord (line [c]) - ord ('0')
    # end def __init__

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

    def _range (self, number) :
        if number :
            return (number,)
        return range (1, 10)
    # end def _range

    def _new_location (self, row, col) :
        newrow = row
        newcol = col + 1
        if newcol >= 9 :
            newcol = 0
            newrow = row + 1
        if newrow >= 9 :
            return None, None
        return newrow, newcol
    # end def _new_location

    def solve (self, row, col) :
        newrow, newcol = self._new_location (row, col)
        old = self.puzzle [row][col]
        for i in self._range (old) :
            self.puzzle [row][col] = i
            if self.is_ok (row, col) :
                #print row, col, newrow, newcol
                #self.display ()
                if newrow is None :
                    print "Solved:"
                    self.display ()
                    #sys.exit (0)
                else :
                    self.solve (newrow, newcol)
        self.puzzle [row][col] = old
        if col == 0 and row == 0 :
            print "No (more) solutions"
    # end def solve
# end class Puzzle

file = sys.stdin
if len (sys.argv) > 1 :
    file = open (sys.argv [1])
x = Puzzle (file)
x.display ()
x.solve   (0, 0)

