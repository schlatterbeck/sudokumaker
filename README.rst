.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=212955&type=7
    :height: 62
    :width: 210
    :alt: SourceForge.net Logo
    :target: http://sourceforge.net/projects/sudokumaker

Sudoku Maker
============

:Author: Ralf Schlatterbeck <rsc@runtux.com>

Sudoku Maker is a generator for Sudoku number puzzles. It uses a genetic
algorithm internally, so it can serve as an introduction to genetic
algorithms. The generated Sudokus are usually very hard to solve -- good
for getting rid of a Sudoku addiction (or maybe not).

It also includes a simple depth-first solver for sudoku puzzles -- the
solver is internally needed when generating sudoku puzzles. The included
``sudoku.py`` can be called and reads a sudoku from standard input.
It outputs the solution (if any) or if there isn't a single solution to
the given puzzle it will output several (up to a maximum).

The representation of sudoku puzzles is a simple: 9 lines with 9 numbers
in each line, e.g., ::

    300000500
    000000260
    000308000
    000000091
    400100000
    037000000
    800006000
    006485700
    000009002

The numbers 1-9 represent the given numbers of the puzzle while the
zeros represent the empty tiles. A solved puzzle simply contains no
zeros.

There are two variants of sudoku puzzles supported. The first variant
adds the diagonals (so in each of the two diagonals the numbers 1-9 must
be present), this variant can be requested with the ``--diagonal``
option. The sudoku maker currently doesn't support the variants.
The second variant requires that in each quadrant there are 9 distinct
colors, the same color is always at the same position in each quadrant.
The numbers 1-9 must be present on each of the colors.

Sudoku puzzles can be pretty-printed as LaTeX using the included
``sudoku_as_tex`` program. This currently supports printing the
diagonals in yellow if the ``--diagonal`` option is given. Color
printing for the second variant of sudoku puzzles is not yet supported.

For the genetic algorithm library, my python wrapper *pgapy* of the
parallel genetic algorithm library (pgapack) is needed. There is
currently no Windows support for *pgapy* as it requires the pgapack
library to be installed. For a skilled person it should be possible to
get pgapack running on Windows, so if you're doing this, let me know.

Version 0.2: README update

The README (and the SF homepage which is generated from it) had wrong
link to the project. Also the python package index didn't accept one of
my classifier. Grmpf.

 - Fix project link in README (SF Logo)
 - Remove one classifier not accepted by pypi

Version 0.1: Initial Release

Sudoku Maker is a generator for Sudoku number puzzles. It uses a genetic
algorithm internally.

 - First Release after a long silent development
