#!/bin/env python3

from __future__ import print_function
import os
import sys
import logging
from subprocess import check_call, check_output #, CalledProcessError
from argparse import ArgumentParser, ArgumentError

if(sys.version_info.major >= 3):
    _popen_extra_args = {'encoding': 'utf-8'}
else:
    _popen_extra_args = {}

FLAVOURS = ['espresso', 'microcentury', 'longlunch', 'workday', 'tomorrow', 'testmatch', 'nextweek']


def parse_args():
    parser = ArgumentParser(
        description = 'Create job folders to submit the EventAnalyzer step to HTCondor'
        , epilog='Unknown arguments will be forwarded to run.py in the batch scripts'
    )
    parser.add_argument('action' , choices=['increase', 'decrease', 'show', 'set'])
    parser.add_argument('--to', choices=FLAVOURS)
    parser.add_argument('samples', nargs='+', metavar='SAMPLE_DIR', help='sample folders containing a condor.sub file to modify')
    parser.add_argument('--log', dest='loglevel', metavar='LEVEL', default='WARNING', help='Level for the python logging module. Can be either a mnemonic string like DEBUG, INFO or WARNING or an integer (lower means more verbose).')

    args = parser.parse_args()
    if(args.action == 'set' and args.to is None):
        raise ArgumentError('With "set", a job flavour must be specified with the option "--to"')

    return args


def main(args):
    logging.debug('args: %s', args)

    ok = True
    for sample in args.samples:
        status = change_job_flavour(sample, action=args.action, to=args.to)
        ok &= (status == 0)
    return 0 if ok else 1


def change_job_flavour(sample, action='show', to=None):
    logging.debug('sample: %s', sample)

    old_flavour = get_job_flavour(sample)
    if(action == 'show'):
        print('%s: %s' %(sample, old_flavour))
        return 0
    elif(action == 'set'):
        set_job_flavour(sample, to)
    else:
        index = FLAVOURS.index(old_flavour)
        if  (action == 'increase'):
            if(index+1 >= len(FLAVOURS)):
                logging.error('sample "%s" has already the highest flavour (%s)' %(sample, old_flavour))
                return 1
            else:
                set_job_flavour(sample, FLAVOURS[index+1])
                return 0
        elif(action == 'decrease'):
            if(index == 0):
                logging.error('sample "%s" has already the lowest flavour (%s)' %(sample, old_flavour))
                return 1
            else:
                set_job_flavour(sample, FLAVOURS[index-1])
                return 0


def set_job_flavour(sample, newflavour):
    '''
    Set job flavour for all the jobs of a sample, since they share the condor.sub
    '''
    logging.info('%s: setting flavour to %s', sample, newflavour)
    condorsub = os.path.join(sample, 'condor.sub')
    cmd = ['sed', '-i', '-r', 's/(JobFlavour\s+= ")[^"]+/\\1%s/' %(newflavour), condorsub]
    logging.debug('+ %s', ' '.join("'"+w+"'" for w in cmd))
    check_call(cmd, **_popen_extra_args)


def get_job_flavour(sample):
    condorsub = os.path.join(sample, 'condor.sub')
    cmd = ['grep', 'JobFlavour', condorsub]
    line = check_output(cmd, **_popen_extra_args)
    flavour = line.split('=')[1].strip('" \n')

    return flavour


if __name__ == '__main__':
    args = parse_args()
    loglevel = args.loglevel.upper() if not args.loglevel.isdigit() else int(args.loglevel)
    logging.basicConfig(format='%(levelname)s:%(module)s:%(funcName)s: %(message)s', level=loglevel)

    exit(main(args))
