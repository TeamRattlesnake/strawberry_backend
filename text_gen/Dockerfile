FROM debian:bullseye-slim

WORKDIR /home

COPY ./requirements.txt /home

COPY ./src /home

RUN apt update && \
    apt -y install python3 python3-pip && \
    pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip3 install -r requirements.txt

CMD ["uvicorn", "--app-dir", "/home", "--host", "0.0.0.0", "--port", "14566", "server:app"]
