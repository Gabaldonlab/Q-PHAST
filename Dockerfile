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
RUN conda install -n main_env -c conda-forge --force-reinstall ld_impl_linux-64 # fix the packages
RUN /workdir_app/installation/install_R_packages_main_env.R # install extra packages

# run the application
CMD source /opt/conda/etc/profile.d/conda.sh > /dev/null 2>&1 && conda activate main_env > /dev/null 2>&1 && /workdir_app/scripts/run_app.py

#### COMMENTS ####

# Create this image with 'docker build -t mikischikora/qcast:v0.1 -f ./Dockerfile .'

# Upload to dockerhub with 'docker push mikischikora/qcast:v0.1'

# download with 'docker pull mikischikora/qcast:v0.1'

# echo "SUCCESS: You could create the docker image of perSVade. You can publish this image with docker push mikischikora/persvade:$tag. You can then create a singularity image with singularity build --docker-login ./mikischikora_persvade_$tag.sif docker://mikischikora/persvade:$tag"


# Run with 'xhost +local:docker && docker run -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v $(pwd)/scripts:/workdir_app/scripts --rm mikischikora/qcast:v0.1' # tested on opensuse



##################