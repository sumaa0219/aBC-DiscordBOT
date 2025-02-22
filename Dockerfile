FROM python:3.10-slim
USER root

RUN apt-get update
RUN apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN apt install -y git gcc libasound2-dev
RUN git config --global --add safe.directory /abc-discord-bot

RUN mkdir -p /abc-discord-bot
COPY ./requirements.txt /abc-discord-bot
COPY ./.env /abc-discord-bot
COPY ./firebase-adminsdk.json /abc-discord-bot
WORKDIR /abc-discord-bot

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

CMD ["python", "main.py"]