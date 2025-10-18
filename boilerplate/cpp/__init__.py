# how to use it : 
# put //bp  behind all members that you want to generate something for.
# add letters after to explain what, here are the bindings : 
# cg : const getter, g : getter 
# s : setter 
# x : serialize and serialize
# l : consider the member as a list for the serialisation
#
# for example : 
# int _var //bp cgsxl
# 


import re
import sys
import os
from ml import fileTools as ft

pdir = os.path.dirname(__file__)
sys.path.append(pdir + "/../../")
import stringTools as st

def commentsRemoved(line) : 
    line = line.split("//")
    return line[0]

def commentsRemovedFromLines(lines) : 
    r = []
    for l in lines : 
        nl = commentsRemoved(l)
        if nl.replace(" ", "") == "" : 
            continue
        r.append(nl)
    return r

def whitespacesCleaned(line) : 
    while "\t" in line : 
        line = line.replace("\t", "")
    while "  " in line : 
        line = line.replace("  ", " ")
    while ", " in line : 
        line = line.replace(", ", ",")
    while " ," in line : 
        line = line.replace(" ,", ",")
    while "= " in line : 
        line = line.replace("= ", "=")
    while " =" in line : 
        line = line.replace(" =", "=")
    while "\n" in line : 
        line = line.replace("\n", "")
    if len(line) == 0 : 
        return ""
    if line[0] == " " : 
        line = line[1:]
    if len(line) == 0 : 
        return ""
    if line[-1] == " " : 
        line = line[:-1]
    return line

def namespaceFromLine(line) : 
    line = line.replace("namespace ", "")
    line = line.replace("class ", "")
    line = line.replace("struct ", "")
    line = line.split(":")[0]
    line = line.split("{")[0] #}
    line = whitespacesCleaned(line)
    while ("}" in line ) : 
        line = line.replace("}", "")
    return line

def listTemplate(type) : 
    chev = 0
    tpl = ""
    for i in range(len(type)) :
        if type[i] == "<" : 
            chev += 1
            continue
        elif type[i] == ">" : 
            chev -= 1
        if chev > 0 : 
            tpl += type[i]

    return tpl

def isTypeComplex(type, includeString=True) : 
    ty = type
    if "<" in ty and ">" in ty : 
        return True

    if includeString : 
        if  ("bool" in ty or 
             "int" in ty or 
             "long" in ty or 
             "char" in ty or 
             "float" in ty or 
             "double" in ty or
             "string" in ty) : 
            return False
    else : 
        if  ("bool" in ty or 
             "int" in ty or 
             "long" in ty or 
             "char" in ty or 
             "float" in ty or 
             "double" in ty) : 
            return False
    return True

#args is string representing the args between the '()'
#it will return a list of Arg instance
def getArgs(args) : 
    _r = []
    splitpos = []
    chev = 0
    brackets = 0

    for i in range(len(args)) : 
        if args[i] == "<" : 
            chev += 1
        elif args[i] == ">" : 
            chev -= 1
        elif args[i] == "{" :  # }
            brackets += 1
        elif args[i] == "}" : 
            brackets -= 1

        if chev == 0 and brackets == 0 and args[i] == "," : 
            splitpos.append(i)

    _tmp = st.splitByIndexes(args, splitpos)
    for a in _tmp : 
        _r.append(Arg(a))

    return _r

def namespace(fileContent, lineNumber) : 
    f = Function()
    f.setNamespace(fileContent, lineNumber)
    if len(f.namespaces) > 0 : 
        return f.namespaces[0]
    else : 
        return ""

class Arg : 
    # raw is the full text version of the args with no parsing.
    def __init__(self, raw="") : 
        if len(raw) >= 1 and raw[0] == "," : 
            self.raw = raw[1:]
        else : 
            self.raw = raw
        self.type = ""
        self.name=""
        self.default = ""
        if self.raw == "" : 
            return
        rest = self.setType()
        self.setNameNDefault(rest)

    #return the raw without the type
    def setType(self) : 
        i = 0
        if self.raw[0:6] == "const " : 
            i = 6

        split = 0
        chev = 0
        brackets = 0
        while i < len(self.raw) : 
            if self.raw[i] == "<" : 
                chev += 1
            elif self.raw[i] == ">" : 
                chev -= 1
            elif self.raw[i] == "{" :  # }
                brackets += 1
            elif self.raw[i] == "}" : 
                brackets -= 1
                
            if chev == 0 and brackets == 0 and self.raw[i] == " " :
                split = i 
                break
            i += 1

        splitted = st.splitByIndexes(self.raw, [split])
        self.type = splitted[0]
        if self.type[-1] == " " : 
            self.type = self.type[:-1]
        return splitted[1]

    # rest is the value returned by self.setType()
    def setNameNDefault(self, rest) : 
        if rest[0] == " " : 
            rest = rest[1:]
        tmp = rest.split("=")
        self.name = tmp[0]
        if len(tmp) > 1 : 
            self.default = tmp[1]

    def log(self) : 
        v = ""
        v += "type : " + self.type+"\n"
        v += "name : " + self.name+"\n"
        v += "default : " + self.default+"\n"
        return v

    #declaration synatx in .h files
    def declaration(self) : 
        v = ""
        v += self.type + " "
        v += self.name
        if self.default != "" : 
            v += " = " + self.default

        return v

    #implemantation syntax for the .cpp file
    def implemantation(self) : 
        v = ""
        v += self.type + " "
        v += self.name
        return v

class Function : 
    def __init__(self) : 
        self.decl = ""
        self.funcname = ""
        self.args = []
        self.returnType = ""
        self.override = False
        self.virtual = False
        self.static = False
        self.const = False # careful here do not mislead with the return value type tha tcould const too, that's not the same.
        self.namespaces = []

    def log(self) : 
        v = ""
        v += "Override : " + str(self.override) + "\n"
        v += "Static : " + str(self.static) + "\n"
        v += "Virtual : " + str(self.virtual) + "\n"
        v += "Const : " + str(self.const) + "\n"
        v += "Return Type : " + str(self.returnType) + "\n"
        v += "\n"
        v += "Args : \n"
        for a in self.args : 
            v += a.log()
        v += "--\n"
        v += "Name : " + str(self.funcname) + "\n"
        if len(self.namespaces) > 0 : 
            v += "namespace : " + self.namespaces[0] + "\n"

        print(v) 

    #static, virtual, override
    #return a version of the line with no decorators
    def setDecorators(self) : 
        if ("static " in self.decl or " static" in self.decl) : 
            self.static = True

        if ("virtual " in self.decl or " virtual" in self.decl) : 
            self.virtual = True

        if ("override " in self.decl or " override" in self.decl) : 
            self.override = True

        r = ""
        r = self.decl.replace("static", "")
        r = r.replace("virtual ", "")
        r = r.replace("override", "")
        return r

    #cleaned is the return of the nethod setDecorators (after whitespacesCleaned has been called on it)
    def setConst(self, cleaned) : 
        tmp = cleaned.split(")")
        if "const" in tmp[-1] : 
            self.const = True
        return cleaned

    #set the return type and return the line with no return type
    #should be called after setDecorators and whitespacesCleaned
    def setReturnType(self, cleaned) : 
        if cleaned[0:6] == "const " : 
            self.returnType = "const "
            cleaned = cleaned[6:]
        tmp = cleaned.split("(")
        if " " in tmp[0] : 
            cleaned = cleaned.split(" ")
            self.returnType += cleaned[0]
            self.returnType = self.returnType.replace(",", ", ")
            cleaned.pop(0)
            return " ".join(cleaned)
        else : 
            self.returnType = ""
            return cleaned

    #should be called on the setReturnType returned value
    def setName(self, cleaned) : 
        tmp = cleaned.split("(") #)
        self.funcname = tmp[0]
        return "(" + tmp[1]   #)

    #should be called on the setName returned value
    def setArgs(self, cleaned) : 
        count = 0
        args = ""
        for i in range(len(cleaned)) : 
            if cleaned[i] == "(" : #)
                count += 1
                continue
            elif cleaned[i] == ")" : 
                count -= 1

            if count == 1 : 
                args += cleaned[i]
        self.args = getArgs(args)

    def parseLine(self, line) : 
        self.decl = line
        cleaned = self.setDecorators()
        cleaned = whitespacesCleaned(cleaned)
        cleaned = self.setConst(cleaned)
        cleaned = self.setReturnType(cleaned)
        cleaned = self.setName(cleaned)
        cleaned = self.setArgs(cleaned)

    # example : 
    #const ml::Vec<std::function<void(std::string, int)>> myfunc(const object& arg1, std::string arg2 = "default")
    @staticmethod
    def fromLine(line) : 
        line = commentsRemoved(line)
        f = Function()
        f.parseLine(line)
        return f

    #the lines sould be a list or a str, if str it will be splitted by '\n'
    @staticmethod
    def fromLines(lines) : 
        if type(lines) == str : 
            lines = lines.split("\n")

        line = ""
        for l in lines : 
            line += l + " "

        return Function.fromLine(line)

    #declaration synatx in .h files
    def declaration(self) : 
        v = ""
        if self.virtual : 
            v += "virtual "
        if self.static : 
            v += "static "
        v += self.returnType + " "
        v += self.funcname + "(" #)
        for a in self.args : 
            v += a.declaration() + ","
        v = v[:-1]
        v += ")"

        if self.const : 
            v += " const"
        if self.override : 
            v += " override"
        v+= ";"
        v = v.replace("( )", "()")
        return v

    #implemantation syntax for the .cpp file
    def implemantation(self, includeNamespace=False) : 
        v = ""
        v += self.returnType + " "
        if includeNamespace and len(self.namespaces) > 0 : 
            v+= self.namespaces[-1] + "::"
        v += self.funcname + "(" #)
        for a in self.args : 
            v += a.implemantation() + ","
        v = v[:-1]
        v += ")"

        if self.const : 
            v += " const"
        v = v.replace("( )", "()")
        v += "\n{\n\t\n}\n"
        return v

    # when calling this function, the other params, specially the funcname and the args MUST be known and setted (if lineNumber == -1)
    def setNamespace(self, filecontent, lineNumber = -1) : 
        lines = filecontent.split("\n")
        brackets = 0
        namespaces = []

        for j in range(len(lines)) :
            l = lines[j]
            if "namespace " in l or "class " in l or "struct " in l:  
                ns = namespaceFromLine(l)
                namespace = {}
                namespace["name"] = ns
                namespace["index"] = brackets + 1
                namespace["open"] = True
                namespaces.append(namespace)

            for i in range(len(l)) : 
                if l[i] == "{" : #}
                    brackets += 1
                elif l[i] == "}" : 
                    if brackets == namespaces[-1]["index"] : 
                        namespaces[-1]["open"] = False
                    brackets -= 1

            if lineNumber == -1 :
                if self.returnType.replace(" ", "") in l.replace(" ", "") and self.funcname in l : 
                    same = True
                    for a in self.args : 
                        if not a.type.replace(" ", "") in l.replace(" ", "") : 
                            same = False 
                            break 
                    if same : 
                        break
            else : 
                if j + 1 == lineNumber : 
                    break

        i = len(namespaces) - 1
        self.namespaces = []
        while i > 0 : 
            if namespaces[i]["open"] : 
                self.namespaces.append(namespaces[i]["name"])
                return
            i -= 1

def functionsFromLines(lines) :
    if type(lines) == str : 
        lines = lines.split("\n")

    glines = []
    for l in lines : 
        l = commentsRemoved(l)
        l = whitespacesCleaned(l)
        if l != "" : 
            glines.append(l)

    fs = []
    for l in glines : 
        f = Function.fromLine(l)
        fs.append(f)
    return fs

def functionsImplsFromLines(lines, filepath, namespace="") : 
    fileContent = ft.read(filepath)
    fs = functionsFromLines(lines)
    _r = []

    for f in fs : 
        f.namespaces.append(namespace)
        _r.append(f.implemantation(True))
    return _r

class Attr : 
    def __init__(self) : 
        self.namespaces = []
        self.type = ""
        self.name = ""
        self.addGetter = False
        self.addSetter = False
        self.addConstGetter = False
        self.addSerialize = False
        self.isList = False

    @staticmethod 
    def fromLine(line, fileContent="", lineNumber=-1) : 
        _r = Attr()
        decl = line.split("=")[0]
        decl = whitespacesCleaned(decl)
        decl = decl.split(";")[0]
        tmp = decl.split(" ")
        if len(tmp) > 1 :
             _r.name = tmp[-1]

        _r.type = " ".join(tmp[:-1])
        if lineNumber > -1 and fileContent != "" : 
            _r.setNamespaces(fileContent, lineNumber)
        return _r

    def setNamespaces(fileContent, lineNumber) : 
        self.namespaces.append(namespace(fileContent, lineNumber))

    #the lines sould be a list or a str, if str it will be splitted by '\n'
    @staticmethod
    def fromLines(lines) : 
        if type(lines) == str : 
            lines = lines.split("\n")

        line = ""
        for l in lines : 
            line += l + " "

        return Attr.fromLine(line)

    #std::strin is considerate simple here
    def isComplex(self) : 
        return isTypeComplex(self.type)

    def getterType(self, const=False) :
        if ("vector" in self.type or "Vec" in self.type) :
            if const :
                return "const " + self.type + "&"
            else : 
                return self.type + "&"

        if "*" in self.type or "ptr" in self.type or "pointer" in self.type : 
            if const : 
                return "const " + self.type
            else : 
                return self.type

        ty = self.type.split("<")[0]
        if  ("bool" in ty or 
             "int" in ty or 
             "long" in ty or 
             "char" in ty or 
             "float" in ty or 
             "double" in ty or
             "string" in ty) : 
            if const : 
                if "string" in ty : 
                    return "const " + self.type + "&"
                else : 
                    return "const " + self.type
            else : 
                return self.type

        ty = self.type + "&"
        if const : 
            ty = "const " + ty
        return ty

    def getterName(self) : 
        if self.name[0] == "_" : 
            return self.name[1:]
        else : 
            return "get" + self.name[0].upper() + self.name[1:]

    def setterType(self) : 
        if "*" in  self.type : 
            return self.type

        ty = self.type.split("<")[0]
        if  ("bool" in ty or 
             "int" in ty or 
             "long" in ty or 
             "char" in ty or 
             "float" in ty or 
             "double" in ty) :
            return self.type

        ty = self.type + "&"
        ty = "const " + ty
        return ty

    def getter(self, const=False) : 
        if not const :
            return self.getterType() + " " + self.getterName() + "(){return " + self.name + ";}"
        else :
            return self.getterType(True) + " " + self.getterName() + "() const {return " + self.name + ";}"

    def getters(self) : 
        _r = self.getter()
        if self.addConstGetter : 
            _r += "\n" + self.getter(True)


    def setterArgName(self) : 
        if self.name[0] == "_" : 
            return self.name[1:]
        else : 
            return "new" + self.name[0].upper() + self.name[1:]

    def setter(self) : 
        _r = "void "
        name = self.name
        if name[0] == "_" : 
            name = self.name[1:]
        _r += "set" + name[0].upper() + name[1:] + "(" + self.setterType() + " " + self.setterArgName() + "){" + self.name + " = " + self.setterArgName() + ";}"
        return _r

    def impl(self) : 
        _r = ""
        if self.addGetter : 
            _r += self.getter() + "\n"
        if self.addConstGetter : 
            _r += self.getter(True) + "\n"
        if self.addSetter : 
            _r += self.setter()

        return _r

    def serializeLine(self) : 
        cmplx = self.isComplex()
        if not cmplx : 
            return "_j[\"" + self.name + "\"] = " + self.name + ";"

        sep = "."
        if "*" in self.type or "ptr" in self.type or "pointer" in self.type : 
            sep = "->"

        if self.isList : 
            cppId = "_j[\"" + self.name + "\"]"
            _r = cppId + " = json::array();\n"
            _r += "for (int i=0; i<" + self.name + ".size(); i++)\n"
            tpl = listTemplate(self.type)
            cmplx_tpl = isTypeComplex(tpl, True)

            if cmplx_tpl : 
                _r += "    " + cppId + ".push_back(" + self.name + "[i]" + sep + "serialize());"
            else : 
                _r += "    " + cppId + ".push_back(" + self.name + "[i]);"
            return _r

        else : 
            return "_j[\"" + self.name + "\"] = " + self.name + sep + "serialize();"

    def deserializeLine(self) : 
        cmplx = self.isComplex()
        _r = "if (_j.contains(\"" + self.name + "\"))\n"
        if not cmplx : 
            _r += self.name + " = _j[\"" + self.name +"\"];"
            return _r

        sep = "."
        if "*" in self.type or "ptr" in self.type or "pointer" in self.type : 
            sep = "->"

        if self.isList : 
            tpl = listTemplate(self.type)
            cmplx_tpl = isTypeComplex(tpl, True)
            _r += self.name + ".clear();\n"
            _r += "for (auto& ji : _j[\"" + self.name + "\"])\n{\n" #}

            if cmplx_tpl : 
                _r += "    " + tpl + " tmp;\n"
                _r += "     tmp.deserialize(ji);\n"
                _r += "    " + self.name + ".push_back(tmp)\n";
            else : 
                _r += "    " + self.name + ".push_back(ji.get<" + tpl + ">());\n"

            _r += "}"
            return _r

        else : 
            _r += self.name + sep + "deserialize(_j[\"" + self.name +"\"]);"
            return _r


class Class : 
    def __init__(self) : 
        self.attrs = []
        self.name = ""

    def gettersNSetters(self) : 
        _r = ""
        for a in self.attrs : 
            _r += a.impl() + '\n\n'
        return _r

    def serializeMethodDecl(self) : 
        return "json serialize_gen() const;"

    def deserializeMethodDecl(self) : 
        return "void deserialize_gen(const json& _j);"

    def serializeMethodImpl(self) : 
        _r = "json " + self.name + "::serialize_gen() const\n{\n" #}
        _r += "json _j;\n"
        for a in self.attrs : 
            if a.addSerialize : 
                _r += "    " + a.serializeLine() + "\n"
        _r += "return _j;\n}\n\n"
        return _r

    def deserializeMethodImpl(self) : 
        _r = "void " + self.name + "::deserialize_gen(const json& _j)\n{\n" #}
        for a in self.attrs : 
            if a.addSerialize : 
                _r += "    " + a.deserializeLine() + "\n"
        _r += "}\n\n"
        return _r

    @staticmethod
    def fromFile(fileContent) : 
        lines = fileContent.split("\n")
        attrs = []
        cls = Class()

        for i in range(len(lines)) : 
            ln = i + 1
            tmp = lines[i].split("//bp ") #bp => boiler plate code generation
            if len(tmp) > 1 : 
                comments = tmp[1]
                a = Attr.fromLine(lines[i])
                if "g" in comments : 
                    a.addGetter = True
                if "gc" in comments or "cg" in comments : 
                    a.addConstGetter = True
                if "s" in comments : 
                    a.addSetter = True
                if "x" in comments : 
                    a.addSerialize = True
                if "l" in comments : 
                    a.isList = True
                cls.attrs.append(a)
        return cls

    def needSerialize(self) : 
        for a in self.attrs : 
            if a.addSerialize : 
                return True
        return False


# main function

def generate(dir) : 
    for f in os.listdir(dir) : 
        filepath = dir + os.sep + f
        if os.path.isdir(filepath) :
            generate(filepath)
        else : 
            generateFromfile(filepath)

def generateFromfile(filepath) : 

    #TODO : add the ability to do it in namespace too (for now, it written in .h file, so not possible.)
    if ft.ext(filepath) != "h" and ft.ext(filepath) != "hh" : 
        return

    if "_gen." in filepath : 
        return

    cls = Class.fromFile(ft.read(filepath))
    cls.name = ft.filename(ft.noExt(filepath))
    hgen = ft.noExt(filepath) + "_gen.h"
    s = "//This is a generated file, don't change it manually, it will be override when rebuild.\n\n"
    content = cls.gettersNSetters()
    if cls.needSerialize() : 
        content += cls.serializeMethodDecl() + "\n" + cls.deserializeMethodDecl()
    if content != "" : 
        res = ft.write(s + content, hgen)
        if res == 0 : 
            print("Error generating : " + hgen)
        else : 
            print(ft.filename(hgen) + " generated from " + ft.filename(filepath))
    else : 
        try : 
            os.remove(hgen)
        except : pass

    cppgen = ft.noExt(filepath) + "_gen.cpp"
    if not cls.needSerialize() : 
        try :
            os.remove(cppgen)
        except : pass
        return
    s = "//This is a generated file, don't change it manually, it will be override when rebuild.\n\n"
    content = "#include \"./" + ft.filename(filepath) + "\"\n\n"
    content += cls.serializeMethodImpl() + cls.deserializeMethodImpl()
    ft.write(s + content, cppgen)
    print(ft.filename(cppgen) + " generated from " + ft.filename(filepath))

def createCppFile(headerFilepath) : 
    if ft.ext(headerFilepath) != "h" and ft.ext(headerFilepath) != "hh" : 
        raise Exception ("Not a header file : " +  headerFilepath)

    cpp = headerFilepath.replace(".hh", ".cpp")
    cpp = cpp.replace(".h", ".cpp")

    if os.path.exists(cpp) : 
        print (cpp + " already exists. File generation aborted.")
        return

    content = "#include \"./" + ft.filename(headerFilepath) + "\"\n"
    ft.write(content, cpp)
    print(ft.filename(cpp) + " generated.")

#func is a Function object (from the class Function)
def ctypesPyFunc(func) : 
    isCharRet = "char*" in func.returnType
    r = ""
    if (isCharRet) :
        r += "lib." + func.funcname + ".restype = ctypes.c_char_p\n"
    r+= "def " + func.funcname + "("
    argsstr = ""
    for a in func.args :
        argsstr += a.name + ","
    argsstr = argsstr[:-1]
    r+= argsstr

    argsstr = argsstr.split(",")
    for i in range(len(argsstr)) :
        if "char*" in func.args[i].type : 
            argsstr[i] = argsstr[i] + ".encode(\"utf-8\")"

    r+= ") : \n"
    r+= "    return lib." + func.funcname + "(" + ",".join(argsstr) + ")"
    if (isCharRet) :
        r += ".decode(\"utf-8\")"
    r += "\n"
    return r

def generatePythonCFile(libpath, cheaders, pytonfile) : 
    pycode = "#This is a generated file, don't change it manually, it will be override when rebuild.\n\n"
    pycode += "import ctypes\n"
    pycode += "lib = ctypes.CDLL(\"" + libpath + "\")\n"

    for cheader in cheaders : 
        if not os.path.exists(cheader) : 
            raise Exception ("C header file not found : " + cheader)

        ccodef = open(cheader, "r")
        ccode = ccodef.read()
        ccodef.close()

        ccode = ccode.split("extern \"C\"")[1]
        for l in ccode.split("\n") : 
            if ";" in l and "//" not in l and "/*" not in l and "*/" not in l : 
                f = Function.fromLine(l)
                pycode += ctypesPyFunc(f) + "\n"

    pycodef = open(pytonfile, "w")
    pycodef.write(pycode)
    pycodef.close()

    print(pytonfile + " generated.")

#Function function
#modulevar as string
def pybindFunc(function, modulevar, namespace="") : 
    r = modulevar + ".def(\"" + function.funcname + "\", &"
    if namespace == "" : 
        r+= function.funcname
    else : 
        r+= namespace + "::" + function.funcname
    r+= ");"
    return r

def pybindCls(classname, cts_args_type="", modulevar="m") : 
    r = "py::class_<" + classname + ">(" + modulevar + ", \"" + classname + "\")\n"
    r+= ".def(py::init<" + cts_args_type + ">())\n"
    return r

def pybindMethod(function, classname) : 
    tcast = function.returnType + " (" + classname + "::*)("
    for a in function.args :
        tcast += a.type + ","
    tcast = tcast[:-1]
    tcast += ")"
    if function.const :
        tcast += " const"
    tcast = "(" + tcast + ")"
    r = ".def(\"" + function.funcname + "\", " + tcast + "&" + classname + "::" + function.funcname + ")"
    return r
