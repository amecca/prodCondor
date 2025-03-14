#!/usr/bin/env python3

from argparse import ArgumentParser
import logging
import os
import sys
import math
from datetime import timedelta

# import ROOT
# import cmsstyle
import numpy as np

job_flavours = {
    'espresso'    : timedelta(minutes=20),
    'microcentury': timedelta(hours=1   ),
    'longlunch'   : timedelta(hours=2   ),
    'workday'     : timedelta(hours=8   ),
    'tomorrow'    : timedelta(days=1    ),
    'testmatch'   : timedelta(days=3    ),
    'nextweek'    : timedelta(weeks=1   ),
}

def main(args):
    # Get times from file or stdin
    times = get_times(args.fname)
    if(len(times) == 0):
        logging.info('no times, ending')
        return 0

    jobs_to_info = {}
    for logfile, time in times.items():
        job = '/'.join(logfile.lstrip('./').split('/')[:3])
        time = times[logfile]
        size = get_fsize(job, sampledir=args.sampledir)
        jobs_to_info[job] = {'time': time, 'size': size}
    logging.info('Got the size of %d jobs', len(jobs_to_info))

    ok = print_stat(jobs_to_info)
    if(ok != 0): return ok

    # ROOT.gROOT.SetBatch(True)
    # ok = plot_times(times)
    # if(ok != 0): return ok

    return 0


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('fname', metavar='FILE', nargs='?', help='File with elapsed times of Condor jobs. If None (default) or -, read from stdin')
    parser.add_argument(      '--sampledir', default='samples')
    parser.add_argument('--log', dest='loglevel', metavar='LEVEL', default='WARNING', help='Level for the python logging module. Can be either a mnemonic string like DEBUG, INFO or WARNING or an integer (lower means more verbose).')

    return parser.parse_args()


def print_stat(jobs_info):
    times = [j['time'] for _, j in jobs_info.items()]
    t_min, t_max, t_mean, t_std = min(times), max(times), np.mean(times), np.std(times)
    print('[raw]   min/max/mean/std.dev: %d/%d/%.0f/%.0f' %(t_min, t_max, t_mean, t_std))
    print('[fancy] min/max/mean/std.dev: %s/%s/%s/%s'     %(
        timedelta(seconds=t_min),
        timedelta(seconds=t_max), 
        timedelta(seconds=round(t_mean)),
        timedelta(seconds=round(t_std))
    ))

    tdeltas = [timedelta(seconds=t) for t in times]
    last = 0
    n_tot = len(tdeltas)
    jobs_remaining = set(jobs_info.keys())
    for flavour, length in job_flavours.items():
        jobs_below_this = {n for n in jobs_remaining
                           if(timedelta(seconds=jobs_info[n]['time'])) < length}
        jobs_remaining -= jobs_below_this

        below_this = len(jobs_below_this)
        below_tot  = len(jobs_info) - len(jobs_remaining)

        max_size_this = max(jobs_info[n]['size'] for n in jobs_below_this)
        print('%-12s: %2d (%.3g%%) - max_size: %4.1f GB' %(flavour, below_this, 100.*below_this/n_tot, max_size_this/1e9))

        if(len(jobs_remaining) == 0):
            break

    return 0


# def plot_times(times):
#     t_max = max(times)
#     magnitude = 10**(round(math.log10(t_max)))
#     x_max = magnitude*round(times*1.05/magnitude, 3)

#     h = ROOT.TH1F('h_times', ';time [s];# Jobs', round(sqrt(len(times)))+1, 0, x_max)
#     for t in times: _ = h.Fill(t)

#     h.Draw('hist')


def get_times(fname):
    def parse_file(handle):
        out = {}
        for line in handle:
            split = line.split()
            logname = split[0].rstrip(':')
            runtime = int(split[-1])
            out[logname] = runtime
        return out

    if(fname is None or fname == '-'):
        times = parse_file(sys.stdin)
    else:
        with open(fname) as f:
            times = parse_file(f)

    logging.info('read %d times', len(times))
    # logging.debug('%s', times)
    return times


def get_fsize(jobpath, sampledir='samples'):
    # jobpath: <year>/<sample>/<chunk>
    split = jobpath.split('/')
    year = split[0]
    name = split[2]
    isData = '201' in name
    fpath = os.path.join(sampledir, 'Data' if isData else 'MC', year, name+'.root')
    logging.debug('in: %s year: %s  name: %s  isData? %s -> %s', jobpath, year, name, isData, fpath)
    if(not os.path.exists(fpath)):
        fpath = os.path.join(sampledir, year, name+'.root')
    if(not os.path.exists(fpath)):
        raise RuntimeError('Unable to find sample for job "%s"' %(jobpath))

    return os.stat(fpath).st_size


def calc_thresholds(jobs_to_info):
    pass


if __name__ == '__main__':
    args = parse_args()
    loglevel = args.loglevel.upper() if not args.loglevel.isdigit() else int(args.loglevel)
    logging.basicConfig(format='%(levelname)s:%(module)s:%(funcName)s: %(message)s', level=loglevel)

    exit(main(args))
