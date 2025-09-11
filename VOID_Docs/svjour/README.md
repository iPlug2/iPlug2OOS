# Simplified Springer Journal Template

> Quick start for modern LaTeXing with [Springer Journals](http://www.springer.com/computer/journal/450?detailsPage=pltci_1060413)

The files `svjour3.cls`, `spbasic.bst`, `spmpsci.bst`, `spphys.bst` are copyright by Springer.
The are only allowed to be used when submitting to a journal published by Springer.

## Features

* Provides a skeletal [paper.tex](paper.tex) file.
  See [paper.pdf](paper.pdf) for a rendered result.
* Ready-to-run configuration with BibTeX.
* Linked DOI field.
* Working configuration for [microtype] and [cleveref].
* [natbib] enabled as default.
* Generated PDF allows for copy and paste of text without getting words with ligatures such as "workflow" destroyed.
  This is enabled by the [cmap] package, which encodes ligatures (such as fl) using unicode characters.
* Automatic setting of "Fig." and "Section"/"Sect." according to the LNCS style.
  Just use `\Cref{sec:xy}` at the beginning of a sentence and `\cref{sec:xy}` in the middle of a sentence.
  Thanx to [cleveref].
* Support of hyperlinked references without extra color thanx to [hyperref].
* Better breaking of long URLs.
* Sharper font (still compatible with Springer's requirements). See <https://tex.stackexchange.com/a/98405/9075> for a discussion.
* Support for `\powerset` command.
* Support todos as pdf annotations. This is enabled by the [pdfcomment] package.
* [microtypographic extensions](https://www.ctan.org/pkg/microtype) for a better look of the paper.
* Adds modern packages such as [csquotes], [paralist], [hyperref], [hypcap], [upquote], [booktabs], [cfr-lm].
* <s>Optional: Support for [minted] package. Uncomment `\usepackage[newfloat]{minted}` to get started.</s>
* Optional: Compile with `lualatex` instead of `pdflatex`.
* Ready-to-go configuration for [latexindent].

## Tool hints

There is currently no official biblatex support.

MiKTeX installation hints are given at <https://github.com/latextemplates/scientific-thesis-template/blob/template/README.md#installation-hints-for-windows>.

- Grammar and spell checking is available at [TeXstudio].
  Please download [LanguageTool] (Windows: `choco install languagetool`) and [configure TeXstudio to use it](http://wiki.languagetool.org/checking-la-tex-with-languagetool#toc4).
  Note that it is enough to point to `languagetool.jar`.
  **If TeXstudio doesn't fit your need, check [the list of all available LaTeX Editors](http://tex.stackexchange.com/questions/339/latex-editors-ides).**
- Use [JabRef] to manage your bibliography (Windows: `choco install jabref`).

In case you want to get started using minted, do following steps:

1. Install python: `choco install python` - that uses [chocolatey](https://chocolatey.org/) to install Python
2. Install [pygments]: `pip instal pygments` - that uses the Pyhton package manager to install the pygments library
3. When latexing, use `-shell-escape`: `pdflatex -shell-escape paper`.
   You can also just execute `latexmk paper`.

## Using the template with your git repository

1. Initialize your git repository as usual
2. Add this repository as upstream: `git remote add upstream https://github.com/latextemplates/LNCS.git`
3. Merge the branch `upstream/master` into your `master` branch: `git merge upstream/master`.

After that you can use and push the `master` branch as usual.
Notes on syncing with the upstream repository [are available from GitHub](https://help.github.com/articles/syncing-a-fork/).

## FAQ

### Q: I get the error  `! pdfTeX error (font expansion): auto expansion is only possible with scalable fonts.`

Install the `cm-super` package using the MiKTeX package manager. Then, run `initexmf --mkmaps` on the command line. (Long description: http://tex.stackexchange.com/a/324972/9075)

### Q: How can I reformat my .tex files?

Execute `latexindent -l -s -sl -w paper.tex`

### Q: How I want to obey the one-sentence-per-line rule.

Execute `latexindent -m -l -s -sl -w paper.tex`.
Attention! This is work in progress and does not always produce best results.

## Development [![Donate to koppor on Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/koppor)

Reindent: `latexindent -y="indentPreamble:1,defaultIndent:'  '" -m -w paper.tex`

If you like this work, please consider donating via [Liberapay](https://liberapay.com/koppor)!

## Links

 * Other templates: <https://latextemplates.github.io/>

  [booktabs]: https://ctan.org/pkg/booktabs
  [cfr-lm]: https://www.ctan.org/pkg/cfr-lm
  [cleveref]: https://ctan.org/pkg/cleveref
  [cmap]: https://www.ctan.org/pkg/cmap
  [csquotes]: https://www.ctan.org/pkg/csquotes
  [hypcap]: https://www.ctan.org/pkg/hypcap
  [hyperref]: https://ctan.org/pkg/hyperref
  [latexindent]: https://ctan.org/pkg/latexindent
  [microtype]: https://ctan.org/pkg/microtype
  [minted]: https://ctan.org/pkg/minted
  [natbib]: https://ctan.org/pkg/natbib
  [newtx]: https://ctan.org/pkg/newtx
  [paralist]: https://www.ctan.org/pkg/paralist
  [pdfcomment]: https://www.ctan.org/pkg/pdfcomment
  [upquote]: https://www.ctan.org/pkg/upquote

  [JabRef]: https://www.jabref.org
  [LanguageTool]: https://languagetool.org/
  [TeXstudio]: http://texstudio.sourceforge.net/
  [pygments]: http://pygments.org/
