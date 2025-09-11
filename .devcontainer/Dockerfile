FROM emscripten/emsdk

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
<<<<<<< HEAD
    && apt-get -y install --no-install-recommends nano \
    && pip3 install semver
=======
    && apt-get -y install --no-install-recommends vim \
    && pip3 install semver openai requests python-config-parser
>>>>>>> cloud-dev-trash-branch

RUN echo "alias python=python3 \n alias lr='ls -lart' \n alias cd..='cd ..'" >> "$HOME/.bashrc"
