FROM continuumio/miniconda3:4.8.2

# define the working directory (creates the folder /workdir_app inside the virtual machine)
WORKDIR /workdir_app

# copy all the necessary files into /workdir_app. This is everything from the github repository.
# COPY . . # debug commenting

# log
RUN echo 'Creating docker image...'

# give permissions
RUN chmod -R 755 /workdir_app

# install mamba to be faster
RUN conda install -y -c conda-forge mamba=0.15.3

# create the main conda env
# RUN mamba env create --name main_env
RUN mamba create --name main_env

# create the environment to run colonyzer (colonyzer_env)
RUN mamba create --name colonyzer_env -y python=2.7 matplotlib pandas scipy pillow opencv # create environments with packages
SHELL ["conda", "run", "-n", "colonyzer_env", "/bin/bash", "-e", "-c"] # make all commands below to be run under the colonyzer_env
RUN pip install Colonyzer2
RUN pip install pygame
RUN pip install sobol

# run remaing commands under the main env
SHELL ["conda", "run", "-n", "main_env", "/bin/bash", "-e", "-c"] # make all commands below to be run under the colonyzer_env

# run the application
CMD /workdir_app/scripts/run_app.py
# CMD pcmanfm

# log
RUN echo 'Docker image successfully built!'



#### COMMENTS ####

# Create this image with 'docker build -t qcast:v0.1 -f ./Dockerfile .'
# Run with 'docker run qcast:v0.1'
# Debug run with 'docker run -v /home/mschikora/samba/scripts/qCAST/scripts:/workdir_app/scripts -v /:/host_machine_root qcast:v0.1' # developing scripts

# Run with display 'docker run -u=$(id -u $USER):$(id -g $USER) -e DISPLAY=$DISPLAY -v /home/mschikora/samba/scripts/qCAST/scripts:/workdir_app/scripts --rm qcast:v0.1'


# -v $PWD/docker/perSVade_testing_outputs_$tag:/perSVade/installation/test_installation/testing_outputs


##################