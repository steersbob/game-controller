FROM brewblox/brewblox-service:latest

RUN apt-get update && apt-get install -y xboxdrv

RUN mkdir -p /pkg
COPY ./pkg/* /pkg/

EXPOSE 5000

RUN pip3 install /pkg/* || true \
    && pip3 install game-controller \
    && pip3 show game-controller

ENTRYPOINT ["python3", "-m", "game_controller"]
