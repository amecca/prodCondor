#!/usr/bin/env python3

from argparse import ArgumentParser
import logging
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
    ok = print_stat(times)
    if(ok != 0): return ok

    # ROOT.gROOT.SetBatch(True)
    # ok = plot_times(times)
    # if(ok != 0): return ok

    return 0


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('fname', metavar='FILE', nargs='?', help='File with elapsed times of Condor jobs. If None (default) or -, read from stdin')
    parser.add_argument('--log', dest='loglevel', metavar='LEVEL', default='WARNING', help='Level for the python logging module. Can be either a mnemonic string like DEBUG, INFO or WARNING or an integer (lower means more verbose).')

    return parser.parse_args()


def print_stat(times):
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
    for flavour, length in job_flavours.items():
        below_tot  = sum(1 if td < length else 0 for td in tdeltas)
        below_this = below_tot - last

        print('%-12s: %d (%.3g%%)' %(flavour, below_this, 100.*below_this/n_tot))
        if(below_tot == n_tot):
            break
        last  = below_tot


# def plot_times(times):
#     t_max = max(times)
#     magnitude = 10**(round(math.log10(t_max)))
#     x_max = magnitude*round(times*1.05/magnitude, 3)

#     h = ROOT.TH1F('h_times', ';time [s];# Jobs', round(sqrt(len(times)))+1, 0, x_max)
#     for t in times: _ = h.Fill(t)

#     h.Draw('hist')


def get_times(fname):
    def parse_file(handle):
        out = []
        for line in handle:
            out.append(int(line.split()[-1]))
        return out

    if(fname is None or fname == '-'):
        times = parse_file(sys.stdin)
    else:
        with open(fname) as f:
            times = parse_file(f)

    logging.info('read %d times', len(times))
    logging.debug('%s', times)
    return times


if __name__ == '__main__':
    args = parse_args()
    loglevel = args.loglevel.upper() if not args.loglevel.isdigit() else int(args.loglevel)
    logging.basicConfig(format='%(levelname)s:%(module)s:%(funcName)s: %(message)s', level=loglevel)

    exit(main(args))
