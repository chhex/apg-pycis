
import argparse
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.shortcuts import confirm
import os
import getpass
import configparser
import pathlib

from regex import W
import jfuturbr

class YesNoValidator(Validator): 
    def validate(self, document):
        text = document.text

        if text != "Y" and text != 'n':
            raise ValidationError(message='Please enter Y or n',cursor_position=1)

def main():
    dsc = """This script set's up a feature branch in jenkins, according to apg conventions,
from a source branch / Version

For the configuration , see the file ~/.apg_pycis/config.ini , for command line parameters , see --help

Preconditions: 
a The USER is a jenkins.apgsga.ch user
b The jenkins user needs to be able to access jenkins cli password less via ssh , see https://jenkins.apgsga.ch/cli/
c The jenkins userid is the same as the cvs.apgsga.ch user
d The cvs user has passwordless access to cvs.apgsga.ch

It has a interactive modus and a non interactive modus, see command line option --not-interactive'

With the interfactive modus, the configuration is created interactively and the execution of the corresponding functions is prompted

TODO Overview of functionality

"""

    arg_parser = argparse.ArgumentParser(description=dsc,
                                            formatter_class=argparse.RawDescriptionHelpFormatter)
    arg_parser.add_argument('--not-interactive', '-ni', dest='is_not_interactive', default=False, action='store_true',
                            help="Optional Argument, if true : non interactive mode")           
    arg_parser.add_argument('--skip-co', dest='is_skip_co',  default=False, action='store_true',
                            help="Optional Argument, if true, Cvs Checkout is skipped")
    arg_parser.add_argument('--skip-br', dest='is_skip_br',  default=False, action='store_true',
                            help="Optional Argument, if true, Cvs Branching is skipped")
    arg_parser.add_argument('--skip-pom-upd', dest='is_skip_pom_upd',  default=False, action='store_true',
                            help="Optional Argument, if true, the pom.xml of the modules is not updated")
    arg_parser.add_argument('--skip-commit', dest='is_skip_commit',  default=False, action='store_true',
                            help="Optional Argument, if true, the pom.xml of the modules is not updated")
    arg_parser.add_argument('--skip-create-jobs', dest='is_skip_create_jobs',  default=False, action='store_true',
                            help="Optional Argument, if true, the jenkins jobs are not created")
    args = arg_parser.parse_args()
    config = configparser.ConfigParser()
    here = pathlib.Path(__file__).parent.resolve()
    config_file_path, exists = jfuturbr.get_configuration()
    work_config_path = config_file_path
    print(f"Configuration %s, exists : %s" % (work_config_path,exists))
    if not exists:
        work_config_path =  os.path.join(here,"config_template.ini")
        print(f"Taking Configuration from template %s" % (work_config_path))
    config.read(work_config_path)
    interactive = not args.is_not_interactive;
    if interactive:
        session = PromptSession()
        configure(session,config)
        with open(config_file_path, "w", encoding="utf-8") as config_file:
            config.write(config_file)
            print("Configuration changes written to: %s" % config_file_path)
        answer = prompt("Do you want to confinue with processing (Y/n) : ", validator=YesNoValidator()) 
        if answer == 'n':
            print(f"Exiting programm with no further processing....")
            exit(0)
        print(f"Continueing with processing ....")
    print(f"Retrieving jobs names from source view %s with endswith filter: %s" % (config['JENKINS']['source_views'], config['JENKINS']['job_endswith_filter']))
    daos = jfuturbr.get_daos_from_view(config)
    print(f"Retrieving jobs detail from selected jobs and updating to target branch: %s" % config['CVS']['target_branch'])
    dao_details = jfuturbr.get_and_upd_job_details(daos, config)
    prompt_if_interactive_and_execute(interactive, args.is_skip_co, args,"cvs co of the selected modules" ,
        jfuturbr.co_and_branching_modules, dao_details, config)
    prompt_if_interactive_and_execute(interactive, args.is_skip_pom_upd, None,"the update of the pom.xml of the selected modules " , 
        jfuturbr.update_module_poms, dao_details, config)
    prompt_if_interactive_and_execute(interactive, args.is_skip_commit,None,f"commiting changes to cvs to branch: %s"  % config['CVS']['target_branch'] , 
        jfuturbr.commit_modules, dao_details, config)
    prompt_if_interactive_and_execute(interactive, args.is_skip_create_jobs,None,f"create new Jenkins Jobs for Branch and Version: %s " % config['CVS']['target_branch'], 
        jfuturbr.create_new_jobs, dao_details, config)
    print(f"Finished.") 

def prompt_if_interactive_and_execute(interactive, cmd_arg,args, msg_text, func, dao_details, config):
    is_to_do  = prompt_if_interactive(interactive,cmd_arg,msg_text)
    arg = None
    if func == jfuturbr.co_and_branching_modules:
        answer = prompt_if_interactive(interactive, not args.is_skip_br,f"After cvs co of the modules, create the branch %s " % config['CVS']['target_branch'])
        arg = not answer if interactive else answer
    execute(is_to_do,msg_text,func,arg,dao_details,config)

def prompt_if_interactive(interactive, cmd_arg, msg_text):
    print(f"Prompt if interactive: %s, cmd_arg: %s, msg_text: %s" % (interactive,cmd_arg,msg_text))
    answer = "Y"
    if cmd_arg:
        answer =  "n"
    if interactive:
       answer =  prompt(f"Continue with %s ? ('Y' or 'n') :" % msg_text,validator=YesNoValidator())    
    if answer != 'Y':
        return False
    return True

def execute(is_to_do, msg_text, func, arg,dao_details, config):
    print(f"Execute : %s, is_to_do: %s, arg: %s, msg_text: %s" % (func,is_to_do,arg,msg_text))
    what = "Confinuing with" if is_to_do else "Skipping "
    print(f"%s %s" % (what, msg_text))
    if not is_to_do:
        return
    func(dao_details, config) if arg == None else func(dao_details, arg,config)
    print(f"Done with %s." % msg_text)

def configure(session,config):
    update_config(session,config)
    if confirm_config(session,config):
        return
    configure(session,config)

def update_config(session,config):
    config['ENV']['user'] = session.prompt('User: ',  default='%s' % getpass.getuser())
    config['ENV']['local_work_dir'] = session.prompt('Work Dir:  ',  default=config['ENV']['local_work_dir'])
    config['CVS']['repository'] = session.prompt('CVS Repository: ',  default=config['CVS']['repository'])
    config['JENKINS']['source_uri'] = session.prompt('Jenkins URI: ',  default=config['JENKINS']['source_uri'])
    config['JENKINS']['target_uri']  =  config['JENKINS']['source_uri'] # Target and Source uri for the moment the same
    config['JENKINS']['port'] = session.prompt('Jenkins Cli Port: ',  default=jfuturbr.get_jenkins_port(config)) # Target and Source port for the moment the same
    config['JENKINS']['source_views'] = session.prompt('Jenkins Source View(s): ',  default=config['JENKINS']['source_views'])
    config['JENKINS']['source_job_name_prefixes'] = session.prompt('Source View(s) Job Prefix(es): ',  default=config['JENKINS']['source_job_name_prefixes'])
    config['JENKINS']['job_endswith_filter'] = session.prompt('Jenkins Jobname ends with filter(s): ', default=config['JENKINS']['job_endswith_filter'])
    config['JENKINS']['jobs_exludes'] = session.prompt('Job excludes filter: ',  default=config['JENKINS']['jobs_exludes'])
    config['JENKINS']['target_view'] = session.prompt('Target View: ',  default=config['JENKINS']['target_view'])
    config['JENKINS']['target_job_name_prefix'] = session.prompt('Target View Job Prefix: ',  default=config['JENKINS']['target_job_name_prefix'])
    config['CVS']['target_branch'] = session.prompt('Target Branch: ',   default=config['CVS']['target_branch'])
    config['MAVEN']['target_version'] = session.prompt('Maven Target Vrsion: ',   default=config['MAVEN']['target_version'])


def confirm_config(session,config):
    print("Configuration terminated.")
    print(f"Redisplaying configuration, which will be used:")
    for each_section in config.sections():
        for (each_key, each_val) in config.items(each_section):
            print(f"[%s][%s]=%s" % (each_section,each_key,each_val)) 
    answer = prompt("Is the config ok? (Y/n) : ", validator=YesNoValidator()) 
    if answer == 'n':
        print(f"Reconfiguring....")
        return False
    return True