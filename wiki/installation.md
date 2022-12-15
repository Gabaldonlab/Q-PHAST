# Installation

To run this software you'll need to execute (from a terminal) the main wrapper script (`main.py` from this repository), which uses a docker image (called `mikischikora/qcast`) with all dependencies. This structure ensures reproducible running across any OS. To get all these things you need to install different things depending in you operating system:

## Linux installation

- Download the content of this repository [here](https://github.com/Gabaldonlab/qCAST/archive/refs/heads/main.zip). This contains the `main.py` wrapper script and its dependencies (in the `scripts` folder).

- Optional: if the python dependencies 'pillow' and/or 'Tk-inter' are not installed, install them with `pip install Pillow` and/or `pip install tk`.

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. Note that to run docker you need to have root permissions.

- Initialize the 'docker daemon' to start using docker with `sudo systemctl start docker` from the terminal.

- Install the `mikischikora/qcast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/qcast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v0.1`, you should run `docker pull mikischikora/qcast:v0.1` from the terminal. You can run `docker images` to check that the image is available.


## Mac installation

- Download the content of this repository [here](https://github.com/Gabaldonlab/qCAST/archive/refs/heads/main.zip). This contains the `main.py` wrapper script and its dependencies (in the `scripts` folder).

- Optional: if the python dependencies 'pillow' and/or 'Tk-inter' are not installed, install them with `pip install Pillow` and/or `pip install tk`.

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. 'Docker Desktop' is a good option. Note that to run docker you need to have root permissions.

- Install XQUARTZ (from [here](https://www.xquartz.org/)), essential to run docker here. To make XQUARTZ compatible with this software you have to run xquartz, go to 'Preferences', then 'Security' and click 'Allow connections from network clients'.

- Initialize the 'docker daemon' to start using docker by running 'Docker Desktop'.

- Install the `mikischikora/qcast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/qcast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v0.1`, you should run `docker pull mikischikora/qcast:v0.1` from the terminal. You can run `docker images` to check that the image is available.


## Windows installation

- Download the content of this repository [here](https://github.com/Gabaldonlab/qCAST/archive/refs/heads/main.zip). This contains the `main.py` wrapper script and its dependencies (in the `scripts` folder).

- Install python 3 [here](https://www.python.org/downloads/windows/), which is necessary to execute the main wrapper script For windows you can download it from [here](https://www.python.org/downloads/windows/).

- Optional: if the python dependencies 'pillow' and/or 'Tk-inter' are not installed, install them with `pip install Pillow` and/or `pip install tk`.

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. 'Docker Desktop' is a good option. Note that to run docker you need to have administrator permissions.

- Install the VcXsrv XLauch app (from [here](https://sourceforge.net/projects/vcxsrv/)), which is necessary to run docker here.

- Initialize the 'docker daemon' to start using docker by running 'Docker Desktop'.

- Install the `mikischikora/qcast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/qcast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v0.1`, you should run `docker pull mikischikora/qcast:v0.1` from the terminal. You can run `docker images` to check that the image is available.
