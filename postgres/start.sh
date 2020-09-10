#!/bin/bash

docker stop postgres_db_communicator_1
mkdir -p $HOME/docker/volumes/postgres_db_communicator
docker-compose -f docker-compose.yml up --no-start
docker-compose -f docker-compose.yml start
