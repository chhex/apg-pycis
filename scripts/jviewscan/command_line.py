
import argparse
import glob
import os
import getpass
import shutil
import sys
import tempfile
from bs4 import BeautifulSoup
import jenkins
from common import run

class Password:

    DEFAULT = 'Prompt if not specified'

    def __init__(self, value):
        if value == self.DEFAULT:
            value = getpass.getpass('Jenkins password: ')
        self.value = value

    def __str__(self):
        return self.value

def scan_and_print(module_name, args, found_files):
    curr_dir = os.getcwd()
    os.chdir(f"./%s" % module_name)
    file_glob = args.file_glob
    source_filters = args.scan
    print(f"Scanning module: %s" % (module_name))
    found = []
    files_to_scan = glob.glob(file_glob, recursive=True)
    for fs in files_to_scan:    
        with open(fs) as f:
            print("Searching file: %s" % fs)
            for source_filter in source_filters:
                if source_filter in f.read():
                    print(f"File found: %s which matches %s" % (fs,source_filter))
                    found.append(f"%s" % fs)
    if len(found) > 0:
        found_files[module_name] = found
    print("**** Done")
    os.chdir(curr_dir)


def main():
    dsc = """This script takes the all the build Jobs from a Jenkins (JENKINS_URL) View (VIEW_NAME) and
    ,assuming that source code is CVS (CVS_URI) backed, checks the modules out in a temporary directory
    and scans (SCAN) and reports the code according the file glob (FILE_GLOB) an a per module basis 
    and reports found ocurrencies of the SCAN strings.  The selection of the Jobs
    in the view (VIEW_HAME) can be additionally filtered (JOB_FILTER)
    The scripts runs with defaults without any additional arguments, expect for the Jenkins Password (PASSWORD)
"""

    arg_parser = argparse.ArgumentParser(description=dsc,
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument('-u','--user',  default=os.getlogin(),
                            help="Jenkins User, by default the os user")
    arg_parser.add_argument('-p', '--password', type=Password, help='Jenkins user password', default=Password.DEFAULT)
    arg_parser.add_argument('-j', '--jenkins_url',  help='Jenkins url', default="https://jenkins.apgsga.ch/")
    arg_parser.add_argument('-v','--view_name', help="Jenkins View name", default="Java8Mig")
    arg_parser.add_argument('-c','--cvs_uri', help="Cvs Uri", default="cvs.apgsga.ch:/var/local/cvs/root")
    arg_parser.add_argument('-g','--file_glob', help="Globs of Files to be scanned", default="**/*.java")
    arg_parser.add_argument('-s','--scan', help="Regex for with is to be scanned", nargs='+', default=["java.text.SimpleDateFormat"])
    arg_parser.add_argument('-f','--job_filter', help="String with contains match to filter Jenkins Jobs", default=None)
    args = arg_parser.parse_args()
    # Work directory
    target_work_dir = tempfile.mkdtemp(prefix="cvscodescan-")
    os.chdir(target_work_dir)
    print(f"Running in temporary Dir: %s" % target_work_dir)
    # CVS Enviroment
    cvs_env = os.environ.copy()
    cvs_env["CVSROOT"] = f":ext:%s@%s" % (args.user,args.cvs_uri)
    cvs_env["CVS_RSH"] = "ssh"
    # Jenkins Api 
    server = jenkins.Jenkins( args.jenkins_url, username=args.user, password=args.password.value)
    jobs = server.get_jobs(view_name=args.view_name)
    found_files = {}
    for job in jobs:
        job_name = job["name"]
        if  args.job_filter and args.job_filter not in job_name:
            continue
        job_detail = server.get_job_config(job_name)
        xml = BeautifulSoup(job_detail, 'xml')
        hudson_cvs_repo = xml.scm.repositories.find('hudson.scm.CvsRepository') 
        repo_item = hudson_cvs_repo.repositoryItems.find('hudson.scm.CvsRepositoryItem')
        cvs_modules = repo_item.modules.find_all('hudson.scm.CvsModule')
        source_branch = repo_item.location.locationName.contents[0]
        for i in range(len(cvs_modules)):
            cvs_remote_name= cvs_modules[i].remoteName.contents[0]
            run.run_subprocess(['cvs', '-q', 'co',  '-r', source_branch, cvs_remote_name], cvs_env)
            scan_and_print(cvs_remote_name,args,found_files)
    
    shutil.rmtree(target_work_dir)
    print("Running command: ")
    print(' '.join(sys.argv)) 
    print("Results: ")
    print(f"Number of modules with matches for search strings : %s with file glob: %s in Jenkins view %s: %s" % (args.scan, args.file_glob, args.view_name, len(found_files)))
    for k,v  in found_files.items():
        for file in v:
            print("Module: %s, File %s" % (k,file))
    
