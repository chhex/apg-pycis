import argparse
import os
def dir_path(path):
    if path == None:
        return path
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError("Not a readable directory: %s " % path)

def file_path(path):
    if os.path.isfile(path):
        return path
    else:
        raise argparse.ArgumentTypeError("Not a readable file: %s " % path)

def exe_path(path):
    if path == "mvn":
        return path
    if os.path.isfile(path) and os.access(path,os.X_OK):
        return path
    else:
        raise argparse.ArgumentTypeError("Not a executable file {0}".format(path))