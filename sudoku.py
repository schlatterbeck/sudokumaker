#!/usr/bin/python

import sys
import time
from   sets                import Set
from   copy                import copy
from   rsclib.autosuper    import autosuper
from   rsclib.iter_recipes import combinations
from   textwrap            import dedent

# these are used as indeces into a pos tuple (row, col)
ROW = 0
COL = 1

class Tile (Set, autosuper) :
    """ Class representing alternatives at a single tile position in a puzzle.
        This is basically a Set with some additional methods and
        variables to remember the position in the puzzle.
    """
    def __init__ (self, parent, row, col, iterable = None) :
        if iterable is None :
            iterable = range (1, 10)
        self.__super.__init__ (iterable)
        self.parent = parent
        self.row    = row
        self.col    = col
    # end def __init__

    def key (self) :
        """ Key for sorting.
        """
        return len (self), self.row, self.col
    # end def key

    def copy (self) :
        """ Copy constructor
        """
        return self.__class__ (self.parent, self.row, self.col, self)
    # end def copy

    def discard (self, val) :
        """ Discard val from possibilities """
        self.__super.discard (val)
        if len (self) == 1 :
            self.parent.mark_solved (self)
    # end def discard

    def get (self) :
        """ Get only item if there is only one """
        assert (len (self) == 1)
        return tuple (self) [0]
    # end def get

    def set (self, val) :
        """ Set tile to the sole possibility val """
        self.clear ()
        self.add   (val)
        self.parent.mark_solved (self)
    # end def set

    @property
    def pos (self) :
        """ return position coordinates tuple """
        return (self.row, self.col)
    # end def pos

    def __repr__ (self) :
        return "Tile (row = %s, col = %s, %s)" \
            % (self.row, self.col, ''.join (sorted (str (x) for x in self)))
    # end def __repr__

    __str__ = __repr__
# end class Tile

class Alternatives :
    """ Internal representation of a puzzle.
        We store the set of possibilities for each tile position.
        The inverse structure solved_by_n stores for each number the set
        of positions where this number is the only possibility.
    """

    def __init__ \
        ( self
        , puzzle           = None
        , tile             = None
        , solvable         = True
        , diagonal         = False
        , colorconstrained = False
        ) :
        self.solvable         = solvable
        self.diagonal         = diagonal
        self.colorconstrained = colorconstrained
        self.tile             = tile or {}
        if tile :
            self.solved_by_n = dict ((n, Set ()) for n in range (1, 10))
            for t in self.tiles () :
                t.parent = self
                if len (t) == 1 :
                    self.solved_by_n [t.get ()].add (t.pos)
            return
        for r in range (9) :
            for c in range (9) :
                self.tile [(r, c)] = Tile (self, r, c)
        self.solved_by_n = dict ((n, Set ()) for n in range (1, 10))
        if puzzle :
            for r in range (9) :
                for c in range (9) :
                    if puzzle [r][c] :
                        self.update (r, c, puzzle [r][c])
            if self.solvable :
                self.infer (puzzle)
        #print self
        #sys.stdout.flush ()
    # end def __init__

    def copy (self) :
        """ Copy constructor
        """
        tile = {}
        for k, v in self.tile.iteritems () :
            tile [k] = v.copy ()
        return self.__class__ \
            ( tile = tile
            , solvable         = self.solvable
            , diagonal         = self.diagonal
            , colorconstrained = self.colorconstrained
            )
    # end def copy

    def mark_solved (self, tile) :
        """ mark position as solved """
        self.solved_by_n [tile.get ()].add (tile.pos)
    # end def mark_solved

    def update (self, row, col, val) :
        """ Update puzzle at position row, col with value val.
            After update client should determine if still solvable.
        """
        if val not in self.tile [(row, col)] :
            self.tile [(row, col)].clear ()
            self.solvable = False
            return
        tile = self.tile [(row, col)]
        tile.set (val)
        for s in self.row_iter (*tile.pos) :
            if s.row != row :
                s.discard (val)
        for s in self.col_iter (*tile.pos) :
            if s.col != col :
                s.discard (val)
        for s in self.quadrant_iter (*tile.pos) :
            if s.row != row or s.col != col :
                s.discard (val)
        if self.diagonal :
            for s in self.diagonal_iter (*tile.pos) :
                if s.row != row or s.col != col :
                    s.discard (val)
        if self.colorconstrained :
            for s in self.quadrant_position_iter (*tile.pos) :
                if s.row != row or s.col != col :
                    s.discard (val)
    # end def update

    # iterators:

    def tiles (self) :
        """ Iterate over all tiles in the puzzle """
        return sorted (self.tile.itervalues (), key = lambda x : x.key ())
    # end def tiles

    def col_iter (self, row, col) :
        """ Iterate over all tiles in a given col
            >>> a = Alternatives ()
            >>> for t in a.col_iter (0, 0) :
            ...     t.pos
            (0, 0)
            (0, 1)
            (0, 2)
            (0, 3)
            (0, 4)
            (0, 5)
            (0, 6)
            (0, 7)
            (0, 8)
        """
        return (self.tile [(row, col)] for col in range (9))
    # end def col_iter
        
    def row_iter (self, row, col) :
        """ Iterate over all tiles in a given row
            >>> a = Alternatives ()
            >>> for t in a.row_iter (0, 0) :
            ...     t.pos
            (0, 0)
            (1, 0)
            (2, 0)
            (3, 0)
            (4, 0)
            (5, 0)
            (6, 0)
            (7, 0)
            (8, 0)
        """
        return (self.tile [(row, col)] for row in range (9))
    # end def row_iter

    def quadrant_iter (self, row, col) :
        """ Iterate over all tiles in a quadrant.
            Coordinates are from one set in that quadrant.
            >>> a = Alternatives ()
            >>> for t in a.quadrant_iter (0, 0) :
            ...     t.pos
            (0, 0)
            (0, 1)
            (0, 2)
            (1, 0)
            (1, 1)
            (1, 2)
            (2, 0)
            (2, 1)
            (2, 2)
        """
        colstart = int (col / 3) * 3
        rowstart = int (row / 3) * 3
        for r in range (rowstart, rowstart + 3) :
            for c in range (colstart, colstart + 3) :
                yield self.tile [(r, c)]
    # end def quadrant_iter

    def diagonal_iter (self, row, col) :
        """ Iterate over all tiles in the diagonal given by row, col.
            If row, col isn't on a diagonal, iterator stops immediately.
            If row, col is on both diagonals, return all positions on
            diagonal. The center in that case is returned twice.
            >>> a = Alternatives ()
            >>> for t in a.diagonal_iter (1, 2) :
            ...     t.pos
            >>> for t in a.diagonal_iter (0, 0) :
            ...     t.pos
            (0, 0)
            (1, 1)
            (2, 2)
            (3, 3)
            (4, 4)
            (5, 5)
            (6, 6)
            (7, 7)
            (8, 8)
            >>> for t in a.diagonal_iter (0, 8) :
            ...     t.pos
            (0, 8)
            (1, 7)
            (2, 6)
            (3, 5)
            (4, 4)
            (5, 3)
            (6, 2)
            (7, 1)
            (8, 0)
            >>> for t in a.diagonal_iter (4, 4) :
            ...     t.pos
            (0, 0)
            (1, 1)
            (2, 2)
            (3, 3)
            (4, 4)
            (5, 5)
            (6, 6)
            (7, 7)
            (8, 8)
            (0, 8)
            (1, 7)
            (2, 6)
            (3, 5)
            (4, 4)
            (5, 3)
            (6, 2)
            (7, 1)
            (8, 0)
        """
        if row == col :
            for r in range (9) :
                c = r
                yield self.tile [(r, c)]
        if row == 8 - col :
            for r in range (9) :
                c = 8 - r
                yield self.tile [(r, c)]
    # end def diagonal_iter

    def quadrant_position_iter (self, row, col) :
        """ Iterate over tiles which have the same position in their quadrant.
            Used for an additional constraint for color sudokus.
            >>> a = Alternatives ()
            >>> for t in a.quadrant_position_iter (1, 1) :
            ...     t.pos
            (1, 1)
            (1, 4)
            (1, 7)
            (4, 1)
            (4, 4)
            (4, 7)
            (7, 1)
            (7, 4)
            (7, 7)
        """
        coloffs = col % 3
        rowoffs = row % 3
        for qrow in range (3) :
            for qcol in range (3) :
                yield self.tile [(3 * qrow + rowoffs, 3 * qcol + coloffs)]
    # end def quadrant_position_iter

    # related to solving:

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
        # FIXME: don't use puzzle
        for n, v in self.solved_by_n.iteritems () :
            for idx in (0, 1) : # by row or by column
                length = len (v)
                # sort by column or row, then row or column
                v = tuple (sorted \
                    (v, key = lambda x : (int (x [idx] / 3), x [1 - idx])))
                #print "%s sorted: %s" % (n, v)
                for i in range (length) :
                    for j in range (i + 1, min (i + 2, length)) :
                        # qbase is the quadrant row or col
                        # qoffs is the row or col in that quadrant
                        # quadr is the quadrant in the other direction
                        qbase = [int (v [k][idx    ] / 3) for k in (i, j)]
                        qoffs = [int (v [k][idx    ] % 3) for k in (i, j)]
                        quadr = [int (v [k][1 - idx] / 3) for k in (i, j)]
                        #print "idx: %s, qbase: %s, qoffs: %s, quadr: %s" % \
                        #    (idx, qbase, qoffs, quadr)
                        # not in same quadrant row / quadrant col
                        if qbase [0] != qbase [1] : continue
                        # violations: FIXME mark me invalid
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
                                if n in self.tile [(r, c)] :
                                    found += 1
                                    row = r
                                    col = c
                            elif puzzle [r][c] == n :
                                found = -1
                                break
                            #print found
                        if not found :
                            self.tile [v [i]].clear ()
                        if found == 1 :
                            self.tile [(row, col)].set (n)
    # end def infer

    def set_exclude (self) :
        """ We check the tiles in one row, column or quadrant.
            If a single number is only in one of them, we remove all
            other numbers from the Tile in that position.
            Likewise: If two numbers are only in two tiles, remove all
            other numbers from these two, and so on for three, four, ...
            We record if changes were made, so the caller can decide to
            call us again until nothing changes.
        """
        changed = False
        return changed
    # end def set_exclude

    def set_remove (self) :
        """ We check the tiles in one row, column or quadrant.
            If there are two identical tiles with cardinality 2 we remove
            the numbers in that tile from all other tiles in that entity.
            Likewise for 3, 4, ...
            Let the caller know if something changed, so we can be
            called again until reaching stable state. Probably a good
            idea to interleave calls to this method with calls to
            set_exclude.
        """
        changed = False
        return changed
    # end def set_remove

    def __repr__ (self) :
        s = ['Alternatives:']
        for row in range (9) :
            x = []
            for t in self.col_iter (row, 1) :
                x.append ('%-9s' % ''.join (str (x) for x in sorted (t)))
            s.append (' '.join (x))
        return '\n'.join (s)
    # end def __repr__

    __str__ = __repr__

# end class Alternatives

class Puzzle :
    def __init__ \
        ( self
        , verbose          = True
        , solvemax         = 100
        , do_time          = False
        , diagonal         = False
        , colorconstrained = False
        ) :
        x = [0] * 9
        self.puzzle           = [copy (x) for i in range (9)]
        self.solvecount       = 0
        self.verbose          = verbose
        self.solvemax         = solvemax
        self.do_time          = do_time
        self.diagonal         = diagonal
        self.colorconstrained = colorconstrained
        self.runtime          = 0.0
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
        """ Output as TeX code
            FIXME: might want to paint tiles when
            colorconstrained is specified.
        """
        if not author :
            author = 'Sudoku-Maker by Ralf Schlatterbeck'
        if not date :
            date = time.strftime ('%Y-%m-%d')
        print dedent \
            (   r"""
                \documentclass[12pt]{article}
                \usepackage{color}
                \date{%s}
                \author{%s}
                \title{%s}
                \begin{document}
                \maketitle
                \thispagestyle{empty}
                \Huge
                \begin{center}
                \newlength{\w}\setlength{\w}{3ex}
                \setlength{\fboxsep}{0pt}
                \begin{tabular}%%
                 {@{}|@{}p{\w}@{}|@{}p{\w}@{}|@{}p{\w}@{}|
                     |@{}p{\w}@{}|@{}p{\w}@{}|@{}p{\w}@{}|
                     |@{}p{\w}@{}|@{}p{\w}@{}|@{}p{\w}@{}|@{}}
                """ % (date, author, title)
            )
        bgcolor = diagcolor = 'white'
        if self.diagonal :
            diagcolor = 'yellow'
        for r in range (9) :
            print r"\hline"
            if r % 3 == 0 and r :
                print r"\hline"
            print '&'.join \
                ( r"\colorbox{%s}{\hbox to\w{\hfil\strut %s\hfil}}"
                % ([bgcolor, diagcolor][r == n or r == 8 - n], p or '')
                  for n, p in enumerate (self.puzzle [r])
                ),
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
        if self.do_time :
            before = time.time ()
        self._solve \
            (Alternatives 
                (self.puzzle
                , diagonal         = self.diagonal
                , colorconstrained = self.colorconstrained
                )
            )
        if self.do_time :
            self.runtime = time.time () - before
        if self.verbose :
            print "No (more) solutions"
            if self.do_time :
                print "runtime: %s" % self.runtime
    # end def solve

    def _solve (self, alt) :
        if self.solvecount >= self.solvemax :
            return
        v = None
        for x in alt.tiles () :
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
            nalt.infer  (self.puzzle)
            #print v.row, v.col
            #self.display ()
            self._solve (nalt)
        self.puzzle [v.row][v.col] = old
    # end def _solve
# end class Puzzle

if __name__ == "__main__" :
    from optparse import OptionParser
    from Version  import VERSION

    cmd = OptionParser (version = "%%prog %s" % VERSION)
    cmd.add_option \
        ( "-c", "--colorconstrained"
        , dest    = "colorconstrained"
        , help    = "Add color constraint"
        , action  = "store_true"
        )
    cmd.add_option \
        ( "-d", "--diagonal"
        , dest    = "diagonal"
        , help    = "Add diagonality constraint"
        , action  = "store_true"
        )
    cmd.add_option \
        ( "-m", "--solvemax"
        , dest    = "solvemax"
        , help    = "Maximum number of solutions printed"
        , type    = "int"
        , default = 100
        )
    cmd.add_option \
        ( "-t", "--time"
        , dest    = "do_time"
        , help    = "Runtime measurement"
        , action  = "store_true"
        )
    (opt, args) = cmd.parse_args ()
    file = sys.stdin
    if len (args) > 1 :
        cmd.error ("Only 1 argument accepted")
    elif len (args) == 1 :
        file = open (args [0])
    x = Puzzle \
        ( diagonal         = opt.diagonal
        , colorconstrained = opt.colorconstrained
        , do_time          = opt.do_time
        , solvemax         = opt.solvemax
        )
    x.from_file (file)
    #x.display   ()
    x.solve     ()
