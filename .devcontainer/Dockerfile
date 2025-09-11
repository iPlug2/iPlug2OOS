FROM emscripten/emsdk


RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends vim wget biber latexmk \
    && pip3 install semver


RUN echo "alias python=python3 \n alias lr='ls -lart' \n alias cd..='cd ..'" >> "$HOME/.bashrc"

# include stuff I need for svjour LaTeX because its the best
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        texlive-lang-german \
        texlive-babel-german

