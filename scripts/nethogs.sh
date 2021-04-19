#!/bin/bash

pipe=/tmp/openPipes/nethogs_pipe

trap "rm -f $pipe" EXIT

if [[ ! -p $pipe ]]; then
    mkfifo $pipe
fi
exec 3<>$pipe
nethogs -t -a >&3 2>&1

exit 0