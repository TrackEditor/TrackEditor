# Welcome to the TrackEditor Dockerfile
# This has been created to provide a ready environment to launch the app.
# Proposed procedure:
# docker build -t track_editor_im:1.0 .
# xhost +
# docker-compose up -d
#

FROM ubuntu:20.10

# TZ data
RUN export TZ=Europe/Minsk && \
        ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
        echo $TZ > /etc/timezone

# Installation
RUN apt-get update

RUN apt-get install -y \
        python3 \
        python3-pip \
        python3-tk

ADD ./requirements.txt /
RUN pip install -r requirements.txt

# Prepare file system
WORKDIR /home/TrackEditor
COPY src /home/TrackEditor/src

# Launch app
CMD ["/bin/python3", "/home/TrackEditor/src/track_editor.py"]
                                                    