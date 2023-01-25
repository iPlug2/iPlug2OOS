FROM emscripten/emsdk

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends vim faust \
    && pip3 install semver

RUN echo "alias python=python3 \n alias lr='ls -lart' \n alias cd..='cd ..'" >> "$HOME/.bashrc"

#patch emcc.py
RUN sed -i.bak s,"if not js_manipulation.isidentifier(settings.EXPORT_NAME):","if False:",g "/emsdk/upstream/emscripten/emcc.py"
