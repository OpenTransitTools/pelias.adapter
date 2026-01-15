Pelias.Adapter
==============

Python wrapper to make Pelias look like SOLR (geosearch instance)


build:
------
  1. install python 3.x, poetry and git
  1. git clone https://github.com/OpenTransitTools/pelias.adapter.git
  1. cd pelias.adapter
  1. poetry install

run:
----
  1. rm nohup.out; nohup poetry run pserve config/development.ini --reload PELIAS_SOLR=1 &
  1. http://localhost:45554/solr/select?q=2
  1. http://localhost:45554/solr/boundary/select?q=8

test:
-----
  1. run the server (see above)
  1. poetry run pytest

rules:
-----
  1. try 'autocomplete' .. if that fails, try 'search'
  1. (or should we look at length of string and try 'search' first on longer strings?)
  1. fix 'same string' problem:
      - remove duplicate points (strings 99% similar and lat/lon very close by)
      - clean up duplicate strings (e.g., Starbucks problem)
  1. call Pelias with configurable url (sources=oa,osm,transit, etc...)
  1. if we get WoF a city record(s), then strip city from query string and resubmit (e.g., bad city problem)
  1. ...

urls:
-----
  1. Pelias TriMet-only: https://ws.trimet.org/peliaswrap/v1/autocomplete?text=6
  1  Pelias Multi-Agency: https://ws.trimet.org/peliaswrap/v1/rtp/autocomplete?text=6
  1. SOLR: https://ws-st.trimet.org/solrwrap/v1/select?start=0&limit=10&wt=json&qt=dismax&rows=10&q=834%20SE&fq=type:stop
  1. SOLR Stops Only: https://ws-st.trimet.org/solrwrap/v1/select?start=0&limit=10&wt=json&qt=dismax&rows=10&q=834%20SE&fq=type:stop
