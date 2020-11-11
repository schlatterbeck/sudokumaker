#!/usr/bin/python3

from argparse import ArgumentParser

def tryall (n, digitsum, mind = 1, exclude = ()) :
    """ Yield all possible combinations of n digits that sum to digitsum
    >>> list (tryall (5, 15))
    [[1, 2, 3, 4, 5]]
    >>> list (tryall (2, 17))
    [[8, 9]]
    >>> list (tryall (2, 12))
    [[3, 9], [4, 8], [5, 7]]
    >>> list (tryall (3, 18, exclude = (1, 3)))
    [[2, 7, 9], [4, 5, 9], [4, 6, 8], [5, 6, 7]]
    >>> list (tryall (4, 21, exclude = (2, 4)))
    [[1, 3, 8, 9], [1, 5, 6, 9], [1, 5, 7, 8], [3, 5, 6, 7]]
    """
    for k in range (mind, 10) :
        if k in exclude :
            continue
        if (n == 1 and k == digitsum) :
            yield [k]
        else :
            for l in tryall (n - 1, digitsum - k, k + 1, exclude = exclude) :
                yield [k] + l

def main () :
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( 'ndigits'
        , help    = 'Number of digits to sum'
        , type    = int
        )
    cmd.add_argument \
        ( 'digitsum'
        , help    = 'Sum of all digits, no number repeats'
        , type    = int
        )
    cmd.add_argument \
        ( '-x', '--exclude'
        , help    = 'Exclude solutions with these numbers'
        , type    = int
        , action  = 'append'
        , default = []
        )
    args = cmd.parse_args ()
    print (list (tryall (args.ndigits, args.digitsum, exclude = args.exclude)))
# end def main

if __name__ == '__main__' :
    main ()
