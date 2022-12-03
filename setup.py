#!/usr/bin/env python3
# Copyright (C) 2008-2022 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from setuptools import setup
try:
    from Version import VERSION
except:
    VERSION = None

with open ('README.rst') as f:
    description = f.read ()

license = 'GNU General Public License (GPL)'

setup \
    ( name             = "sudokumaker"
    , version          = VERSION
    , description      = "Genetic-Algorithm based Sudoku generator (and solver)"
    , long_description = description
    , license          = license
    , author           = "Ralf Schlatterbeck"
    , author_email     = "rsc@runtux.com"
    , url              = "https://github.com/schlatterbeck/sudokumaker"
    , packages         = ['sudokumaker']
    , package_dir      = { 'sudokumaker' : '' }
    , platforms        = 'Any'
    , entry_points     = dict
        ( console_scripts =
            [ 'sudokumaker=sudokumaker.maker:main'
            , 'sudoku=sudokumaker.sudoku:main'
            , 'sudoku_as_tex=sudokumaker.sudoku_as_tex:main'
            , 'sumsudoku=sudokumaker.sumsudoku:main'
            ]
        )
    , install_requires = ['pgapy', 'rsclib']
    , classifiers      = \
        [ 'Development Status :: 5 - Production/Stable'
        , 'Environment :: Console'
        , 'Intended Audience :: Developers'
        , 'Intended Audience :: Education'
        , 'Intended Audience :: End Users/Desktop'
        , 'License :: OSI Approved :: ' + license
        , 'Operating System :: OS Independent'
        , 'Programming Language :: Python'
        , 'Topic :: Education'
        , 'Topic :: Games/Entertainment :: Puzzle Games'
        ]
    )
