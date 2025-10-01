# py-utils

## Subprojects :

This repo contains the following subprojects :
 - [fxmake](https://github.com/Rrominet/py-utils/tree/main/build)
 - [boilerplate](https://github.com/Rrominet/py-utils/tree/main/boilerplate)

## Installation

Just run the `install` script as `sudo` in the root directory of the project.  
For your convinience, use the code below to download this git repo, and install it on your system automaticly : 

If you don't have python3 installed on your system for any reason : 
```bash 
sudo apt install python3 # << or equivalent for your distro
```

```bash
git clone https://github.com/Rrominet/py-utils.git
cd ./py-utils
sudo chmod +x ./install
sudo ./install
cd ..
rm -rf ./py-utils #remove the git repo, not needed once it's installed. But you can keep it you want.
```
You should be good to go.

If you want to uninstall it simply run the `uninstall` script with `sudo`.

## Usage

For now, this repo is not meant to be used alone (that being said, you can if you want - more on that later).  
It's a dependencies for my others projects in python that will download and install this repo automaticly if needed.

If you still want to use it as a standalone module, this one is called `ml`.
So in your python script/program just write : 

```python
import ml
# or
from ml import ...
```

For example, to import our file tools module : 

```python
from ml import fileTools as ft
ft.write("Some data", "path/to/file")
```

> [!NOTE]
> The documentation is not done yet, so for now, you need to read the source code.  
> Sorry :)

## TODO

- Make it usable as standalone python module with a proper documentation.
