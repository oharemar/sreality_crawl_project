#!/bin/bash

# start pgsql
service postgresql start

# set password for postgres
su postgres bash -c "psql -c \"ALTER USER postgres WITH PASSWORD 'postgres';\""

# run scraping and flask server
python /web_test/src/server.py
