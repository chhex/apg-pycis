import os
import subprocess


def run_subprocess(cmd, env =  os.environ.copy(), verbose = False):
    print("About to run command: %s with enviroment: %s" (" ".join(cmd),env ))
    output = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if verbose:
        print(output.stdout)
    if output.stderr:
        print(output.stderr)
    if output.returncode != 0:
        print("Programm Error termindated because of failing subprocess")
        exit(1)
