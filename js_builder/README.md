# js_builder

A no-bullshit JS/CSS build tool. Minifies, bundles, hashes, generates HTML. That's it.

Built on top of `uglifyjs` and `cleancss`. If you don't have those, go install them.

---

## What it does

- Bundles JS and CSS files (individually or grouped)
- **Debug mode** → no compilation, raw files, fast iteration
- **Release mode** → minifies everything via `uglifyjs` + `cleancss`, injects a content hash in filenames (cache busting, you're welcome)
- Generates the final HTML from a template
- Tracks written files so it can clean up after itself
- `install()` copies the built output to a destination folder, removing stale files

---

## Dependencies

```bash
npm install -g uglify-js clean-css-cli
```

Also uses this `py-utils` lib imported as `ml`.
If you followed the installation from the `py-utils` [repo]("https://github.com/Rrominet/py-utils"), you're good to go.

---

## Basic usage

```python
#!/usr/bin/env python3
from ml import js_builder
import sys

pr = js_builder.create(sys.argv)

# Your HTML template file (relative to build_dir)
# The built output will be written as index.html (strips the _tpl part)
pr.html_tpl = "index_tpl.html"

# Add individual files
pr.addFiles("frameworks/libs/highlight.min.js")

# Bundle multiple files under one output name
pr.addFiles([
    "frameworks/js/db.js",
    "frameworks/js/utils.js",
    "frameworks/js/HttpRequest.js",
], "lib")

# Add a whole directory
pr.addFiles("js/")

# CSS works the same way
pr.addFiles("style.css")

if "clean" in sys.argv:
    pr.clean()
elif "install" in sys.argv:
    pr.install("/var/www/html/my-project")
else:
    pr.build()
```

Run it:

```bash
./make          # debug build
./make release  # release build (minified + hashed)
./make clean    # removes all generated files
./make install  # copies output to destination
```

---

## HTML Template

Your template needs two placeholders. js_builder will inject the right `<script>` and `<link>` tags automatically:

```html
<!DOCTYPE html>
<html>
<head>
    *css*
</head>
<body>
    ...
    *js*
</body>
</html>
```

---

## API

### `js_builder.create(argv=[], build_dir="")`
Creates a `JsProject`. Pass `sys.argv` and it handles debug/release for you. `build_dir` defaults to `cwd`.

---

### `pr.addFiles(src, keyname="")`
- `src` → a file path, a list of file paths, or a directory path (relative to `build_dir`)
- `keyname` → output filename when bundling multiple files together. Defaults to the first file's basename.
- JS and CSS are handled separately, no need to sort them yourself.

---

### `pr.build()`
Does the whole thing. Clean → Compile (if release) → Write → Generate HTML.

---

### `pr.clean()`
Removes every file that was written by a previous build. Tracked in `.written_files`.

---

### `pr.install(dest)`
Copies built files to `dest`. Removes stale `.js`, `.css`, `.html` files in the destination that are no longer part of the build. Won't copy files that haven't changed.

---

### `pr.setType(type)`
`js_builder.debug` or `js_builder.release`. Usually handled automatically via `setFromArgs(sys.argv)`.

---

## Release mode: hashed filenames

In release mode, output files get a content hash injected:

```
lib.js  →  lib.a3f9c21b.js
```

Cache busting without thinking about it. The HTML template gets updated automatically with the correct paths.

---

## File tracking

js_builder writes a `.written_files` file in your `build_dir`. Don't delete it manually or `clean()` won't know what to remove. You've been warned.

---

## License

Do whatever you want with it.
