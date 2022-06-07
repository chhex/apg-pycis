from dataclasses import dataclass
import subprocess
import os
import shutil
from bs4 import BeautifulSoup
import re


@dataclass
class JobDetail:
    job_name: str
    module_name: str
    curr_branch: str
    local_file_name: str


def check_and_create_workdir(child, config):
    dir_ = config["ENV"]["local_work_dir"]
    target_dir = os.path.join(dir_, child)
    print(target_dir)
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir, ignore_errors=False, onerror=None)
    os.makedirs(target_dir)
    return target_dir


def get_daos_from_view(config):
    jobs_names = subprocess.check_output(
        ['ssh', '-l', config["ENV"]["user"], '-p', config["JENKINS"]["port"], config['JENKINS']['target_uri'],
         'list-jobs', f"%s" % config['JENKINS']['source_views']], text=True)
    exludes = config['JENKINS']['jobs_exludes'].split()
    daos = []
    for job in jobs_names.splitlines():
        name_filter = config['JENKINS']['job_endswith_filter']
        if not name_filter or job.endswith(name_filter):
            excluded = False
            for exclude in exludes:
                if exclude in job:
                    excluded = True
                    continue
            if excluded:
                continue
            daos.append(job)
    return daos


def get_and_upd_job_details(daos, config):
    target_dir = check_and_create_workdir("jenkins", config)
    dao_details = []
    for dao in daos:
        print(f"Gathering details of job %s" % dao)
        detail = subprocess.check_output(
            ['ssh', '-l', config["ENV"]["user"], '-p', config["JENKINS"]["port"], config['JENKINS']['target_uri'],
             'get-job', f"'%s'" % dao.replace(' ', '\\ ')], text=True)
        xml = BeautifulSoup(detail, 'xml')
        hudson_cvs_repo = xml.scm.repositories.find('hudson.scm.CvsRepository')
        repo_item = hudson_cvs_repo.repositoryItems.find('hudson.scm.CvsRepositoryItem')
        cvs_module = repo_item.modules.find('hudson.scm.CvsModule')
        source_branch = repo_item.location.locationName.contents[0]
        repo_item.location.locationName.string = config['CVS']['target_branch']
        file_name = re.sub(r"\s+", "", dao) + ".xml"
        file_path = os.path.join(target_dir, file_name)
        with open(file_path, "w") as file:
            file.write(str(xml))
        job_detail = JobDetail(job_name=dao,
                               module_name=cvs_module.remoteName.contents[0],
                               curr_branch=source_branch,
                               local_file_name=file_path)
        dao_details.append(job_detail)
    return dao_details


def co_and_branching_modules(dao_details, skip_br, config):
    target_dir = check_and_create_workdir("cvs", config)
    print(f"Using work dir %s" % target_dir)
    curr_dir = os.getcwd()
    print(f"Saving current dir %s" % curr_dir)
    os.chdir(target_dir)
    print(f"Changed to dir %s" % os.getcwd())
    cvs_env = os.environ.copy()
    cvs_env["CVSROOT"] = f":ext:%s@%s:/var/local/cvs/root" % (config["ENV"]["user"], config["CVS"]["repository"])
    cvs_env["CVS_RSH"] = "ssh"
    for module in dao_details:
        print(f"!!!!! processing module: %s " % module.module_name)
        print(f"***** Current working directory %s " %  os.getcwd())
        print(f"***** Checking the out module %s " % module)
        output = subprocess.run(['cvs', 'co', '-r', module.curr_branch, module.module_name],
                        capture_output=True, text=True, env=cvs_env)
        print(output.stdout)
        if output.stderr:
            print(output.stderr)
        if skip_br:
            print("Not Branching module %s since skipping commit requested" % module)
            continue
        module_path = os.path.join(target_dir, module.module_name)
        print(f"***** Changing to directory: %s for tagging  " % module_path)
        os.chdir(module_path)
        print(f"***** cvs tag -b  %s, target branch: %s", (module.module_name, config["CVS"]["target_branch"]))
        output = subprocess.run(['cvs', 'tag', '-b', config["CVS"]["target_branch"]],
                         capture_output=True, text=True, env=cvs_env)
        print(output.stdout)
        if output.stderr:
            print(output.stderr)
        print(f"***** cvs update:  %s", (module.module_name))
        output = subprocess.run(['cvs', 'update', '-r', config["CVS"]["target_branch"]],
                        capture_output=True, text=True, env=cvs_env)
        print(output.stdout)
        if output.stderr:
            print(output.stderr)
        os.chdir(target_dir)
        print(f"!!!!! processing module: %s finished!" % module.module_name)
    os.chdir(curr_dir)


def update_module_poms(dao_details, config):
    curr_dir = os.getcwd()
    dir_ = config["ENV"]["local_work_dir"]
    cvs_path = os.path.join(dir_, "cvs")
    for module in dao_details:
        module_path = os.path.join(cvs_path, module.module_name)
        pom_path = os.path.join(module_path, "pom.xml")
        print(f"Updating %s" % pom_path)
        with open(pom_path) as f:
            pom = BeautifulSoup(f, 'xml')
        parent_version = pom.project.parent.version
        print(f"Updating parent version: %s" % str(parent_version))
        parent_version.string = config["MAVEN"]["target_version"]
        print(f"Updated parent to version: %s" % str(parent_version))
        versions = pom.project.find_all('version')
        for version in versions:
            if version.contents[0].endswith("${revision}"):
                print(f"Removing module version: %s" % str(version))
                version.decompose()
        with open(pom_path, "w") as file:
            file.write(str(pom))
    os.chdir(curr_dir)


def commit_modules(dao_details, config):
    curr_dir = os.getcwd()
    dir_ = config["CVS"]["local_work_dir"]
    cvs_path = os.path.join(dir_, "cvs")
    cvs_env = os.environ.copy()
    cvs_env["CVSROOT"] = f":ext:%s@%s:/var/local/cvs/root" % (config["ENV"]["user"], config["CVS"]["repository"])
    cvs_env["CVS_RSH"] = "ssh"
    for module in dao_details:
        module_path = os.path.join(cvs_path, module.module_name)
        os.chdir(module_path)
        subprocess.call(['cvs', 'ci', '-m', f"Updated pom.xml with new Version"], stdout=True, stderr=True, env=cvs_env)
        os.chdir(cvs_path)
    os.chdir(curr_dir)


def create_new_jobs(dao_details, config):
    for job in dao_details:
        job_name = re.sub(r"\s+", "", job.job_name)
        job_name = job_name.replace(config['JENKINS']['source_job_name_prefix'],
                                    config['JENKINS']['target_job_name_prefix'])
        print(f"Deleting Jenkins Job %s" % job_name)
        subprocess.call(['ssh', '-l', config["ENV"]["user"],
                         '-p', config["JENKINS"]["port"],
                         config['JENKINS']['target_uri'],
                         'delete-job', job_name], stdout=True, stderr=True)
        print(f"Creating Jenkins Job %s" % job_name)
        cat = subprocess.Popen(['cat', job.local_file_name], stdout=subprocess.PIPE)
        subprocess.check_output(['ssh', '-l', config["ENV"]["user"],
                                '-p', config["JENKINS"]["port"],
                                 config['JENKINS']['target_uri'],
                                 'create-job', job_name], stdin=cat.stdout)
        cat.wait()
        print(f"Adding Jenkins Job %s to view %s" % (job_name, config['JENKINS']['target_view']))
        subprocess.call(['ssh', '-l', config["ENV"]["user"],
                         '-p', config["JENKINS"]["port"],
                         config['JENKINS']['target_uri'],
                         'add-job-to-view', config['JENKINS']['target_view'], job_name], stdout=True, stderr=True)


def get_jenkins_port(config):
    cmd = "curl -Lv https://%s/login 2>&1 | grep 'X-SSH-Endpoint'" % config['JENKINS']['source_uri']
    ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = ps.communicate()[0]
    answer = output.decode("utf-8") 
    pos = answer.rfind(":")
    if pos >= 0:
        return answer[pos+1:].strip()
    return 99999

def get_configuration():  
    config_dir_path = os.path.expanduser("~/.apg_pycis")
    exists = os.path.exists(config_dir_path)
    if exists and not os.path.isdir(config_dir_path): 
        raise NotADirectoryError(config_dir_path)
    os.makedirs(config_dir_path, exist_ok=True) 
    config_file_path = os.path.join(config_dir_path, "config.ini")
    exists = os.path.exists(config_file_path)
    if (os.stat(config_file_path).st_size == 0):
        exists = False
    return config_file_path, exists
