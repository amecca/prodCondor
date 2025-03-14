#!/bin/sh

set -e
set -u
set -o pipefail

show_help(){ cat <<EOF
Usage: ${0##*/} DIR [DIR...]
    Resubmit all the jobs in DIR(s), regardless of their status
EOF
}

dry_run=false
OPTIND=1
while getopts "hd" opt; do
    case $opt in
	h)
	    show_help
	    exit 0
	    ;;
	d)
	    dry_run=true
	    ;;
	\?)
	    show_help 1>&2
	    exit 1
	    ;;
    esac
done
shift "$((OPTIND-1))"

[ $# -ge 1 ] || { show_help 1>&2 ; exit 1 ; }
proddir="$@"

$dry_run && CONDOR_SUBMIT="echo condor_submit" || CONDOR_SUBMIT=condor_submit

for condorsub in $(find $proddir -type f -name condor.sub) ; do
    sampledir=$(dirname $condorsub)
    sample=${sampledir##*/}
    printf "*** %s ***\n" "$sampledir"
    (
	cd $sampledir
	$CONDOR_SUBMIT condor.sub -queue directory in $sample*
    )
done
