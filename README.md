# LaTeX files

This repository contains files I use for LaTeX and beamer styling, as well
as simple document templates.

## Installation

For use with a simple documents, simply place the `.sty` files you need in
the same folder as your `.tex` document

For general use on Linux, place the `.sty` files in `~/texmf/tex/latex/` or any subdirectory thereof.

## Contents

**Color theme:**
- [styles/beamercolorthemeeyedark.sty](./styles/beamercolorthemeeyedark.sty): The eyedark color theme for beamer metropolis (dark blue, dark red or dark green)

**Style files:**
- [styles/my-preamble.sty](./styles/my-preamble.sty): common imports and some useful functions
- [styles/my-math.sty](./styles/my-math.sty): math shortcut definitions, theorems and operators
- [styles/my-metropolis.sty](./styles/my-math.sty): configures beamer metropolis to add section pages

**Templates:** simple prefilled document to avoid retyping common things
- [templates/document.tex](./template/document.tex)
- [templates/beamer.tex](./template/document.tex)

**Scripts:**
- [scripts/newtex](./scripts/newtex): bash script to generate a new tex file from template and open texmaker
- [scripts/texcleanup](./scripts/texcleanup): bash script to remove tex build files in a build directory
