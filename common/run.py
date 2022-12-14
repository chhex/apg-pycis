import os
import subprocess


def run_subprocess(cmd, env =  os.environ.copy()):
    output = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if output.stderr:
        print(output.stderr)
    if output.returncode != 0:
        print("Programm Error termindated because of failing subprocess")
        exit(1)
