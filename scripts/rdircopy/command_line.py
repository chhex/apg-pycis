
import argparse
import os
import shutil
import tempfile
from common import run
from common import validation



def main():
    dsc = """ This script copies all subdirectories recursively from a source project directory to a target
    directory. It does the copy with rsync , with a default exclude-from file, which can be listed
    It is possible to add additional exclude-from specs 
    
    Typical usage scenaro, copy from a existing git repo to a target directory 
"""

    arg_parser = argparse.ArgumentParser(description=dsc,
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument('-s','--source_dir', type=validation.dir_path, help="Source Directory", required=True)
    arg_parser.add_argument('-d','--dest_dir', type=validation.dir_path, help="Destination Directory", required=True)
    arg_parser.add_argument('-x','--exclude', nargs='+', default=[],
                            help="rsync exclude-from specs, see also list option")
    arg_parser.add_argument('-l','--list',  action='store_true', default=False, 
                            help="List's the rsync exclude-from specs, including the with -x specified")
    args = arg_parser.parse_args()

    # Work directory
    target_work_dir = tempfile.mkdtemp(prefix="rdircopy-")
    print(f"Temporary Dir: %s" % target_work_dir)
    # File Path
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)
    target_excl_file = os.path.join(target_work_dir, "rsync_excludes.txt")
    shutil.copyfile("%s/rsync_excludes.template.txt" % dir_path, target_excl_file)
    with open(target_excl_file,"a+") as f:
        first = True
        for excl in args.exclude: 
            if first:
                f.write("# addional options, added from command_line\n")
                first = False
            f.write(f"%s\n" % excl) 
    cmd = ['rsync', '-av', f"--exclude-from=%s" % target_excl_file, args.source_dir, 
             args.dest_dir]
    if args.list:
        print("\nWould run the following rsync command:")
        print(" ".join(cmd))
        print("\nWhere the content of the --exclude-from spec is the following:\n")
        with open(target_excl_file,"r") as f:
            contents = f.read()
            print(contents)
            exit(0)


    run.run_subprocess(['rsync', '-av', f"--exclude-from=%s/rsync_excludes.txt" % target_work_dir, args.source_dir, 
             args.dest_dir], verbose=True)
    
    shutil.rmtree(target_work_dir)
    print("Done.")

