import argparse
import configparser
from configparser import ConfigParser

import jfuturbr

def main():
    dsc = """This script set's up a feature branch in jenkins, according to apg conventions,
from a source branch / Version

For the configuration , see the file jenkins_config.ini , for command line parameters , see --help

Preconditions: 
a The USER is a jenkins.apgsga.ch user
b The jenkins user needs to be able to access jenkins cli password less via ssh , see https://jenkins.apgsga.ch/cli/
c The jenkins userid is the same as the cvs.apgsga.ch user
d The cvs user has passwordless access to cvs.apgsga.ch
e The jenkins cli PORT must be deterined: 
curl -Lv https://jenkins.apgsga.ch/login 2>&1 | grep 'X-SSH-Endpoint

"""
    
    arg_parser = argparse.ArgumentParser(description=dsc,
                                            formatter_class=argparse.RawDescriptionHelpFormatter)
    arg_parser.add_argument('--user', '-u', action='store', required=True,
                            help="User, with which Jenkins jobs will be started, optional, depends on --location")
    arg_parser.add_argument('--port', '-p', action='store', required=True,
                            help="Port for the Jenkins cli")
    arg_parser.add_argument('--list', "-l", dest='is_list', action='store_true',
                            help="Optional Argument, if true, the current config is listed only")
    arg_parser.add_argument('--dry', dest='is_dry_run', action='store_true',
                            help="Optional Argument, if true, the cvs changes are not commited and the jenkins jobs "
                                    "not uploaded")
    arg_parser.add_argument('--skip-co', dest='is_skip_co', action='store_true',
                            help="Optional Argument, if true, Cvs Checkout is skipped")
    arg_parser.add_argument('--skip-pom-upd', dest='is_skip_pom_upd', action='store_true',
                            help="Optional Argument, if true, the pom.xml of the modules is not updated")
    arg_parser.add_argument('--skip-commit', dest='is_skip_commit', action='store_true',
                            help="Optional Argument, if true, the pom.xml of the modules is not updated")
    args = arg_parser.parse_args()
    config: ConfigParser = configparser.ConfigParser()
    config.read("./data/jenkins_config.ini")
    if args.is_list:
        with open('./data/jenkins_config.ini', 'r') as f:
            print(f.read())
        exit
        
    print(f"Retrieving jobs names from source view"
            f" %s with endswith filter: %s" %
            (config['JENKINS']['source_view'],
            config['JENKINS']['job_endswith_filter']))
    daos = jfuturbr.get_daos_from_view(args, config)
    print(f"Retrieving jobs detail from selected jobs "
            f"and updating to target branch: %s" %
            config['CVS']['target_branch'])
    dao_details = jfuturbr.get_and_upd_job_details(daos, args, config)
    print(f"Checking out from cvs and creating target Branch %s" % config['CVS']['target_branch'])
    jfuturbr.co_and_branching_modules(dao_details, args, config)
    print(f"Updating pom.xml of selected modules "
            f"with target Revision: %s" % config['MAVEN']['target_version'])
    jfuturbr.update_module_poms(dao_details, args, config)
    print(f"Commiting changes to cvs to branch: %s "
            % config['CVS']['target_branch'])
    jfuturbr.commit_modules(dao_details, args, config)
    print(f"Creating new Jenkins for Branch and Version: %s "
            % config['CVS']['target_branch'])
    jfuturbr.create_new_jobs(dao_details, args, config)
    print(f"Done.")

if __name__ == '__main__':
    main()