FROM emscripten/emsdk:2.0.3

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends vim \
    && pip3 install semver

RUN echo "alias lr='ls -lart' \n alias cd..='cd ..'" >> "$HOME/.bashrc"