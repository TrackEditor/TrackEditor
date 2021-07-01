# Welcome to the TrackEditor Dockerfile
# This has been created to provide a ready environment to launch the app.
# Proposed procedure:
# sudo docker build -t track_editor_im:1.0 .
# xhost +
# sudo docker run \ 
#    --rm \ 
#    -e DISPLAY=$DISPLAY \
#    -v /tmp/.X11-unix:/tmp/.X11-unix  \
#    -v /home/$USER/Desktop:/home/Desktop \
#    track_editor_im:1.0 
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

RUN pip3 install \
        numpy==1.20.1 \
        matplotlib==3.3.4 \
        pandas==1.2.2 \
        urllib3==1.25.9 \
        geopy==2.1.0 \
        gpxpy==1.4.2

# Prepare file system
WORKDIR /home/TrackEditor
COPY src /home/TrackEditor/src

# Launch app
CMD ["/bin/python3", "/home/TrackEditor/src/track_editor.py"]
