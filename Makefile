
.PHONY: cleanall
cleanall:
	rm -rf bin develop-eggs include lib parts .installed.cfg .mr.developer.cfg pyvenv.cfg

.PHONY: buildout
buildout:
	virtualenv -p python2 .
	bin/pip install -r requirements.txt
	bin/buildout