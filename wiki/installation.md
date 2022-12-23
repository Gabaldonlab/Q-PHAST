# Installation

To run this software you'll need to execute (from a terminal) the main wrapper script (`main.py` from this repository), which uses a docker image (called `mikischikora/qcast`) with all dependencies. This structure ensures reproducible running across any OS. To get all these things you need to:

- Download the content of this repository [here](https://github.com/Gabaldonlab/qCAST/archive/refs/heads/main.zip). This contains the `main.py` wrapper script and its dependencies (in the `scripts` folder).

- In WINDOWS, install python 3 from [here](https://www.python.org/downloads/windows/), which is necessary to execute the main wrapper script. Make sure that you click on the 'add python to PATH' box during installation. Note that python 3 should already be installed in MAC/LINUX.

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. Note that to run docker you need to have root/administrator permissions. For MAC/WINDOWS 'Docker Desktop' is a good option.

- Initialize the 'docker daemon' to start using docker. You can do this by either running `sudo systemctl start docker` from the terminal (LINUX) or starting 'Docker Desktop' (WINDOWS/MAC).

- Install the `mikischikora/qcast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/qcast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v0.1`, you should run `docker pull mikischikora/qcast:v0.1` from the terminal. You can run `docker images` from the terminal to check that the image is available.
