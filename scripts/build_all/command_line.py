#!/usr/bin/env python
import argparse
import configparser
import subprocess
import os
from pathlib import Path
from common import validation
from common import run

class SaneFormatter(argparse.RawTextHelpFormatter, 
                    argparse.ArgumentDefaultsHelpFormatter):
    pass

def remove_module_paths(modules_w_path):
    modules = []
    for module_w_path in modules_w_path:
        if not module_w_path or module_w_path.isspace():    
            continue
        module , module_path = module_w_path.split(":")
        if module not in modules:
            modules.append(module)
    return modules


def build_maven_modules(config,args,modules,root_dir):
    alt_jdk = None
    if config.has_option("JDK","path"):
        alt_jdk = config["JDK"]["path"]
    if args.jdk:
        alt_jdk = args.jdk
    for module in modules:
        work_dir = os.path.join(root_dir, module)
        if not root_dir == work_dir:
            os.chdir(work_dir)
        process_args = []
        if alt_jdk:
            process_args.append("-Dmaven.compiler.fork=true")
            process_args.append(f"-Dmaven.compiler.executable=%s/bin/javac" % alt_jdk)
        process_args.extend(args.mvn)
        process_args_to_run = []
        if os.name == 'nt':
            # TODO : Support alternative jdk location for windows
            process_args_to_run =  ['cmd.exe', '/c', "{0} {1}".format(args.maven,'').join(process_args)]
        else:
            stripped = list(map(str.strip, process_args))
            my_env = os.environ.copy()
            if alt_jdk:
                my_env["JAVA_HOME"] = alt_jdk
            process_args_to_run.append(args.maven)
            process_args_to_run.extend(stripped)
        run.call_subprocess(cmd=process_args_to_run, env=my_env, verbose=True)
        if not root_dir == work_dir:
            os.chdir(root_dir)

def build_gradle_modules(args,modules,root_dir):
    # TODO : support alterntative Jdk locations for Gradle Builds , see Maven builds
    for module in modules:
        work_dir = os.path.join(root_dir, module)
        if not root_dir == work_dir:
            os.chdir(work_dir)
        if os.name == 'nt':
            process_args_to_run = ['cmd.exe', '/c', f"gradlew.bat %s" % ''.join(args.gradle)]
        else:
            stripped = list(map(str.strip, args.gradle))
            process_args_to_run = ['./gradlew'] + stripped
        run.call_subprocess(cmd=process_args_to_run, verbose=True)

def main():
    
    dsc = """ This script builds all modules according to a configuration file,
    located in the root directory,  default
    testconfig.ini, with a entry for Maven builds like:
    [MAVEN]
    modules =   com.affichage.common.maven.parentpom, ibus-dm-bom, ibus-dm-pom, 
                com.affichage.common.maven.dao.parentpom
    and for Gradle with the [GRADLE] key
"""

    arg_parser = argparse.ArgumentParser(description=dsc,
                                            formatter_class=SaneFormatter)
    # Options
    arg_parser.add_argument('-path', type=validation.dir_path, default=os.getcwd(),
                            help="Root directory of build")
    arg_parser.add_argument('-config', type=validation.file_path, default=os.path.join(os.getcwd(),"testconfig.ini"),
                            help="Config File")
    arg_parser.add_argument('-maven', type=validation.exe_path, default="mvn", 
                            help="Maven executable ")
    arg_parser.add_argument('-jdk', type=validation.dir_path, 
                            help="Alternative Jdk path for Maven Builds")     
    arg_parser.add_argument('-modules', nargs='+', default=None, 
                            help="Specific module(s) to build, instead of all modules")
    arg_parser.add_argument('-mvn', nargs='+', default=['clean', 'install'], 
                            help="Specific maven build arguments")
    arg_parser.add_argument('-mvnProfile',  default=None, 
                            help="Specific maven profile to build")
    arg_parser.add_argument('-gradle', nargs='+', default=['clean ', 'build ', 'publishToMavenLocal ', '-PCIBUILD', '--info ', '--stacktrace '], 
                            help="Specific gradle build arguments")                    
    arg_parser.add_argument('--skipMaven', help="Skip the maven builds", action='store_true', default=False)
    arg_parser.add_argument('--skipGradle', help="Skip the gradle builds", action='store_true', default=False)
    args = arg_parser.parse_args()
    if not Path(args.config).is_file():
        print(f"%s is not a File") % args.config
        arg_parser.print_help()
        exit(1)
    config = configparser.ConfigParser(converters={'List': lambda x: [i.strip() for i in x.split(',')]})
    config.read(args.config)
    if args.modules == None:
        to_build = config.getList('MAVEN','modules')
    else:
        to_build = args.modules
    os.chdir(args.path)
    root_dir = os.getcwd()
    # Maven Builds 
    if not args.skipMaven:
        build_maven_modules(config,args,to_build,root_dir)
    # Gradle Build 
    if not args.skipGradle:
        to_build = config.getList('GRADLE','modules')
        build_gradle_modules(args,remove_module_paths(to_build),root_dir)
