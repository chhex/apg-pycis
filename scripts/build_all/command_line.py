#!/usr/bin/env python
import argparse
import configparser
import subprocess
import os
from pathlib import Path

def remove_module_paths(modules_w_path):
    modules = []
    if len(modules_w_path) == 0:
        return modules
    for module_w_path in modules_w_path:
        module , module_path = module_w_path.split(":")
        if module not in modules:
            modules.append(module)
    return modules

def dir_path(path):
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
        if args.publish:
            process_args = ['clean ', 'deploy ']
        else:
             process_args = ['clean ', 'install ']
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
    # Options
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-path', type=dir_path, default=os.getcwd(),
                            help="Root directory of build")
    arg_parser.add_argument('-config', type=file_path, default=os.path.join(os.getcwd(),"testconfig.ini"),
                            help="Config File")
    arg_parser.add_argument('-maven', type=exe_path, default="mvn", 
                            help="Maven executable ")
    arg_parser.add_argument('--publish', action='store_true', default=False)
    arg_parser.add_argument('--skipMaven', action='store_true', default=False)
    arg_parser.add_argument('--skipGradle', action='store_true', default=False)
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
