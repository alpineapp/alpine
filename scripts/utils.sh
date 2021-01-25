#!/bin/bash

# Set up color printing
# https://stackoverflow.com/a/5947802
red='\033[0;31m'
green='\033[0;32m'
blue='\033[1;34m'
nc='\033[0m' # No Color

print() {
    if [[ $1 = green ]]
    then
        printf "${green}$2${nc}\n"
    elif [[ $1 = blue ]]
    then
        printf "${blue}$2${nc}\n"
    elif [[ $1 = red ]]
    then
        printf "${red}$2${nc}\n"
    fi
}

# ---
