#include <iostream>
#include "debug.h"
#include <string>
#include "hash.h"
#include "files/File.h"

int main(int argc, char** argv)
{
    path::_execDir();
#ifdef def1
    lg("def1");
#endif
    lg("Hello World!");
    std::string data = "This is my data.";
    std::cout << data << std::endl;
    std::cout << "this is the hased version : " << hash::sha3(data, 256) << std::endl;
    std::cout << "There is a change !" << std::endl;
    return 0;
}
