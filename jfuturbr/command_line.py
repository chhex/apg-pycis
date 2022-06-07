
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
    config = configparser.ConfigParser()
    here = pathlib.Path(__file__).parent.resolve()
    config_file_path, exists = jfuturbr.get_configuration()
    work_config_path = config_file_path
    print(f"Configuration path %s, exists : %s" % (work_config_path,exists))
    if not exists:
        work_config_path =  os.path.join(here,"config_template.ini")
        print(f"Taking Configuration from template %s" % (work_config_path))
    config.read(work_config_path)
    session = PromptSession()
    configure(session,config)
    with open(config_file_path, "w", encoding="utf-8") as config_file:
        config.write(config_file)
        print("Configuration changes written to: %s" % config_file_path)
    answer = prompt("Do you want to confinue with processing (Y/n) : ", validator=YesNoValidator()) 
    if answer == 'n':
        print(f"Exiting programm with np further processing....bye, bye")
        exit(0)
    print(f"Continueing with processing ....")
    anwser = prompt("Do you want processing dry run modus (Y/n) : ", validator=YesNoValidator()) 
    dry_run = False
    if answer == 'Y':
        print(f"Running in Dry Run modus")
        dry_run = True
    print(f"Processing TODO")
    print(f"Finished.") 
    
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
    config['JENKINS']['port'] = session.prompt('Jenkins Cli Port: ',  default=jfuturbr.get_jenkins_port(config))
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