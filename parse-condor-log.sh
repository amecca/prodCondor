#!/bin/sh

set -e
do_raw_only=true

extract_elapsed_time() {
    [ $# -eq 1 ] || return 1
    # echo $1
    start=$(grep -oP "[^\(\)]+(?= Job submitted from host)" "$1") || { echo "ERROR: could not find job start date in $1" 1>&2; exit 1; }
    finish=$(grep -oP "[^\(\)]+(?= Job terminated)" "$1")         || { echo "ERROR: could not find job end date in $1"   1>&2; exit 1; }
    printf "%d - %d\n" $(date -d "$finish" +"%s") $(date -d "$start" +"%s") | bc
}

for log in $@ ; do
    raw=$(extract_elapsed_time $log)
    if $do_raw_only ; then
	printf "%s: %d\n" "$log" $raw
    else
	fancy="$(date -d @$raw -u +'%H:%M:%Ss')"
	printf "%s: %ds (%s)\n" "$log" $raw $fancy
    fi
done
