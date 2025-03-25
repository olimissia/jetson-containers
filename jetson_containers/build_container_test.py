#!/usr/bin/env python3
# import os
# import sys
# import copy
# import time
# import json
# import pprint
# import fnmatch
# import logging
# import traceback
# import subprocess
# import dockerhub_api 

# from .packages import validate_dict 
#,  find_package, find_packages, resolve_dependencies,  #, _PACKAGE_ROOT
# from .l4t_version import L4T_VERSION, l4t_version_from_tag, l4t_version_compatible, get_l4t_base
# from .utils import split_container_name, query_yes_no, needs_sudo, sudo_prefix
# from .logging import log_dir, log_debug, pprint_debug

# from packaging.version import Version

def validate_dict(package):
    """
    Return true if this is a package configuration dict.
    """
    if not isinstance(package, dict):
        return False
        
    for key, value in package.items():
        if key not in _PACKAGE_KEYS:
            #print(f"-- Unknown key '{key}' in package config:", value)
            return False
            
    return True

import os
import re
import sys
import json
import platform
import subprocess
import glob

from packaging.version import Version


def get_l4t_version(version_file='/etc/nv_tegra_release'):
    """
    Returns the L4T_VERSION in a packaging.version.Version object
    Which can be compared against other version objects:  https://packaging.pypa.io/en/latest/version.html
    You can also access the version components directly.  For example, on L4T R35.3.1:
    
        version.major == 35
        version.minor == 3
        version.micro == 1
        
    The L4T_VERSION will either be parsed from /etc/nv_tegra_release or the $L4T_VERSION environment variable.
    """
    if platform.machine() != 'aarch64':
        raise ValueError(f"L4T_VERSION isn't supported on {ARCH} architecture (aarch64 only)")
        
    if 'L4T_VERSION' in os.environ and len(os.environ['L4T_VERSION']) > 0:
        return Version(os.environ['L4T_VERSION'].lower().lstrip('r'))
        
    if not os.path.isfile(version_file):
        raise IOError(f"L4T_VERSION file doesn't exist:  {version_file}")
        
    with open(version_file) as file:
        line = file.readline()
        
    # R32 (release), REVISION: 7.1, GCID: 29689809, BOARD: t186ref, EABI: aarch64, DATE: Wed Feb  2 21:33:23 UTC 2022
    # R34 (release), REVISION: 1.1, GCID: 30414990, BOARD: t186ref, EABI: aarch64, DATE: Tue May 17 04:20:55 UTC 2022
    # R35 (release), REVISION: 2.1, GCID: 32398013, BOARD: t186ref, EABI: aarch64, DATE: Sun Jan 22 03:18:23 UTC 2023
    # R35 (release), REVISION: 3.1, GCID: 32790763, BOARD: t186ref, EABI: aarch64, DATE: Wed Mar 15 07:54:12 UTC 2023
    parts = [part.strip() for part in line.split(',')]

    # parse the release
    l4t_release = parts[0]
    l4t_release_prefix = '# R'
    l4t_release_suffix = ' (release)'
    
    if not l4t_release.startswith(l4t_release_prefix) or not l4t_release.endswith(l4t_release_suffix):
        raise ValueError(f"L4T release string is invalid or in unexpected format:  '{l4t_release}'")
        
    l4t_release = l4t_release[len(l4t_release_prefix):-len(l4t_release_suffix)]

    # parse the revision
    l4t_revision = parts[1]
    l4t_revision_prefix = 'REVISION: '
    
    if not l4t_revision.startswith(l4t_revision_prefix):
        raise ValueError(f"L4T revision '{l4t_revision}' doesn't start with expected prefix '{l4t_revision_prefix}'")
       
    l4t_revision = l4t_revision[len(l4t_revision_prefix):]
    
    # return packaging.version object
    return Version(f'{l4t_release}.{l4t_revision}')
    



def get_l4t_base(l4t_version=get_l4t_version()):
    """
    Returns the l4t-base or l4t-jetpack container to use
    """
    print("l4t_version is ", l4t_version)
    if l4t_version.major >= 36:   # JetPack 6
        return "ubuntu:22.04" #"nvcr.io/ea-linux4tegra/l4t-jetpack:r36.0.0"
    elif l4t_version.major >= 34: # JetPack 5
        if l4t_version >= Version('35.4.1'):
            return "nvcr.io/nvidia/l4t-jetpack:r35.4.1"
        else:
            return f"nvcr.io/nvidia/l4t-jetpack:r{l4t_version}"
    else:
        if l4t_version >= Version('32.7.1'):
            return "nvcr.io/nvidia/l4t-base:r32.7.1"
        else:
            return f"nvcr.io/nvidia/l4t-base:r{l4t_version}"
            




def build_container(name, packages, base=get_l4t_base()) : #, build_flags='', build_args=None, simulate=False, skip_tests=[], test_only=[], push='', no_github_api=False):
    """
    Multi-stage container build that chains together selected packages into one container image.
    For example, `['pytorch', 'tensorflow']` would build a container that had both pytorch and tensorflow in it.
    
    Parameters:
      name (str) -- name of container image to build (or a namespace to build under, ending in /)
                    if empty, a default name will be assigned based on the package(s) selected.           
      packages (list[str]) -- list of package names to build (into one container)
      base (str) -- base container image to use (defaults to l4t-base or l4t-jetpack)
      build_flags (str) -- arguments to add to the 'docker build' command
      simulate (bool) -- if true, just print out the commands that would have been run
      skip_tests (list[str]) -- list of tests to skip (or 'all' or 'intermediate')
      test_only (list[str]) -- only test these specified packages, skipping all other tests
      push (str) -- name of repository or user to push container to (no push if blank)
      no_github_api (bool) -- if true, use custom Dockerfile with no `ADD https://api.github.com/repos/...` line.
      
    Returns: 
      The full name of the container image that was built (as a string)
      
    """
    if isinstance(packages, str):
        packages = [packages]
    elif validate_dict(packages):
        packages = [packages['name']]

    print(f"Building container {name} with packages {packages} with base {base}")

name = 'test_container'
packages = ['pytorch', 'transformers']


build_container(name, packages) 




"""
    if len(packages) == 0:
        raise ValueError("must specify at least one package to build")    
        
    # by default these have an empty string
    if len(skip_tests) == 1 and len(skip_tests[0]) == 0:
        skip_tests = []
        
    if len(test_only) == 1 and len(test_only[0]) == 0:
        test_only = []

    # get default base container (l4t-jetpack)
    if not base:
        base = get_l4t_base()
        
    # add all dependencies to the build tree
    packages = resolve_dependencies(packages)
    print('-- Building containers ', packages)
    
    # make sure all packages can be found before building any
    for package in packages:    
        find_package(package)
            
    # assign default container repository if needed
    if len(name) == 0:   
        name = packages[-1]
    elif name.find(':') < 0 and name[-1] == '/':  # they gave a namespace to build under
        name += packages[-1]
    
    # add prefix to tag
    last_pkg = find_package(packages[-1])
    prefix = last_pkg.get('prefix', '')
    postfix = last_pkg.get('postfix', '')
    
    tag_idx = name.find(':')
    
    if prefix:
        if tag_idx >= 0:
            name = name[:tag_idx+1] + prefix + '-' + name[tag_idx+1:]
        else:
            name = name + ':' + prefix

    if postfix:
        name += f"{':' if tag_idx < 0 else '-'}{postfix}"

    # build chain of all packages
    for idx, package in enumerate(packages):
        # tag this build stage with the sub-package
        container_name = f"{name}-{package.replace(':','_')}"

        # generate the logging file (without the extension)
        log_file = os.path.join(log_dir('build'), container_name.replace('/','_')).replace(':','_')
        
        # build next intermediate container
        pkg = find_package(package)
        
        if 'dockerfile' in pkg:
            cmd = f"{sudo_prefix()}DOCKER_BUILDKIT=0 docker build --network=host --tag {container_name}" + _NEWLINE_
            if no_github_api:
                dockerfilepath = os.path.join(pkg['path'], pkg['dockerfile'])
                with open(dockerfilepath, 'r') as fp:
                    data = fp.read()
                    if 'ADD https://api.github.com' in data:
                        dockerfilepath_minus_github_api = os.path.join(pkg['path'], pkg['dockerfile'] + '.minus-github-api')
                        os.system(f"cp {dockerfilepath} {dockerfilepath_minus_github_api}")
                        os.system(f"sed 's|^ADD https://api.github.com|#[minus-github-api]ADD https://api.github.com|' -i {dockerfilepath_minus_github_api}")
                        cmd += f"--file {os.path.join(pkg['path'], pkg['dockerfile'] + '.minus-github-api')}" + _NEWLINE_
                    else:
                        cmd += f"--file {os.path.join(pkg['path'], pkg['dockerfile'])}" + _NEWLINE_
            else:
                cmd += f"--file {os.path.join(pkg['path'], pkg['dockerfile'])}" + _NEWLINE_
            cmd += f"--build-arg BASE_IMAGE={base}" + _NEWLINE_
            
            if 'build_args' in pkg:
                cmd += ''.join([f"--build-arg {key}=\"{value}\"" + _NEWLINE_ for key, value in pkg['build_args'].items()])

            if build_args:
                for key, value in build_args.items():
                    cmd += f"--build-arg {key}={value}" + _NEWLINE_ 

            if 'build_flags' in pkg:
                cmd += pkg['build_flags'] + _NEWLINE_
                
            if build_flags:
                cmd += build_flags + _NEWLINE_
                
            cmd += pkg['path'] + _NEWLINE_ #" . "
            cmd += f"2>&1 | tee {log_file + '.txt'}" + "; exit ${PIPESTATUS[0]}"  # non-tee version:  https://stackoverflow.com/a/34604684
            
            print(f"-- Building container {container_name}")
            print(f"\n{cmd}\n")

            with open(log_file + '.sh', 'w') as cmd_file:   # save the build command to a shell script for future reference
                cmd_file.write('#!/usr/bin/env bash\n\n')
                cmd_file.write(cmd + '\n')
                    
            if not simulate:  # remove the line breaks that were added for readability, and set the shell to bash so we can use $PIPESTATUS 
                status = subprocess.run(cmd.replace(_NEWLINE_, ' '), executable='/bin/bash', shell=True, check=True)  
        else:
            tag_container(base, container_name, simulate)
            
        # run tests on the intermediate container
        if package not in skip_tests and 'intermediate' not in skip_tests and 'all' not in skip_tests:
            if len(test_only) == 0 or package in test_only:
                test_container(container_name, pkg, simulate)
        
        # use this container as the next base
        base = container_name

    # tag the final container
    tag_container(container_name, name, simulate)
    
    # re-run tests on final container
    for package in packages:
        if package not in skip_tests and 'all' not in skip_tests:
            if len(test_only) == 0 or package in test_only:
                test_container(name, package, simulate)
            
    # push container
    if push:
        push_container(name, push, simulate)
     
    print(f"-- Done building container {name}")        
    return name"
"""