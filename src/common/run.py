import os
import subprocess


def run_subprocess(cmd, env =  os.environ.copy(), verbose = False):
    if verbose:
        print("About to run command: %s " % (" ".join(cmd)))
    output = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if verbose:
        print(output.stdout)
    if output.stderr:
        print(output.stderr)
    if output.returncode != 0:
        print("Programm Error termindated because of failing subprocess")
        exit(1)

def call_subprocess(cmd, env =  os.environ.copy(), verbose = False):
    if verbose:
        print("About to run command: %s " % (" ".join(cmd)))
    rt = subprocess.call(cmd, env=env)
    if rt != 0:
        print("Programm Error termindated because of failing subprocess")
        exit(1)
