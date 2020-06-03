# To use this Makefile, get a copy of my SF Release Tools
# git clone git://git.code.sf.net/p/sfreleasetools/code sfreleasetools
# And point the environment variable RELEASETOOLS to the checkout

ifeq (,${RELEASETOOLS})
    RELEASETOOLS=../releasetools
endif
PKG=sudokumaker
PY=sudoku.py maker.py __init__.py
README=README.rst
SRC=Makefile MANIFEST.in setup.py $(README) README.html $(PY)

VERSIONPY=Version.py
VERSION=$(VERSIONPY)
LASTRELEASE:=$(shell $(RELEASETOOLS)/lastrelease -n)

USERNAME=schlatterbeck
PROJECT=sudokumaker
PACKAGE=${PKG}
CHANGES=changes
NOTES=notes
HOSTNAME=shell.sourceforge.net
PROJECTDIR=/home/groups/png256s/su/sudokumaker/htdocs
GSOPT=-sDEVICE=ppmraw -dBATCH -r200 -dNOPAUSE
GS=gs $(GSOPT)

all: $(VERSION)

$(VERSION): $(SRC)

dist: all
	python setup.py sdist --formats=gztar,zip

clean:
	rm -rf default.css Version.py Version.pyc ${CLEAN}

%.tex: %.sud
	sudoku_as_tex $< > $@

%.tex: %.sudd
	sudoku_as_tex --diagonal  $< > $@

%.tex: %.sudc
	sudoku_as_tex --color  $< > $@

%.tex: %.kik
	sudoku_as_tex --kikagaku $< > $@

%.ppm: %.tex
	latex $<
	dvips $$(basename $< .tex)
	$(GS) -sOutputFile=$$(basename $< .tex).ppm $$(basename $< .tex).ps

%.png: %.ppm
	pnmcut -top 750 -bottom 1580 -left 400 -right 1310 < $< | \
	pnmtopng > $@

include $(RELEASETOOLS)/Makefile-sf
