A python library that helps you with basicly every think you need to do in python code every day life.

- Convenient files function wrapper
- Common abstraction for knowm patterns (like Command, Singleton, etc.)
- Thread and multithread helper
- Http server and client
- Process and multiprocess run
- A c/cpp builder(like cmake but simpler to use)
- A boilerplate code generator
- And a lot more.

The philosopy behind it is stupidly simple : 
All I find fuckin annoying to do in python, in put in this library so I don't have to write ever again.

Now you can use it too.
Don't thank me. :)

## Installation

Ok let's start with the installation, because you can't do much without it lol.
It's really simple, just install `git` and `python` if you don't have them already and run : 

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

## First usage and test

Ok just to test if it works now. 
create a file named `named.py` in any writtable directory and write in it : 
```python
from ml import fileTools as ft
ft.write("Hello world !", "./test")
```

Now run `python ./test` and you should get `Hello world !` in the file named `test`.
If yes, congrats, you're good to go.

If not, reread the step you ceratinly forgot something.
If you think that I am the cause of your misary, just contact me here and explain your problem to me, will find a solution.

## Documentation

Like a said, `py-utils` is a bunch of modules, functions and classes that sove real world problem.
So there not really a linear way to learn how to use it. But chill the fuck out, you'll see, it's not complicated.

Here are some of the modules you could start with that I use the more often :

 - The `args` module (Automatic and argument parser)
 - The `fileTools` module (Easy-to-use and convienient file tools)
 - The `commands` module (An abstraction that let you use the `Commande Pattern` easily and that does practicly all for you)
 - The `network`, `TcpServer`, `curl` modules that let you basicly to all the networking stuff you need.
 - The `ffmpeg` module to convert and edit videos easily.
 - The `ipc` module that implement an easy-to-use *Interprocess Communication* system.

And else, you can just search for anything (`Ctrl F`) and you'll arrive on the module you're looking for. (if it exists.)

