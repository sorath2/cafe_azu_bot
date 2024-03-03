FROM python:3.10-slim-bookworm

ENV IS_DOCKER DOCKER

ENV WORKDIR /app
ENV USER admin

WORKDIR $WORKDIR

COPY . .

RUN apt-get update && \
    apt-get install -y netcat-traditional && \
    pip install --upgrade pip && \
    pip install --no-cache-dir poetry==1.6.1 && \
    poetry config virtualenvs.create false && \
    poetry install

RUN mkdir -p $WORKDIR/static/ && \
    mkdir -p $WORKDIR/media/ && \
    groupadd -r $USER && \
    useradd -d $WORKDIR -r -g $USER $USER && \
    chown $USER:$USER -R $WORKDIR && \
    chmod g+x,o+x -R $WORKDIR/media/ && \
    chmod +x dep.sh

EXPOSE 8000

USER $USER

# CMD ["gunicorn", "admin_panel.wsgi:application", "--bind", "0:8000" ]
ENTRYPOINT ["/bin/bash","/app/dep.sh"]
