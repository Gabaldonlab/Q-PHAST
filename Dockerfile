FROM continuumio/miniconda3:4.12.0

# define the working directory (creates the folder /workdir_app inside the virtual machine)
WORKDIR /workdir_app

# copy all the necessary files into /workdir_app. This is everything from the github repository.
# COPY . .
COPY installation installation

# log
RUN echo 'Creating docker image...'

# give permissions
RUN chmod -R 755 /workdir_app

# install mamba to be faster
# RUN conda install -y -c conda-forge mamba=0.15.3
RUN conda install -y -c conda-forge mamba

# create the environment to run colonyzer (colonyzer_env)
RUN mamba env create --file ./installation/colonyzer_env.yml --name colonyzer_env
SHELL ["conda", "run", "-n", "colonyzer_env", "/bin/bash", "-e", "-c"] # run from colonyzer_env
RUN pip install Colonyzer2==1.1.22
RUN pip install pygame==1.9.6
RUN pip install sobol==0.9

# create the main conda env
SHELL ["conda", "run", "-n", "base", "/bin/bash", "-e", "-c"] # run from base env
RUN mamba env create --file ./installation/main_env.yml --name main_env
SHELL ["conda", "run", "-n", "main_env", "/bin/bash", "-e", "-c"] # run from base env
RUN mamba install -n main_env -y -c anaconda openpyxl=3.0.9 
RUN conda install -n main_env -c conda-forge --force-reinstall ld_impl_linux-64 # fix the packages
RUN /workdir_app/installation/install_R_packages_main_env.R # install extra packages

# install ImageJ
RUN wget https://downloads.imagej.net/fiji/archive/20220414-1745/fiji-linux64.tar.gz
RUN tar -xf fiji-linux64.tar.gz && rm fiji-linux64.tar.gz

# give permissions
RUN chmod -R 755 /workdir_app

#### COMMENTS ####

# Create this image with 'docker build -t mikischikora/qcast:v0.1 -f ./Dockerfile .'
# Upload to dockerhub with 'docker push mikischikora/qcast:v0.1'
# download with 'docker pull mikischikora/qcast:v0.1'

##################