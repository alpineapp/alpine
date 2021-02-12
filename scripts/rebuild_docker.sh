#!/bin/bash
. ./scripts/utils.sh

set_up_args() {
    print blue "ENV = $ENV"
    if [[ -z $ENV ]]
    then
        # echo -e "${GREEN}Undefined env var ENV. Should be {local, prod}"
        print red "Undefined env var ENV. Should be {local, prod}"
        exit 1
    elif [[ $ENV = local ]]
    then
        print blue "Overwriting docker-compose.yml with local config..."
        up_args="-f docker-compose.yml -f docker-compose.local.yml"
    else
        up_args="-f docker-compose.yml"
    fi
}

set_up_args
print blue "Re-building docker..."
docker-compose down
docker-compose build
docker-compose $up_args up -d
print green "Docker up!"
