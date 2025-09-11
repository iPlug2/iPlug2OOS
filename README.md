# VOID Audio added functionality contained in VOID_Docs
You need to compile the latex document, but I have made scripts to achieve this. Why use a large LaTeX svjour compilation? Because information presented in LaTeX, specifically Springer format, is inherently more correct.
## setup_latex.sh
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
