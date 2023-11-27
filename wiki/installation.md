## Installation

To run this software you'll need to execute (from a terminal) the main wrapper script (`main.py` from this repository), which uses a docker image (called `mikischikora/q-phast`) with all software dependencies. You can think of this docker image as a virtual machine with the software's environment, which enables reproducible running in any OS. To get all these things you need to:

- Download the content of this repository [here](https://github.com/Gabaldonlab/Q-PHAST/archive/refs/heads/main.zip). This will download a `.zip` file, which you should uncompress, generating the `Q-PHAST` folder that contains the `main.py` wrapper script and its dependencies (in the `scripts` folder). 

- Install `python` (version 3), and the python packages `tk`, `pandas` and `pillow`, which are necessary to run `main.py`. One easy way to install all these is by using Anaconda, which can be downloaded and installed from [here](https://www.anaconda.com/download). Once installed, follow these steps:

  - Open Anaconda Navigator, and go to 'Environments'.

  - Select the environment where you want to install python and its dependencies. It can be the 'base' environment or a new one that you create.

  - Install the packages `python`, `tk`, `pandas` and `pillow`. For this 1) select 'All' in the drop-down menu, 2) use the 'Search Packages' tab to find each package, 3) click on the packages to install and 4) click on 'apply' to install them. Note that some (or all) of thes packages may already be installed (they'd have the green tick if so), which is OK.

  - Regarding package versions, most versions will work. The only critical thing is that you install some python 3 version. For reference, we tested Q-PHAST in LINUX (with `python==3.7.3`, `tk==8.6.8`, `pandas==0.24.2` and `pillow==5.4.1`), WINDOWS (with `python==`, `tk==`, `pandas==` and `pillow==`) and MAC (with `python==`, `tk==`, `pandas==` and `pillow==`)

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. Note that to run docker you need to have root/administrator permissions. For MAC/WINDOWS 'Docker Desktop' is a good option. Note that you need administrator (WINDOWS) or root (LINUX / MAC) permissions to run Docker.

- Initialize the 'docker daemon' to start using docker. You can do this by either running `sudo systemctl start docker` from the terminal (LINUX) or starting the 'Docker Desktop' app (WINDOWS/MAC).

- Install the `mikischikora/q-phast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/q-phast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v1`, you should run `docker pull mikischikora/q-phast:v1` from the terminal. You can run `docker images` from the terminal to check that the image is available. If you are on WINOWS / MAC, you can use the Docker Desktop app to install the `mikischikora/q-phast:v1` image.

Once you install all these dependencies, you can run the pipeline following [these instructions](https://github.com/Gabaldonlab/Q-PHAST/blob/main/wiki/running.md).