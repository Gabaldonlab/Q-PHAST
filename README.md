# qCAST

## Installation

To run this software you'll need to execute (from a terminal) the main wrapper script (`main.py` from this repository), which uses a docker image (called `mikischikora/qcast`) with all dependencies. This structure ensures reproducible running across any OS. To install all these things you need to:

- Get the main wrapper script from [here](https://github.com/Gabaldonlab/qCAST/blob/main/main.py). To download it click on 'Raw', then right click on 'Save as...' and save as `main.py`. 

- Install python 3, which is necessary to execute the main wrapper script. In MAC-OS and LINUX systems this should be already installed. For windows you can download it from [here](https://www.python.org/downloads/windows/).

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. For example, 'Docker Desktop' is a good option. Note that to run docker you need to have root (linux / mac) or administrator (windows) permissions.

- Initialize the 'docker daemon' to start using docker. If installed 'Docker Desktop' you can initialize the 'docker daemon' by running the application. In LINUX's terminal you may use `sudo systemctl start docker`.

- Install the `mikischikora/qcast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/qcast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v1`, you should run `docker pull mikischikora/qcast:v1` from the terminal. You can run `docker images` to check that the image is available.

## Running

To obtain the antifungal susceptibility calculations you can follow these steps (the example would work in LINUX):

- Before doing the experiment, design the plate layout:
	
	- Create a folder (for example `strains_and_drugs`) containing two excel tables: `strains.xlsx` should have the 24 strains to be measured and `drugs.xlsx` should contain the drugs and concentrations. [This folder]() contains an example.

	- Obtain the plate layout with `python3 main.py --os linux --module get_plate_layout --docker_image mikischikora/qcast:v1 --input strains_and_drugs --output plate_layout`. This generates a folder (`plate_layout`) that contains two useful excel tables: `plate_layout.xlsx` has a visual representation of how you should position the strains in each plate 

- Run the experiment to obtain images for  (see [protocol]())

Note that the syntax to execute the script `main.py` is slightly different for each OS. You should execute (in the terminal):

- In LINUX: `python3 main.py --os linux <other argments>` 
- In MAC: `python3 main.py --os mac <other argments>` 
- In WINDOWS: `py main.py --os windows <other arguments>`



