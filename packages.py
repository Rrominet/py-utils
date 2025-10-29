import sys
import os
import subprocess
from ml import log

managers = {
        'apt': 'debian', 
        'apt-get': 'debian',
        'pacman': 'arch',
        'dnf': 'fedora',
        'yum': 'redhat',
        'zypper': 'suse',
        'emerge': 'gentoo',
    }

packages_map = {
        "python3" : {
            "arch" : "python",
            "gentoo" : "dev-lang/python",
            },
        "python3-pydantic" : {
            "arch" : "python-pydantic",
            "gentoo" : "dev-python/pydantic",
            },
        "python3-httpx" : {
            "arch" : "python-httpx",
            "gentoo" : "dev-python/httpx",
            },
        "python3-docstring-parser" : {
            "arch" : "python-docstring-parser",
            "gentoo" : "dev-python/docstring-parser",
            }
        }

def detect() : 
    for manager, family in managers.items() : 
        if subprocess.call(['which', manager], stdout=subprocess.DEVNULL) == 0 : 
            return manager, family
    return None, None

def installCmdFromManagers(manager): 
    cmd = ["sudo"]
    cmd += [manager]
    if (manager == "apt-get" or manager == "apt" or manager == "dnf" or manager == "yum" or manager == "zypper") :
        cmd.append("install")
        cmd.append("-y")
    elif manager == "pacman" : 
        cmd.append("-S")
        cmd.append("--nocomfirm")
    return cmd

def goodPackage(package, family) : 
    if package in packages_map : 
        if family in packages_map[package] : 
            return packages_map[package][family]
    return package

def install(packages) : 
    man_fam = detect()
    manager = man_fam[0]
    family = man_fam[1]
    if not manager :
        log.print("No package manager detected. Can't install packages.", "red")
        sys.exit(1)
    cmd = installCmdFromManagers(manager)
    if type(packages) != list :
        packages = [packages]
    for p in packages : 
        gcmd = cmd + [goodPackage(p, family)]
        re = subprocess.call(gcmd)
        if re != 0 : 
            log.print("Error while installing package " + p, "red")
            log.print ("Install it manually via your package manager or pip/yarn/npm depending of the language.\nShould be obvious.", "yellow")
