# TrackEditor

This is a small tool to edit GPX files. 
There are a number of tools that I periodically need to create my own GPS Tracks and export them in a single GPX file, 
such as: cut, split, reverse, add time, correct elevation... 
and always need more than one single tool to do this!

The single goal of this application is to load, 
visualize and edit your GPX files to create your custom track.

There are amazing tools to create tracks from scratch: komoot, strava... 
But any GPX editor which matches my necessities at 100%.

## Repository organization
- **src**: source code
- **docs**: design documents
- **test**: test cases for src modules
- Dockerfile

## Docker
A Dockerfile is provided to execute the application in a controlled environment. 
It is suggested to be used in a Linux environment, 
since x-server must be configured to get the GUI. 
An ephemeral container is proposed, 
which only exists while the application is being used.
Desktop from current launcher is linked to a container /home/Desktop directory.
Procedure:  
```
sudo docker build -t track_editor_im:1.0 .
xhost +
sudo docker run \ 
    --rm \ 
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix  \
    -v /home/$USER/Desktop:/home/Desktop \
    -v /var/log:/home/TrackEditor/log \
    track_editor_im:1.0
```


## Usage
Launch is automatized by using docker. 
In other case, just go to the src directory and launch:
```
python3 track_editor.py
```

A window in which you can load GPX files will be open, like this:
![alt text](https://github.com/alguerre/TrackEditor/blob/master/docs/using_sample.png?raw=true)



## License
[MIT](https://choosealicense.com/licenses/mit/)


