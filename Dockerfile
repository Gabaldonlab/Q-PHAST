FROM continuumio/miniconda3:4.12.0

# define the working directory (creates the folder /workdir_app inside the virtual machine)
WORKDIR /workdir_app

# copy all the necessary files into /workdir_app. This is everything from the github repository.
COPY installation installation

# log
RUN echo 'Creating docker image...'

# give permissions
RUN chmod -R 755 /workdir_app

# install mamba to be faster
RUN conda install -y -c conda-forge mamba

# create the main conda env
SHELL ["conda", "run", "-n", "base", "/bin/bash", "-e", "-c"] # run from base env
RUN mamba env create --file ./installation/main_env.yml --name main_env
SHELL ["conda", "run", "-n", "main_env", "/bin/bash", "-e", "-c"] # run from base env
RUN conda install -n main_env -c conda-forge --force-reinstall ld_impl_linux-64 # fix the packages
RUN /workdir_app/installation/install_R_packages_main_env.R # install extra packages

# create the environment to run colonyzer (colonyzer_env)
RUN mamba env create --file ./installation/colonyzer_env.yml --name colonyzer_env
SHELL ["conda", "run", "-n", "colonyzer_env", "/bin/bash", "-e", "-c"] # run from colonyzer_env
RUN pip install Colonyzer2==1.1.22
RUN pip install pygame==1.9.6
RUN pip install sobol==0.9
RUN pip install opencv-python-headless==4.2.0.32

# run commands below in the main_env
SHELL ["conda", "run", "-n", "main_env", "/bin/bash", "-e", "-c"] # run from base env

# install ImageJ
RUN wget https://downloads.imagej.net/fiji/archive/20220414-1745/fiji-linux64.tar.gz > /dev/null 2>&1
RUN tar -xf fiji-linux64.tar.gz && rm fiji-linux64.tar.gz

# give permissions
RUN chmod -R 755 /workdir_app

#### COMMENTS ####

# Create this image with 'docker build -t mikischikora/q-phast:v1 -f ./Dockerfile .'
# Upload to dockerhub with 'docker push mikischikora/q-phast:v1'
# download with 'docker pull mikischikora/q-phast:v1'

##################