#!/usr/bin/python

import sys
import time
from   copy                import copy
from   rsclib.autosuper    import autosuper
from   rsclib.iter_recipes import combinations
from   textwrap            import dedent

class Statistics (autosuper) :
    """ Accumulated statistics by depth """
    by_depth  = {}
    formats   = \
        ( ('depth',         2)
        , ('branches',      5)
        , ('maxdepth',      2)
        , ('infer_matches', 5)
        , ('infer_stop',    5)
        )

    def __init__ (self, depth) :
        self.depth         = depth
        self.branches      = 0
        self.infer_matches = 0
        self.infer_stop    = 0
        self.maxdepth      = 0
        self.__class__.by_depth [depth] = self
    # end def __init__

    @classmethod
    def display (cls) :
        for d, s in sorted (cls.by_depth.iteritems ()) :
            print s
    # end def display

    @classmethod
    def update (cls, depth, **kw) :
        s = cls.by_depth.get (depth)
        if not s :
            return
        for k, v in kw.iteritems () :
            setattr (s, k, getattr (s, k) + v)
            if cls.cumulated :
                c = cls.cumulated
                if k != 'maxdepth' :
                    setattr (c, k, getattr (c, k) + v)
                c.maxdepth = max (c.maxdepth, depth)
        s.maxdepth = 1
    # end def update

    def __repr__ (self) :
        r = []
        for k, l in self.formats :
            r.append (('%s: %%(%s)%dd' % (k, k, l)) % self.__dict__)
        return ' '.join (r)
    # end def repr
    __str__ = __repr__

# end class Statistics

Statistics.cumulated = Statistics (-1)

class Tile (set, autosuper) :
    """ Class representing alternatives at a single tile position in a puzzle.
        This is basically a set with some additional methods and
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
        l = len (self)
        self.__super.discard (val)
        if not len (self) :
            self.parent.mark_unsolvable ()
        elif len (self) == 1 and l != 1 :
            self.parent.mark_solved (self)
    # end def discard

    def get (self) :
        """ Get only item if there is only one """
        assert (len (self) == 1)
        return tuple (self) [0]
    # end def get

    def set (self, val) :
        """ Set tile to the sole possibility val """
        if val not in self :
            self.clear ()
            self.parent.mark_unsolvable ()
        elif len (self) == 1 :
            assert (self.get () == val)
        else :
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

    def __hash__ (self) :
        return hash (self.pos)
    # end def __hash__
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
        , diagonal         = False
        , colorconstrained = False
        , depth            = 0
        ) :
        self.solvable         = True
        self.diagonal         = diagonal
        self.colorconstrained = colorconstrained
        self.depth            = depth
        self.pending          = set ()
        self.tile             = tile or {}
        if tile :
            self.solved_by_n = dict ((n, set ()) for n in range (1, 10))
            for t in self.tiles () :
                t.parent = self
                if len (t) == 1 :
                    self.solved_by_n [t.get ()].add (t.pos)
            return
        for r in range (9) :
            for c in range (9) :
                self.tile [(r, c)] = Tile (self, r, c)
        self.solved_by_n = dict ((n, set ()) for n in range (1, 10))
        if puzzle :
            for r in range (9) :
                for c in range (9) :
                    if puzzle [r][c] :
                        self.tile [(r, c)].set (puzzle [r][c])
            self.update ()
            self.infer  ()
        #print self
        #sys.stdout.flush ()
    # end def __init__

    def copy (self) :
        """ Copy constructor
        """
        tile = {}
        for k, v in self.tile.iteritems () :
            tile [k] = v.copy ()
        assert (self.solvable)
        return self.__class__ \
            ( tile = tile
            , diagonal         = self.diagonal
            , colorconstrained = self.colorconstrained
            , depth            = self.depth + 1
            )
    # end def copy

    def mark_solved (self, tile) :
        """ mark position as solved """
        self.solved_by_n [tile.get ()].add (tile.pos)
        self.pending.add (tile)
    # end def mark_solved

    def mark_unsolvable (self) :
        self.solvable = False
    # end def mark_unsolvable

    def set (self, row, col, val) :
        """ Set puzzle at position row, col to val.
            Implicitly may update list of pending changes via callback
            from tile
        """
        self.tile [(row, col)].set (val)
        self.update ()
        self.infer  ()
    # end def set

    def update (self) :
        """ Update puzzle possibilities from pending changes
        """
        if not self.solvable :
            return
        while self.pending :
            tile = self.pending.pop ()
            if not tile :
                assert (not self.solvable)
                return
            val = tile.get ()
            for itn in self.iterator_names () :
                iter  = getattr (self, itn)
                idxer = getattr (self, itn + '_idx')
                for s in iter (idxer (*tile.pos)) :
                    if s.row != tile.row or s.col != tile.col :
                        s.discard (val)
            assert (tile not in self.pending)
    # end def update

    # iterators:

    def tiles (self) :
        """ Iterate over all tiles in the puzzle """
        return sorted (self.tile.itervalues (), key = lambda x : x.key ())
    # end def tiles

    def iterator_names (self) :
        """ Yield names of all iterator methods needed for computing
            tile constraints
            >>> a = Alternatives (diagonal = True, colorconstrained = True)
            >>> for n in a.iterator_names () :
            ...     n
            'col_iter'
            'diag_bltr_iter'
            'diag_tlbr_iter'
            'quadrant_iter'
            'quadrant_pos_iter'
            'row_iter'

        """
        for n in dir (self) :
            if n.endswith ('_iter') :
                yield n
    # end def iterator_names

    def col_iter_idx (self, row, col) :
        return col
    # end def col_iter_idx

    def col_iter (self, col) :
        """ Iterate over all tiles in a given col
            >>> a   = Alternatives ()
            >>> idx = a.col_iter_idx (0, 0)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.col_iter (idx))
            '(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0)'
        """
        return (self.tile [(row, col)] for row in range (9))
    # end def col_iter
        
    def row_iter_idx (self, row, col) :
        return row
    # end def row_iter_idx

    def row_iter (self, row) :
        """ Iterate over all tiles in a given row
            >>> a   = Alternatives ()
            >>> idx = a.row_iter_idx (0, 0)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.row_iter (idx))
            '(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8)'
        """
        return (self.tile [(row, col)] for col in range (9))
    # end def row_iter

    def quadrant_iter_idx (self, row, col) :
        return (int (row / 3), int (col / 3))
    # end def quadrant_iter_idx

    def quadrant_iter (self, idx) :
        """ Iterate over all tiles in a quadrant.
            Coordinates are from one set in that quadrant.
            >>> a   = Alternatives ()
            >>> idx = a.quadrant_iter_idx (0, 0)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.quadrant_iter (idx))
            '(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)'
            >>> idx = a.quadrant_iter_idx (7, 0)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.quadrant_iter (idx))
            '(6,0),(6,1),(6,2),(7,0),(7,1),(7,2),(8,0),(8,1),(8,2)'
        """
        rowstart, colstart = (i * 3 for i in idx)
        for r in range (rowstart, rowstart + 3) :
            for c in range (colstart, colstart + 3) :
                yield self.tile [(r, c)]
    # end def quadrant_iter

    def diag_bltr_iter_idx (self, row, col) :
        """ return true if row, col is on diagonal from bottom left to
            top right
        """
        if self.diagonal and row == 8 - col :
            return True
        return None
    # end def diag_bltr_iter_idx

    def diag_bltr_iter (self, idx) :
        """ Iterate over all tiles in the diagonal from bottom left to
            top right given by row, col.
            If row, col isn't on a diagonal, iterator stops immediately.
            >>> a = Alternatives (diagonal = True)
            >>> for t in a.diag_bltr_iter (a.diag_bltr_iter_idx (0, 0)) :
            ...     t.pos
            >>> idx = a.diag_bltr_iter_idx (0, 8)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.diag_bltr_iter (idx))
            '(0,8),(1,7),(2,6),(3,5),(4,4),(5,3),(6,2),(7,1),(8,0)'
            >>> idx = a.diag_bltr_iter_idx (4, 4)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.diag_bltr_iter (idx))
            '(0,8),(1,7),(2,6),(3,5),(4,4),(5,3),(6,2),(7,1),(8,0)'
        """
        if idx :
            for r in range (9) :
                c = 8 - r
                yield self.tile [(r, c)]
    # end def diag_bltr_iter

    def diag_tlbr_iter_idx (self, row, col) :
        if self.diagonal and row == col :
            return True
        return None
    # end def diag_tlbr_iter_idx

    def diag_tlbr_iter (self, idx) :
        """ Iterate over all tiles in the diagonal from top left to
            bottom right given by row, col.
            If row, col isn't on a diagonal, iterator stops immediately.
            >>> a = Alternatives (diagonal = True)
            >>> for t in a.diag_tlbr_iter (a.diag_tlbr_iter_idx (0, 8)) :
            ...     t.pos
            >>> idx = a.diag_tlbr_iter_idx (0, 0)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.diag_tlbr_iter (idx))
            '(0,0),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8)'
            >>> idx = a.diag_tlbr_iter_idx (4, 4)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.diag_tlbr_iter (idx))
            '(0,0),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8)'
        """
        if idx :
            for r in range (9) :
                c = r
                yield self.tile [(r, c)]
    # end def diag_tlbr_iter

    def quadrant_pos_iter_idx (self, row, col) :
        if self.colorconstrained :
            return (row % 3, col % 3)
        return None
    # end def quadrant_pos_iter_idx

    def quadrant_pos_iter (self, idx) :
        """ Iterate over tiles which have the same position in their quadrant.
            Used for an additional constraint for color sudokus.
            >>> a = Alternatives (colorconstrained = True)
            >>> idx = a.quadrant_pos_iter_idx (1, 1)
            >>> idx
            (1, 1)
            >>> ','.join ('(%s,%s)' % t.pos for t in a.quadrant_pos_iter (idx))
            '(1,1),(1,4),(1,7),(4,1),(4,4),(4,7),(7,1),(7,4),(7,7)'
        """
        if idx :
            rowoffs, coloffs = idx
            for qrow in range (3) :
                for qcol in range (3) :
                    yield self.tile [(3 * qrow + rowoffs, 3 * qcol + coloffs)]
    # end def quadrant_pos_iter

    # related to solving:

    def infer (self) :
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
        if not self.solvable :
            return
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
                        if qoffs [0] == qoffs [1] or quadr [0] == quadr [1] :
                            self.solvable = False
                            Statistics.update (self.depth, infer_stop = 1)
                            return
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
                            if n in self.tile [(r, c)] :
                                found += 1
                                row = r
                                col = c
                        if not found :
                            self.tile [v [i]].clear ()
                            self.solvable = False
                            Statistics.update (self.depth, infer_stop = 1)
                            return
                        if found == 1 :
                            self.tile [(row, col)].set (n)
                        if self.pending :
                            Statistics.update (self.depth, infer_matches = 1)
                        self.update ()
                        if not self.solvable :
                            return
    # end def infer

    def invert (self, iter) :
        """ For the given iterator build set of positions by number.
            Then check by cardinality n of the set:
                - if n == 0: not solvable
                - n == 1 is uninteresting
                - 1 < n < 4: check other iterators (quadrants etc.) if
                  the items found are in same iterator (set
                  intersection). If so, remove the number from all tiles
                  in the other iterator, except for the ones in the
                  intersection.
        """
        for k in range (9) :
            numbers [k] = set ()
        for tile in iter :
            for n in tile :
                numbers [n].add (tile.pos ())

    # end def invert

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
            for t in self.row_iter (self.row_iter_idx (row, 1)) :
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

    def _solve (self, alt, depth = 0) :
        if self.solvecount >= self.solvemax :
            return
        if not alt.solvable :
            return
        v = None
        for x in alt.tiles () :
            assert (x)
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
        Statistics.update (depth, branches = len (v))
        for i in v :
            nalt = alt.copy ()
            self.puzzle [v.row][v.col] = i
            nalt.set    (v.row, v.col, i)
            #print v.row, v.col
            #self.display ()
            self._solve (nalt, depth = depth + 1)
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
        ( "-s", "--statistics"
        , dest    = "do_stats"
        , help    = "Runtime statistics"
        , action  = "store_true"
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
    if opt.do_stats :
        for d in range (81) :
            Statistics (d)
    x = Puzzle \
        ( diagonal         = opt.diagonal
        , colorconstrained = opt.colorconstrained
        , do_time          = opt.do_time
        , solvemax         = opt.solvemax
        )
    x.from_file (file)
    #x.display   ()
    x.solve     ()
    if opt.do_stats :
        Statistics.display ()
