#!/usr/bin/env python
import argparse
import importlib
import sys

def do():
    dsc = """ This script is mainly for Testing purposes, for testing the various package scirpts,
    see the script directory 
"""
    arg_parser = argparse.ArgumentParser(description=dsc,
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter, add_help=False)
    arg_parser.add_argument('-p','--package',  help="Package see scripts directory ", 
        choices=['scripts.jviewscan','scripts.jviewcopy'], default='scripts.jviewscan')
    arg_parser.add_argument('--info',  help="Shows the help", action='store_true')
    args, left = arg_parser.parse_known_args()
    if args.info:
        arg_parser.print_help()
        exit(0)
    cmd = importlib.import_module(f"%s.%s" % (args.package, 'command_line'))
    sys.argv = sys.argv[:1]+left
    cmd.main()
if __name__ == "__main__":
    do()