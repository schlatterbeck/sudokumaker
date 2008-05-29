PKG=sudokumaker
PY=sudoku.py maker.py __init__.py
SRC=Makefile MANIFEST.in setup.py README README.html default.css $(PY)

VERSION=Version.py
LASTRELEASE:=$(shell ../svntools/lastrelease -n)

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

README.html: README default.css
	rst2html --stylesheet=default.css $< > $@

default.css: ../../content/html/stylesheets/default.css
	cp ../../content/html/stylesheets/default.css .

%.py: %.v $(SRC)
	sed -e 's/RELEASE/$(LASTRELEASE)/' $< > $@

upload_homepage: all
	scp README.html $(USERNAME)@$(HOSTNAME):$(PROJECTDIR)/index.html
	scp default.css $(USERNAME)@$(HOSTNAME):$(PROJECTDIR)

clean:
	rm -f MANIFEST README.html default.css \
	    Version.py Version.pyc ${CHANGES} ${NOTES}
	rm -rf dist build

include ../make/Makefile-sf
