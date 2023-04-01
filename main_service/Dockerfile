FROM adefe/strawberry_env:v2

WORKDIR /home

COPY ./config.json /home

COPY ./src /home

CMD ["uvicorn", "--app-dir", ".", "--host", "0.0.0.0", "--port", "14565", "server:app"]
