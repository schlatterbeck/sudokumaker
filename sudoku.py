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

from   __future__ import print_function
import sys
import time
from   copy                import copy
from   rsclib.autosuper    import autosuper
from   rsclib.iter_recipes import combinations
from   textwrap            import dedent
from   operator            import and_
from   functools           import reduce

class Statistics (dict) :
    """ Accumulated statistics by depth """
    by_depth  = {}
    formats   = \
        ( ('depth',          2)
        , ('branches',       5)
        , ('maxdepth',       2)
        , ('invert_matches', 5)
        , ('invert_stop',    5)
        , ('number_sets',    2)
        )

    def __init__ (self, depth) :
        self.__class__.by_depth [depth] = self
        for k, v in self.formats :
            self [k] = 0
        self ['depth'] = depth
    # end def __init__

    @classmethod
    def display (cls, file = None) :
        if file is None :
            file = sys.stdout
        for d, s in sorted (cls.by_depth.items ()) :
            print (s, file = file)
    # end def display

    @classmethod
    def update (cls, depth, **kw) :
        s = cls.by_depth.get (depth)
        if not s :
            return
        for k, v in kw.items () :
            s [k] += v
            if cls.cumulated :
                c = cls.cumulated
                if k != 'maxdepth' :
                    c [k] += v
                c ['maxdepth'] = max (c ['maxdepth'], depth)
        s ['maxdepth'] = 1
    # end def update

    def __repr__ (self) :
        r = []
        for k, l in self.formats :
            r.append (('%s: %%(%s)%dd' % (k, k, l)) % self)
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
        elif len (self) != l :
            self.parent.mark_dirty (self)
            if len (self) == 1 and l != 1 :
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
            self.parent.mark_dirty  (self)
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
        , kikagaku         = None
        , depth            = 0
        ) :
        self.solvable         = True
        self.diagonal         = diagonal
        self.colorconstrained = colorconstrained
        self.depth            = depth
        self.kikagaku_idx     = None
        self.pending          = set ()
        self.dirty            = set ()
        self.tile             = tile or {}
        self.kikagaku         = None
        if kikagaku :
            self.init_kikagaku (kikagaku)
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
            self.invert ()
        #print (self)
        #sys.stdout.flush ()
    # end def __init__

    def copy (self) :
        """ Copy constructor
        """
        tile = {}
        for k, v in self.tile.items () :
            tile [k] = v.copy ()
        assert (self.solvable)
        return self.__class__ \
            ( tile = tile
            , diagonal         = self.diagonal
            , colorconstrained = self.colorconstrained
            , depth            = self.depth + 1
            )
    # end def copy

    def init_kikagaku (self, kikagaku) :
        self.kikagaku_color = {}
        self.kikagaku = []
        self.kikagaku_idx = []
        color_count = 0
        for r in range (9) :
            self.kikagaku_idx.append ([])
            for c in range (9) :
                self.kikagaku_idx [r].append (-1)
                color = kikagaku [r][c]
                if color not in self.kikagaku_color :
                    if color_count > 8 :
                        raise ValueError ("Too many kikagaku colors")
                    self.kikagaku_color [color] = color_count
                    color_count += 1
                    self.kikagaku.append ([])
                idx = self.kikagaku_color [color]
                self.kikagaku [idx].append ((r, c))
                self.kikagaku_idx [r][c] = idx
        if len (self.kikagaku_idx) != 9 :
            raise ValueError ("Not enough kikagaku colors")
        assert len (self.kikagaku) == 9
        for n, c in enumerate (self.kikagaku) :
            if len (c) != 9 :
                color = self.kikagaku_color [n]
                raise ValueError \
                    ("Invalid number of tiles in kikagaku color %s" % color)
    # end def init_kikagaku

    def mark_dirty (self, tile) :
        for n in self.iterator_names () :
            idx = self.indexer (n) (*tile.pos)
            if idx is not None :
                self.dirty.add ((n, idx))
    # end def mark_dirty

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
        self.invert ()
    # end def set

    def update (self) :
        """ Update puzzle possibilities from pending changes
        """
        while self.solvable and self.pending :
            tile = self.pending.pop ()
            if not tile :
                assert (not self.solvable)
                return
            val = tile.get ()
            for n in self.iterator_names () :
                for s in self.iterator (n) (self.indexer (n) (*tile.pos)) :
                    if s.row != tile.row or s.col != tile.col :
                        s.discard (val)
            assert (tile not in self.pending)
    # end def update

    # iterators:

    def tiles (self) :
        """ Iterate over all tiles in the puzzle """
        return sorted (self.tile.values (), key = lambda x : x.key ())
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
            'kikagaku_iter'
            'quadrant_iter'
            'quadrant_pos_iter'
            'row_iter'
        """
        for n in dir (self) :
            if n.endswith ('_iter') :
                yield n
    # end def iterator_names

    def iterator (self, name) :
        return getattr (self, name)
    # end def iterator

    def indexer (self, name) :
        return getattr (self, name + '_idx')
    # end def indexer

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
        if not self.kikagaku :
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
        if not self.kikagaku :
            rowstart, colstart = (i * 3 for i in idx)
            for r in range (rowstart, rowstart + 3) :
                for c in range (colstart, colstart + 3) :
                    yield self.tile [(r, c)]
    # end def quadrant_iter

    def kikagaku_iter_idx (self, row, col) :
        """ Reverse lookup of kikagaku: return the index of the color
            of this position.
        """
        if self.kikagaku_idx :
            return self.kikagaku_idx [row][col]
        return None
    # end def kikagaku_iter_idx

    def kikagaku_iter (self, idx) :
        """ Iterate over the tiles of one color of a kikagaku.
            Coordinates are explicitly stored when creating the
            kikagaku.
        """
        if self.kikagaku :
            assert 0 <= idx <= 8
            for pos in self.kikagaku [idx] :
                yield self.tile [pos]
    # end def kikagaku_iter

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

    def invert (self) :
        """ We check the tiles in one row, column or quadrant.
            If a single number is only in one of them, we remove all
            other numbers from the Tile in that position.
            Likewise: If two numbers are only in two tiles, remove all
            other numbers from these two, and so on for three, four, ...
            We record if changes were made, so the caller can decide to
            call us again until nothing changes.
            For the given iterator build set of positions by number.
            Then check by cardinality n of the set:
                - if n == 0: not solvable (number not possible)
                - if n == 1: set tile to that number
                - 2 <= n <= 4: check other iterators (quadrants etc.) if
                  the items found are in same iterator (set
                  intersection). If so, remove the number from all tiles
                  in the other iterator, except for the ones in the
                  intersection. We don't do that for n == 1, we call
                  self.update instead (which does the same)
                - iterate over 2,3,... n-1 combinations of numbers and
                  see if the union of possibilities is the same
                  cardinality as our number of combinations. If so we
                  can remove all other numbers from the tiles in the
                  union.
        """
        while self.solvable and self.dirty :
            itername, idx = self.dirty.pop ()
            numbers = {}
            for k in range (1, 10) :
                numbers [k] = set ()
            for tile in self.iterator (itername) (idx) :
                for num in tile :
                    numbers [num].add (tile)
            for n, tiles in sorted \
                (numbers.items (), key = lambda x : len (x [1])) :
                l = len (tiles)
                if not l :
                    self.solvable = False
                    Statistics.update (self.depth, invert_stop = 1)
                    return
                elif l == 1 :
                    tile = tuple (tiles) [0]
                    if len (tile) != 1 :
                        Statistics.update (self.depth, invert_matches = 1)
                    tile.set    (n)
                    self.update ()
                    continue
                elif l > 3 :
                    break
                for n2 in self.iterator_names () :
                    if n == n2 :
                        continue
                    indexer = self.indexer (n2)
                    idxs = [indexer (*t.pos) for t in tiles]
                    if not reduce \
                        (and_, (idxs [0] == i for i in idxs [1:]), True) :
                        continue
                        # FIXME, this is almost certainly wrongly indented
                        for t in self.iterator (n2) (idxs [0]) :
                            if t not in tiles :
                                tl = len (t)
                                t.discard (n)
                                if tl != len (t) :
                                    Statistics.update \
                                        (self.depth, invert_matches = 1)
            nums = [(n, s) for n, s in numbers.items () if len (s) > 1]
            for k in range (2, len (nums) - 1) :
                for numset in combinations (nums, k) :
                    ns = set ()
                    se = set ()
                    for n, s in numset :
                        ns.add (n)
                        se.update (s)
                    if len (se) <= k :
                        for tile in se :
                            for number in tile.copy () :
                                if number not in ns :
                                    tile.discard (number)
                                    Statistics.update \
                                        (self.depth, number_sets = 1)
            self.update ()
    # end def invert

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
        , kikagaku         = False
        ) :
        x = [0] * 9
        self.puzzle           = [copy (x) for i in range (9)]
        self.solvecount       = 0
        self.verbose          = verbose
        self.solvemax         = solvemax
        self.do_time          = do_time
        self.diagonal         = diagonal
        self.colorconstrained = colorconstrained
        self.kikagaku         = None
        self.runtime          = 0.0
        if kikagaku :
            self.kikagaku     = [copy (x) for i in range (9)]
    # end def __init__

    def set (self, x, y, value) :
        self.puzzle [x][y] = value
    # end def set

    def from_file (self, file) :
        for r in range (9) :
            line = file.readline ()
            for c in range (9) :
                self.puzzle [r][c] = ord (line [c]) - ord ('0')
        if self.kikagaku :
            for r in range (9) :
                line = file.readline ()
                for c in range (9) :
                    self.kikagaku [r][c] = line [c]
    # end def from_file

    def display (self, file = None) :
        if file is None :
            file = sys.stdout
        for r in range (9) :
            print \
                (''.join \
                    ([chr (self.puzzle [r][c] + ord ('0')) for c in range (9)])
                , file = file
                )
        print (file = file)
    # end def display

    def as_tex (self, date = None, title = "", author = None) :
        """ Output as TeX code
        """
        if not author :
            author = 'Sudoku-Maker by Ralf Schlatterbeck'
        if not date :
            date = time.strftime ('%Y-%m-%d')
        print \
            ( dedent
                (   r"""
                    \documentclass[12pt]{article}
                    \usepackage{xcolor}
                    """
                )
            )
        if self.colorconstrained or self.kikagaku :
            print \
                ( dedent
                    (   r"""
                        \definecolor{sred}{HTML}{FAB3BA}
                        \definecolor{sviolet}{HTML}{EDD4FF}
                        \definecolor{sgrey}{HTML}{DFDDD8}
                        \definecolor{sorange}{HTML}{F3CE82}
                        \definecolor{spink}{HTML}{F1A1DC}
                        \definecolor{syellow}{HTML}{F6FC7B}
                        \definecolor{slgreen}{HTML}{C8FBAE}
                        \definecolor{sdgreen}{HTML}{99EECD}
                        \definecolor{sblue}{HTML}{A4DFF2}
                    """
                    )
                )
            colors = [ ['sred',    'spink',   'sviolet']
                     , ['sgrey',   'sorange', 'syellow']
                     , ['slgreen', 'sdgreen', 'sblue']
                     ]
        if self.kikagaku :
            colors = dict \
                ( r = 'sred',    p = 'spink',   v = 'sviolet'
                , g = 'sgrey',   o = 'sorange', y = 'syellow'
                , l = 'slgreen', d = 'sdgreen', b = 'sblue'
                )
            kik_color = {}
            col_idx   = {}
            alt = Alternatives (self.puzzle, kikagaku = self.kikagaku)
            for c, idx in alt.kikagaku_color.items () :
                if c in colors :
                    kik_color [c] = colors [c]
                    col_idx   [colors [c]] = idx
            free = sorted ([c for c in colors.values () if c not in col_idx])
            for c, idx in alt.kikagaku_color.items () :
                if c not in kik_color :
                    kik_color [c] = free.pop ()

        print \
            ( dedent \
                (   r"""
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
            )

        bgcolor = diagcolor = 'white'
        bg = [bgcolor, bgcolor, bgcolor]
        if self.diagonal :
            diagcolor = 'yellow'
        dg = [diagcolor, diagcolor, diagcolor]
        for r in range (9) :
            print (r"\hline")
            if r % 3 == 0 and r and not self.kikagaku :
                print (r"\hline")
            if self.colorconstrained :
                bg = colors [r % 3]
                if not self.diagonal :
                    dg = colors [r % 3]
            if self.kikagaku :
                print \
                    ('&'.join \
                        ( r"\colorbox{%s}{\hbox to\w{\hfil\strut %s\hfil}}"
                        % (kik_color [self.kikagaku [r][c]], p or '')
                          for c, p in enumerate (self.puzzle [r])
                        )
                    )
            else :
                print \
                    ( '&'.join \
                        ( r"\colorbox{%s}{\hbox to\w{\hfil\strut %s\hfil}}"
                        % ( [bg [n % 3], dg [n % 3]][r == n or r == 8 - n]
                          , p or ''
                          )
                        for n, p in enumerate (self.puzzle [r])
                        )
                    , end = ' '
                    )
            print (r"\\")
        print \
            ( dedent \
                (   r"""
                    \hline
                    \end{tabular}
                    \end{center}
                    \end{document}
                    """
                )
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
                , kikagaku         = self.kikagaku
                )
            )
        if self.do_time :
            self.runtime = time.time () - before
        if self.verbose :
            print ("No (more) solutions")
            if self.do_time :
                print ("runtime: %s" % self.runtime)
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
                print ("Solved (%s):" % (self.solvecount + 1))
                self.display ()
            self.solvecount += 1
            if self.solvecount >= self.solvemax :
                if self.verbose :
                    print ("Max. solutions (%d) reached" % self.solvemax)
            return
        old = self.puzzle [v.row][v.col]
        Statistics.update (depth, branches = len (v))
        for i in v :
            nalt = alt.copy ()
            self.puzzle [v.row][v.col] = i
            nalt.set    (v.row, v.col, i)
            #print (v.row, v.col)
            #self.display ()
            self._solve (nalt, depth = depth + 1)
        self.puzzle [v.row][v.col] = old
    # end def _solve
# end class Puzzle

if __name__ == "__main__" :
    from argparse import ArgumentParser
    from Version  import VERSION

    cmd = ArgumentParser ()
    cmd.add_argument \
        ( "file"
        , help    = "Filename of sudoku file (default stdin)"
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
        , help    = "Add diagonality constraint"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-k", "--kikagaku"
        , dest    = "kikagaku"
        , help    = "Kikagaku with color areas, read additional color defs"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( "-m", "--solvemax"
        , dest    = "solvemax"
        , help    = "Maximum number of solutions printed"
        , type    = int
        , default = 100
        )
    cmd.add_argument \
        ( "-s", "--statistics"
        , dest    = "do_stats"
        , help    = "Runtime statistics"
        , action  = "store_true"
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
    file = sys.stdin
    if args.file :
        file = open (args.file)
    if args.do_stats :
        for d in range (81) :
            Statistics (d)
    x = Puzzle \
        ( diagonal         = args.diagonal
        , colorconstrained = args.colorconstrained
        , kikagaku         = args.kikagaku
        , do_time          = args.do_time
        , solvemax         = args.solvemax
        )
    x.from_file (file)
    #x.display   ()
    x.solve     ()
    if args.do_stats :
        Statistics.display ()
