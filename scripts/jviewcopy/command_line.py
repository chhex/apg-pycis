
import argparse
from dataclasses import dataclass
import os
import shutil
import tempfile
from bs4 import BeautifulSoup
import jenkins
from common import run
from common import prompt_passw

@dataclass
class Module:
    name: str
    branch: str

def cvs_from_hudson(xml):
    module_locations = xml.find('moduleLocations') 
    cvs_modules = module_locations.find_all('hudson.scm.ModuleLocationImpl')
    modules = []
    for i in range(len(cvs_modules)):
        cvs_remote_name= cvs_modules[i].module.contents[0]
        branch = cvs_modules[i].branch.contents[0]
        module = Module(name=cvs_remote_name,branch=branch)
        modules.append(module)
    return modules

def cvs_from_jenkins(xml):
    hudson_cvs_repo = xml.scm.repositories.find('hudson.scm.CvsRepository') 
    repo_item = hudson_cvs_repo.repositoryItems.find('hudson.scm.CvsRepositoryItem')
    cvs_modules = repo_item.modules.find_all('hudson.scm.CvsModule')
    source_branch = repo_item.location.locationName.contents[0]
    modules = []
    for i in range(len(cvs_modules)):
        cvs_remote_name= cvs_modules[i].remoteName.contents[0]
        module = Module(name=cvs_remote_name,branch=source_branch)
        modules.append(module)
    return modules

def main():
    dsc = """This script takes the all the build Jobs from a Jenkins (JENKINS_URL) View (VIEW_NAME) and
    ,assuming that source code is CVS (CVS_URI) backed, checks the modules out in a temporary directory
    and copy the modules using rsync to a destination directory, ignoring the ide and vcs specific files / diretories
    The selection of the Jobs in the view (VIEW_HAME) can be additionally filtered (JOB_FILTER)
    The scripts runs with defaults without any additional arguments, expect for the Jenkins Password (PASSWORD)
"""

    arg_parser = argparse.ArgumentParser(description=dsc,
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument('-u','--user',  default=os.getlogin(),
                            help="Jenkins User, by default the os user")
    arg_parser.add_argument('-p', '--password', type=prompt_passw.Password, help='Jenkins user password', default=prompt_passw.Password.DEFAULT)
    arg_parser.add_argument('-j', '--jenkins_url',  help='Jenkins url', default="https://jenkins.apgsga.ch/")
    arg_parser.add_argument('-v','--view_name', help="Jenkins View name", default="Java8Mig")
    arg_parser.add_argument('-c','--cvs_uri', help="Cvs Uri", default="cvs.apgsga.ch:/var/local/cvs/root")
    arg_parser.add_argument('-d','--dest_dir', help="Destination Directory", required=True)
    arg_parser.add_argument('-f','--job_filter', help="String with contains match to filter Jenkins Jobs", default=None)
    arg_parser.add_argument('--hudson', help="Retrieve from Hudson", default=False)
    args = arg_parser.parse_args()
    # Work directory
    target_work_dir = tempfile.mkdtemp(prefix="cvscodescan-")
    os.chdir(target_work_dir)
    print(f"Running in temporary Dir: %s" % target_work_dir)
    # CVS Enviroment
    cvs_env = os.environ.copy()
    cvs_env["CVSROOT"] = f":ext:%s@%s" % (args.user,args.cvs_uri)
    cvs_env["CVS_RSH"] = "ssh"
    # File Path
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)
    # Jenkins Api 
    server = jenkins.Jenkins( args.jenkins_url, username=args.user, password=args.password.value)
    jobs = server.get_jobs(view_name=args.view_name)
    for job in jobs:
        job_name = job["name"]
        if  args.job_filter and args.job_filter not in job_name:
            continue
        job_detail = server.get_job_config(job_name)
        xml = BeautifulSoup(job_detail, 'xml')
        if 'javabuild' in args.jenkins_url:
            modules = cvs_from_hudson(xml)
        else:
            modules = cvs_from_jenkins(xml)
        for module in modules:
          print(module)
          run.run_subprocess(['cvs', '-q', 'co',  '-r', module.branch, module.name], cvs_env)
          run.run_subprocess(['rsync', '-av', f"--exclude-from=%s/rsync_excludes.txt" % dir_path, os.path.join(target_work_dir, module.name), 
              args.dest_dir], verbose=True)
    
    shutil.rmtree(target_work_dir)
    print("Done.")

