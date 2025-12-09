The `args` module is used to parsed automaticly any command line argument
The format of the arguments should be as such : 
```bash
your-program posarg1 posarg2 -namearg1 value1 -namearg2 value2 -boolflag
```

It's usage is fucking simple.
First import the module.

```python
from ml import args
```

When you import the module, the parsing of the arguments is done automaticly.
So now you just need to know how to retreive them.

Like this :

```python
args.allPositionnal() # return a list of the positionnal arguments
args.option("your-option") # will return the value assosiated to --your-option (ou -your-option) 
args.flag("your-flag") # will return True if the flag is present, False otherwise (once again work for --your-flag and -your-flag)
```

Like I said, easy as fuck.
