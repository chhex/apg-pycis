#!/usr/bin/env python
import argparse
import configparser
import subprocess
import os
from pathlib import Path

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

def dir_path(path):
    if path == None:
        return path
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError("Not a readable directory: %s " % path)

def file_path(path):
    if os.path.isfile(path):
        return path
    else:
        raise argparse.ArgumentTypeError("Not a readable file: %s " % path)

def exe_path(path):
    if path == "mvn":
        return path
    if os.path.isfile(path) and os.access(path,os.X_OK):
        return path
    else:
        raise argparse.ArgumentTypeError("Not a executable file {0}".format(path))

def build_maven_modules(args,modules,root_dir):
    for module in modules:
        work_dir = os.path.join(root_dir, module)
        if not root_dir == work_dir:
            os.chdir(work_dir)
        process_args = ['clean ']
        if args.jdk:
            process_args.append(f"JAVA_HOME=%s" % args.jdk)
            process_args.append("-Dmaven.compiler.fork=true")
            process_args.append(f"-Dmaven.compiler.executable=%s/bin/javac" % args.jdk)
        if args.publish:
            process_args.append('deploy')
        else:
             process_args.append('install')
        process_args_to_run = []
        if os.name == 'nt':
            process_args_to_run =  ['cmd.exe', '/c', "{0} {1}".format(args.maven,'').join(process_args)]
        else:
            stripped = list(map(str.strip, process_args))
            process_args_to_run =  [args.maven] + stripped
        rt = subprocess.call(process_args_to_run)
        if rt != 0:
            exit(rt)
        if not root_dir == work_dir:
            os.chdir(root_dir)

def build_gradle_modules(args,modules,root_dir):
    # TODO : support alterntative Jdk locations for Gradle Builds , see Maven builds
    for module in modules:
        work_dir = os.path.join(root_dir, module)
        if not root_dir == work_dir:
            os.chdir(work_dir)
        if args.publish:
            process_args = ['clean ', 'build ', 'publishToMavenLocal ', 'publish ', '-PCIBUILD','--info ', '--stacktrace ']
        else:
            process_args = ['clean ', 'build ', 'publishToMavenLocal ', '-PCIBUILD', '--info ', '--stacktrace ']
        process_args_to_run = []
        if os.name == 'nt':
            process_args_to_run = ['cmd.exe', '/c', f"gradlew.bat %s" % ''.join(process_args)]
        else:
            stripped = list(map(str.strip, process_args))
            process_args_to_run = ['./gradlew'] + stripped
        rt = subprocess.call(process_args_to_run)
        if rt != 0:
            exit(rt)

def main():
    
    dsc = """ This script builds all modules according to a configuration file,
    located in the root directory,  default
    testconfig.ini, with entry for Maven builds for example like:
    [MAVEN]
    modules =   com.affichage.common.maven.parentpom, ibus-dm-bom, ibus-dm-pom, 
                com.affichage.common.maven.dao.parentpom
    and for Gradle with the [GRADLE] key
"""

    arg_parser = argparse.ArgumentParser(description=dsc,
                                            formatter_class=SaneFormatter)
    # Options
    arg_parser.add_argument('-path', type=dir_path, default=os.getcwd(),
                            help="Root directory of build")
    arg_parser.add_argument('-config', type=file_path, default=os.path.join(os.getcwd(),"testconfig.ini"),
                            help="Config File")
    arg_parser.add_argument('-maven', type=exe_path, default="mvn", 
                            help="Maven executable ")
    arg_parser.add_argument('-jdk', type=exe_path, 
                            help="Alternative Jdk path for Maven Builds")            
    arg_parser.add_argument('--publish', help="publish artifact to repo",action='store_true', default=False)
    arg_parser.add_argument('--skipMaven', help="Skip the maven builds", action='store_true', default=False)
    arg_parser.add_argument('--skipGradle', help="Skip the gradle builds", action='store_true', default=False)
    args = arg_parser.parse_args()
    if not Path(args.config).is_file():
        print(f"%s is not a File") % args.config
        arg_parser.print_help()
        exit(1)
    config = configparser.ConfigParser(converters={'List': lambda x: [i.strip() for i in x.split(',')]})
    config.read(args.config)
    to_build = config.getList('MAVEN','modules')
    os.chdir(args.path)
    root_dir = os.getcwd()
    # Maven Builds 
    if not args.skipMaven:
        build_maven_modules(args,to_build,root_dir)
    # Gradle Build 
    if not args.skipGradle:
        to_build = config.getList('GRADLE','modules')
        build_gradle_modules(args,remove_module_paths(to_build),root_dir)
