FROM python:3
WORKDIR /python

# init
RUN apt-get update \
  && apt-get install -y locales \
  && locale-gen ja_JP.UTF-8 \
  && echo "export LANG=ja_JP.UTF-8" >> ~/.bashrc

# pip upgrade
RUN pip install --upgrade pip
RUN pip install uv
