import os
from ml import fileTools as ft

def current_dir() : 
    return os.path.dirname(os.path.abspath(__file__))


def  generate_window_files (windowclas, parentdir) :
    h_tpmf = current_dir() + os.sep + "win_class.h"
    cpp_tpmf = current_dir() + os.sep + "win_class.cpp"

    h_c = ft.read(h_tpmf)

    cpp_c = ft.read(cpp_tpmf)

    h_c = h_c.replace("**WindowClass**", windowclas)
    cpp_c = cpp_c.replace("**WindowClass**", windowclas)

    h_file = parentdir + os.sep + windowclas + ".h"
    cpp_file = parentdir + os.sep + windowclas + ".cpp"
    
    ft.write(h_c, h_file)
    ft.write(cpp_c, cpp_file)


def  generate_app_files (appclass, parentdir) :
    clsName = appclass
    lowername = appclass.lower()

    h_tpmf = current_dir() + os.sep + "app_class.h"
    cpp_tpmf = current_dir() + os.sep + "app_class.cpp"

    h_c = ft.read(h_tpmf)
    cpp_c = ft.read(cpp_tpmf)

    h_c = h_c.replace("**ClassApp**", clsName)
    cpp_c = cpp_c.replace("**ClassApp**", clsName)

    h_c = h_c.replace("**classapp**", lowername)
    cpp_c = cpp_c.replace("**classapp**", lowername)

    h_file = parentdir + os.sep + clsName + ".h"
    cpp_file = parentdir + os.sep + clsName + ".cpp"
    
    ft.write(h_c, h_file)
    ft.write(cpp_c, cpp_file)

