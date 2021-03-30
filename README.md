# LaTeX files

This repository contains files I use for LaTeX and beamer styling, as well
as simple document templates.

## Installation

For use with a simple documents, simply place the `.sty` files you need in
the same folder as your `.tex` document

For general use on Linux, place the `.sty` files in `~/texmf/tex/latex/` or any subdirectory thereof.

To install the script, add an `alias texmgr='path/to/texmgr'`.

## Contents

**Color theme:**
- [styles/beamercolorthemeeyedark.sty](./styles/beamercolorthemeeyedark.sty): The eyedark color theme for beamer metropolis (dark blue, dark red or dark green). See [previews](./previews) for sample pdf ouputs.

**Style files:**
- [styles/my-preamble.sty](./styles/my-preamble.sty): common imports and some useful functions
- [styles/my-math.sty](./styles/my-math.sty): math shortcut definitions, theorems and operators
- [styles/my-metropolis.sty](./styles/my-math.sty): configures beamer metropolis to add section pages

**Templates:** simple prefilled document to avoid retyping common things
- [templates/document.tex](./template/document.tex)
- [templates/beamer.tex](./template/document.tex)

**Scripts:**
- [scripts/texmgr.py](scripts/texmgr.py): python script to compile/initialize and clean texfiles.
- [scripts/texmgr](scripts/texmgr): executable that calls the `texmgr.py` script's `main`


		Usage: texmgr [--flags] [file list]

		Compiles all files in the file list (defaut, all *.tex files
		in current working directory). Compile three times and clean
		build files afterward

		Flags:
		  --no-clean -n     don't remove build files after compiling
		  --rounds -r <int> number of compile rounds, default = 3

		  --init -i         create files in file list rather than compile them
		  --init-beamer -b  same as --init, but uses the beamer template to create files
		  --clean -c        only clean files (removes build files)
		                    Files removed match a .tex file in the list
		                    and have the following extensions:
		                      aux, log, nav, out, synctez.gz, snm, vrb, toc, bbl

		  --verbose -v      print the commands called
		  --dry-run -d      print the commands but don't run them
		  --version         show version number
		  --help -h         show this help



**Old scripts:**
- [scripts/old/newtex](./scripts/old/newtex): bash script to generate a new tex file from template and open texmaker
- [scripts/old/texcleanup](./scripts/old/texcleanup): bash script to remove tex build files in a build directory
