Geo-Epxertise
=============

A web app for annotating geo-expertise data.


Background
----------

Twitter users have checkins profiling their knowledge of locations. This system provide
a way to annotate such knowledge, so that a better system for retrieving them can be build
upon those annotation.


Setup
-----

Access following API endpoints for import data.
http://localhost:8080/api/import_candidates?_admin_key=xxxxxx&filename=geoexpert_experiment1.expert.csv.gz
http://localhost:8080/api/import_geoentities?_admin_key=xxxxxx&filename=topics.csv
http://localhost:8080/api/import_rankings?_admin_key=xxxxxxx&filename=geoexpert.ranking
http://localhost:8080/api/make_tasks
http://localhost:8080/api/make_taskpackages
