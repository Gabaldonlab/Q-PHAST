# qCAST

This is a pipeline to analyze images and 

## Installation

To run this software you'll need to execute (from a terminal) the main wrapper script (`main.py` from this repository), which uses a docker image (called `mikischikora/qcast`) with all dependencies. This structure ensures reproducible running across any OS. To get all these things you need to install different things depending in you operating system:

### Linux installation

- Get the main wrapper script from [here](https://github.com/Gabaldonlab/qCAST/blob/main/main.py). To download it click on 'Raw', then right click on 'Save as...' and save as `main.py`.

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. Note that to run docker you need to have root permissions.

- Initialize the 'docker daemon' to start using docker with `sudo systemctl start docker` from the terminal.

- Install the `mikischikora/qcast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/qcast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v1`, you should run `docker pull mikischikora/qcast:v1` from the terminal. You can run `docker images` to check that the image is available.


### Mac installation

- Get the main wrapper script from [here](https://github.com/Gabaldonlab/qCAST/blob/main/main.py). To download it click on 'Raw', then right click on 'Save as...' and save as `main.py`.

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. 'Docker Desktop' is a good option. Note that to run docker you need to have root permissions.

- Install XQUARTZ (from [here](https://www.xquartz.org/)), essential to run docker here. To make XQUARTZ compatible with this software you have to run xquartz, go to 'Preferences', then 'Security' and click 'Allow connections from network clients'.

- Initialize the 'docker daemon' to start using docker by running 'Docker Desktop'.

- Install the `mikischikora/qcast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/qcast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v1`, you should run `docker pull mikischikora/qcast:v1` from the terminal. You can run `docker images` to check that the image is available.


### Windows installation

- Get the main wrapper script from [here](https://github.com/Gabaldonlab/qCAST/blob/main/main.py). To download it click on 'Raw', then right click on 'Save as...' and save as `main.py`.

- Install python 3 [here](https://www.python.org/downloads/windows/), which is necessary to execute the main wrapper script For windows you can download it from [here](https://www.python.org/downloads/windows/).

- Install docker, which is necessary to run the docker image. You can [find here](https://docs.docker.com/engine/install/) the installation information. 'Docker Desktop' is a good option. Note that to run docker you need to have administrator permissions.

- Install the VcXsrv XLauch app (from [here](https://sourceforge.net/projects/vcxsrv/)), which is necessary to run docker here.

- Initialize the 'docker daemon' to start using docker by running 'Docker Desktop'.

- Install the `mikischikora/qcast` docker image, available [here](https://hub.docker.com/repository/docker/mikischikora/qcast). You can use whatever tag (or version) you need. For example, if you want to install tag (version) `v1`, you should run `docker pull mikischikora/qcast:v1` from the terminal. You can run `docker images` to check that the image is available.



## Running

To illustrate how you can run this method we will use an example experiment in which we measured antifungal susceptibility to anidulafungin (ANI) and fluconazole (FLZ) in 24 strains and 8 drug concentrations. The images and input files can be found [here](https://github.com/Gabaldonlab/qCAST/tree/main/testing/testing_plates_202108), and you may check them to understand how to design the input files. You may follow these steps to get the calculations (this would work in LINUX for the image `mikischikora/qcast:v1`):

- Before doing the experiment, design the plate layout:

	- Create an excel table with the 24 strains to be measured (called `strains.xlsx` in the example). This may contain empty wells (named 'H2O') or wells with a pool of strains that will grow in all assayed conditions (named 'Pool').

	- Create an excel table with the drugs (column 'drug') and concentrations (column 'concentration') to be assayed (called `drugs.xlsx` in the example). The drugs table should also contain two extra columns:

		- The 'plate_batch' column should be a unique identifier for each batch of plates that will be run in a single scanner.

		- The 'plate' column should be a number between 1 and 4 indicating which plate in the batch has a given drug and concentration. Below you can see which number corresponds to each plate:

		<img src="https://github.com/Gabaldonlab/qCAST/blob/main/misc/example_image.jpeg" width="100%" height="100%">

	- Obtain the plate layout with `python3 main.py --os linux --module get_plate_layout --docker_image mikischikora/qcast:v1 --strains strains.xlsx --drugs drugs.xlsx --output outdir/plate_layout`. This generates a folder (`outdir/plate_layout`) that contains two useful excel tables: `plate_layout.xlsx` has a visual representation of how you should position the strains in each plate and `plate_layout_long.xlsx` is a long table that is required to further analyze the data.

- Run the experiment to obtain images for each plate setting the strains as in `outdir/plate_layout/plate_layout.xlsx` (see [protocol]()). Save them into a folder (called `raw_images` in the example) containing one subfolder for each batch of plates (corresponding to the column 'plate_batch' from `drugs.xslx`). The filename of image should have a timestamp with a 'YYYYMMDD_HHMM' format (i.e. `20210814_0011.tif`, `_0_20210814_0011.tif` or `2021_08_14_00_11.tif`).

-




Note that the syntax to execute the script `main.py` is slightly different for each OS. You should execute (in the terminal):

- In LINUX: `python3 main.py --os linux <other argments>`
- In MAC: `python3 main.py --os mac <other argments>`
- In WINDOWS: `py main.py --os windows <other arguments>`

If you are running on Windows you also need to run the XLauch application (with all default parameters) BEFORE running this pipeline.


## FAQs

### What can I do if I get an error?

[Open an issue](https://github.com/Gabaldonlab/qCAST/issues) and describe your problem. We will try to solve it as soon as possible.
