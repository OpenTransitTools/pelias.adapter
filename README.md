Pelias.Adapter
==============

Python wrapper to make Pelias look like SOLR (geosearch instance)

build:
  1. install python 2.7, along easy_install, zc.buildout ("zc.buildout==1.5.2") and git
  1. git clone https://github.com/OpenTransitTools/pelias.adapter.git
  1. cd pelias.adapter
  1. buildout

run:
  1. rm nohup.out; nohup bin/pserve config/development.ini --reload PELIAS_SOLR=1 &
  1. http://localhost:45454/solr/select?q=2
  1. http://localhost:45454/solr/boundary/select?q=8

test:
  1. run the server (see above)
  1. bin/test
