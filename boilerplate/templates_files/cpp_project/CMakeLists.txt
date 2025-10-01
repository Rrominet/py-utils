# only for cmake --version >= 3.5.1
cmake_minimum_required(VERSION 3.5.1)

# project name
project(your_app_name)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

#lsp file
set(CMAKE_EXPORT_COMPILE_COMMANDS 1)

# I../includes

include_directories(SYSTEM
/media/romain/Donnees/Programmation/C++/libs/json
/media/romain/Donnees/Programmation/C++/libs/boost-install/include
/media/romain/Donnees/Programmation/C++/libs/eigen
)

include_directories(
src 
/media/romain/Donnees/Programmation/C++/frameworks
/media/romain/Donnees/Programmation/C++/frameworks/files
)

# puts all .cpp files inside src to the SOURCES variable
file(GLOB SOURCES 
    src/*.cpp 
    /media/romain/Donnees/Programmation/C++/frameworks/debug.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/str.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/vec.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/random.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/Perfs.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/files/File.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/files/Dir.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/mlTime.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/base64.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/thread.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/os.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/mlprocess.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/json.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/network/TcpClient.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/network/TcpServer.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/network/HttpServer.cpp
    /media/romain/Donnees/Programmation/C++/frameworks/math_json.cpp
)

add_compile_options(-Wall -Wextra -Wshadow -Wsign-conversion 
    -Wno-unused-parameter 
    -Wno-ignored-qualifiers
    -Wno-unused-function
    )
if (CMAKE_BUILD_TYPE MATCHES Debug)
    add_compile_definitions(mydebug)
    add_compile_definitions(DBOOST_STACKTRACE_USE_BACKTRACE)
    add_compile_options(-D_FILE_OFFSET_BITS=64 -O0 -g3 -rdynamic)
else()
    add_compile_options(-D_FILE_OFFSET_BITS=64 -O3)
endif(CMAKE_BUILD_TYPE MATCHES Debug)

# compiles the files defined by SOURCES to generate the executable defined by EXEC
add_executable(${PROJECT_NAME} ${SOURCES})

# linkers
set(CMAKE_EXE_LINKER_FLAGS "-static-libgcc -static-libstdc++") #include libc, libgcc and libstdc++ in my executable. It's way more portable this way.
target_link_libraries(${PROJECT_NAME} 
    pthread
    stdc++fs
    /media/romain/Donnees/Programmation/C++/libs/boost-install/lib/libboost_filesystem.a
)
