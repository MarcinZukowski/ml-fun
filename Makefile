define HELP
Example use:
	X=100 Y=150 IMG=Surajit.png make go
endef

.PHONY: help

help:
	${info ${HELP}}

go:
	make pic
	./ml-fun.py ${X} ${Y} ${IMG}.dat ${IMG}
#	convert -size ${X}x${Y} -depth 8 GRAY:${IMG}.out.gray z.png

pic:
	convert -geometry ${X}x${Y}! -type grayscale ${IMG} GRAY:${IMG}.dat
	convert -geometry ${X}x${Y}! -type grayscale ${IMG} ${IMG}.gray.png

clean:
	rm -f *.out.* *.gray *~ *.pyc *-pg-*.png *.csv *.gray.png *.dat
