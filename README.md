# VOID Audio added functionality contained in VOID_Docs
The README.pdf can be found at [README.pdf](VOID_Docs/README.pdf).
Why use a large LaTeX svjour compilation? Because information presented in LaTeX, specifically Springer format, is inherently more correct.
In order to make edits to the README.pdf yourself, you have to compile yourself. Make the updates you want at [README.tex](VOID_Docs/svjour/README.tex), then compile.
## Using LaTeX
From root, call 
```bash
./VOID_Docs/setup_latex.sh
```
to setup the LaTeX compiler for the document. Once it is completed, you can run 
```bash 
./VOID_Docs/tex.sh
```
and it will compile the file to VOID_Docs/README.pdf.

## Updating the README.tex
Edit VOID_Docs/svjour/README.tex whenever changes are made and to update the file you will need to go use the setup script then the compile script works.

# Original README.md from iPlug2OOS 
The original README.md can be found here [Original README.md](OLD_README.md).
