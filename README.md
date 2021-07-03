[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Build Status](https://github.com/alguerre/TrackEditor/actions/workflows/python-app.yml/badge.svg)

# TrackEditor

This is a small tool to edit GPX files. 
There are a number of tools that I periodically need to create my own GPS Tracks and export them in a single GPX file, 
such as: cut, split, reverse, add time, correct elevation... 
and always need more than one single tool to do this!

The single goal of this application is to load, 
visualize and edit your GPX files to create your custom track.

There are amazing tools to create tracks from scratch: komoot, strava... 
But no GPX editor matches my necessities at 100%.

## Repository organization
- **src**: source code
- **docs**: design documents
- **test**: test cases for src modules
- **media**: videos and photos
- Dockerfile
- docker_compose.yml
- requirements.txt: list of python packages dependencies 

## Usage
Launch is automatized by using docker. 
In other case, just go to the src directory and launch:
```
python3 track_editor.py
```

A window in which you can load GPX files will be open, like this:
[![Watch the video](https://img.youtube.com/vi/eIU_mMSm0dg/maxresdefault.jpg)](https://youtu.be/eIU_mMSm0dg)
_(↑ it is a video, click it!)_

## Docker
A Dockerfile is provided to execute the application in a controlled environment. 
It is suggested to be used in a Linux environment, 
since x-server must be configured to get the GUI. 
In order to have visibility of your file system a volume from /home/${USER}/Desktop (_host_) to /home/Desktop (_guest_) is created. 
Procedure:  
```
docker build -t track_editor_im:1.0 .
xhost +
docker-compose up -d
```

**Note:** if docker-compose is launched with **sudo** the docker-compose.yml should be modified.
The ${USER} variable would be set to _root_ which may be confusing when using the volumes.
This can be debug by using _docker-compose config_

[![Watch the video](https://img.youtube.com/vi/F8aCpumdNfI/maxresdefault.jpg)](https://youtu.be/F8aCpumdNfI)
_(↑ it is a video, click it!)_

## License
[MIT](https://choosealicense.com/licenses/mit/)


