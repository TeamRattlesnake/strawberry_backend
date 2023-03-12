FROM fedora:latest

WORKDIR /home

COPY ./requirements.txt /home

COPY ./config.json /home

COPY ./src /home

RUN dnf install -y pip && \
    pip install -r requirements.txt

CMD ["uvicorn", "--app-dir", ".", "--host", "0.0.0.0", "--port", "14565", "server:app"]
