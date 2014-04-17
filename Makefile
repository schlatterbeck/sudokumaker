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
PROJECTDIR=/home/groups/s/su/sudokumaker/htdocs

all: $(VERSION)

$(VERSION): $(SRC)

dist: all
	python setup.py sdist --formats=gztar,zip

clean:
	rm -f MANIFEST README.html default.css \
	    Version.py Version.pyc ${CHANGES} ${NOTES}
	rm -rf dist build

include $(RELEASETOOLS)/Makefile-sf
