FROM python:3.13-slim-bookworm

# Incluye el simulador externo, Java para regenerar ANTLR y Graphviz para el AST.
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless spim graphviz bash-completion curl \
    && rm -rf /var/lib/apt/lists/*

COPY antlr-4.13.1-complete.jar /usr/local/lib/antlr-4.13.1-complete.jar
COPY commands/antlr commands/grun /usr/local/bin/
RUN chmod +x /usr/local/bin/antlr /usr/local/bin/grun
ENV CLASSPATH=.:/usr/local/lib/antlr-4.13.1-complete.jar

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt

ARG APP_UID=1001
RUN useradd --create-home --uid "${APP_UID}" appuser
USER appuser
WORKDIR /workspace

# Montar el repositorio completo, no solamente program/.
# docker build -t compiscript-fase3 .
# docker run --rm -it -v "$(pwd)":/workspace compiscript-fase3
# Para el IDE (despues de integrar la parte 2):
# docker run --rm -p 5001:5001 -e IDE_HOST=0.0.0.0 \
#   -v "$(pwd)":/workspace compiscript-fase3 python ide/app.py
EXPOSE 5001
CMD ["bash"]
