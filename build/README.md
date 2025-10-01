# fxmake

## Build Module Documentation (fxmake)

The **build module** (fxmake) is a Python library that provides a simple build system for **C** and **C++** projects.  
It’s designed to be easy to use.

## Installation 

See the installation process in the parent repo `py-utils` [here](https://github.com/Rrominet/py-utils)

## Getting Started

First, import the module:

```python
from ml import build
```

Then create a project instance:

```python
prj = build.create("executable_name")
```

The name you pass will be the name of your executable.

## Build Configuration

### Setting build mode (Debug/Release)

You can set build settings automatically from arguments in your Python script:

```python
prj.setFromArgs(argv)
```

Or directly when creating the project:

```python
prj = build.create("executable_name", argv)
```

> [!NOTE]
> By default, the build is in `debug`, to set it in `release`, just pass the argument "release" in `argv` (Or generally calling your build script)

### Choosing a compiler

By default, the builder is `g++`. You can override it:

```python
prj = build.create("executable_name", argv, "your-builder")
```

⚠️ Do **not** set the builder afterward like this:

```python
prj.builder = "..."
```

This will not work, because some settings are initialized inside `create`.

## Project Setup

### Includes

Add include directories:

```python
prj.includes = ["dir1", "dir2", ...]
```

### Source files

Add source files:

```python
prj.addToSrcs(["file1.c", "file2.cpp", ...])
```

* If you provide a directory, all files inside it are added.
* Use the `recursive` argument to add files recursively.

Access all source files:

```python
prj.srcs
```

Exclude files during compilation/linking:

```python
prj.srcs_exclude.append("your-file-name.cpp")
```

### Compiler options

Add compiler definitions:

```python
prj.definitions += ["def1", "def2", ...]
```

Add compiler flags:

```python
prj.flags += ["O3", "Wall", ...]  
```

(`-` prefix is optional, it will be handled.)

### Libraries

#### Static libraries

```python
prj.addToLibs(["/full/path/lib1.a", "/full/path/lib2.a", ...])
```

#### Shared libraries

```python
prj.addToLibs(["name1", "name2", ...])
```

* Remove the `.so` extension and `lib` prefix (but if you don’t, it still works).
* If only `.so.version` files exist, the build system will create a symlink
  (`./yourfile.so -> ./yourfile.so.version`).
  If the symlink already exists, nothing happens.

#### Library directories

```python
prj.addToLibDirs(["/full/path/dir1", "./libs/dir2", ...])
```

* `./` is converted to `$ORIGIN/` for runtime (`rpath`).
* You can inspect linked libraries at runtime with:

```bash
readelf -d ./your_binary
```

### Installed libraries (pkg-config)

If a library is installed system-wide and managed by `pkg-config`:

```python
prj.addInstalledLibrary("libname")
```

This automatically adds the correct includes, flags, and libs.

### Static executables

To make your binary fully independent by statically linking the standard C and C++ libraries:

```python
prj.static = True
```

It’s useful mainly when targeting systems with older `libc`.

> [!WARNING]
> This increases binary size and may break some functions, since `libc` was not designed for static linking.  

## Building

Build your project:

```python
prj.build()
```

By default, a `compile_commands.json` file is exported in the parent directory.  
Disable it if you don’t need it:

```python
prj.export_compile_commands = False
```

## Shared Libraries

To create a **shared library** instead of an executable:

```python
prj.shared = True
```

## Cleaning

Clean all `.o` and cache files:

```python
prj.clean()
```

A common practice:

```python
if "clean" in sys.argv or "clear" in sys.argv:
    prj.clean()
else:
    prj.build()
```

## Example

For a complete working example, see the [examples](https://github.com/Rrominet/py-utils/tree/master/examples) folder (especially the script files `make`).

