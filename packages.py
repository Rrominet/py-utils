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
            },
        "g++": {
            "arch" : "gcc-c++",
            "fedora" : "gcc-c++",
            "redhat" : "gcc-c++",
            "gentoo" : "gcc-c++",
            "suse" : "gcc-c++"
            },
        "libboost-all-dev" : {
            "fedora" : "boost-devel",
            "redhat" : "boost-devel",
            "arch" : "boost",
            "suse": "boost-devel",
            "gentoo": "dev-libs/boost"
            },
        "libboost" : {
            "debian" : "libboost-all",
            "fedora" : "boost",
            "redhat" : "boost",
            "arch" : "boost",
            "suse": "libboost",
            "gentoo": "dev-libs/boost"
            },
        "make" : {
            "gentoo" : "dev-util/make",
            },
        "libc6-dev": {
                "fedora" : "glibc-devel",
                "redhat" : "glibc-devel",
                "arch" : "glibc",
                "suse" : "glibc-devel", 
                "gentoo" : "dev-libs/glibc"
                },
        "libc6": {
                "debian" : "libc6",
                "fedora" : "glibc",
                "redhat" : "glibc",
                "arch" : "glibc",
                "suse" : "glibc",
                "gentoo" : "dev-libs/glibc"
                },
        "libgtkmm-4.0-dev" : {
                "fedora" : "gtkmm4.0-devel",
                "redhat" : "gtkmm4.0-devel",
                "arch" : "gtkmm4.0",
                "suse" : "gtkmm4-devel",
                "gentoo" : "dev-cpp/gtkmm"
            },
        "libgtkmm-4.0" : {
                "debian" : "libgtkmm-4.0",
                "fedora" : "gtkmm4.0",
                "redhat" : "gtkmm4.0",
                "arch" : "gtkmm4.0",
                "suse" : "gtkmm4",
                "gentoo" : "dev-cpp/gtkmm"
            },
        "pkg-config" : {
            "fedora" : "pkgconf",
            "arch": "pkgconf",
            "gentoo": "dev-util/pkgconfig",
            },
        "libwebkitgtk-6.0-dev" : {
            "fedora" : "webkitgtk6.0-devel",
            "redhat" : "webkitgtk6.0-devel",
            "arch": "webkitgtk6.0",
            "suse": "webkitgtk6-devel",
            },
        "libwebkitgtk-6.0" : {
            "debian" : "libwebkitgtk-6.0",
            "fedora" : "webkitgtk6.0",
            "redhat" : "webkitgtk6.0",
            "arch": "webkitgtk6.0",
            "suse": "webkitgtk6",
            "gentoo": "net-libs/webkit-gtk",
            },
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
