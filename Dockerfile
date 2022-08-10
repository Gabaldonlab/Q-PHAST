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
RUN source /opt/conda/etc/profile.d/conda.sh  && conda activate colonyzer_env && pip install Colonyzer2==1.1.22
RUN source /opt/conda/etc/profile.d/conda.sh  && conda activate colonyzer_env && pip install pygame==1.9.6
RUN source /opt/conda/etc/profile.d/conda.sh  && conda activate colonyzer_env && pip install sobol==0.9
RUN source /opt/conda/etc/profile.d/conda.sh  && conda activate colonyzer_env && which pip

# create the main conda env
RUN mamba env create --file ./installation/main_env.yml --name main_env
RUN conda install -n main_env -c conda-forge --force-reinstall ld_impl_linux-64 # fix the packages
RUN source /opt/conda/etc/profile.d/conda.sh  && conda activate main_env && /workdir_app/installation/install_R_packages_main_env.R # install extra packages

# run the application
CMD source /opt/conda/etc/profile.d/conda.sh  && conda activate main_env > /dev/null 2>&1 && /workdir_app/scripts/run_app.py

#### COMMENTS ####

# Create this image with 'docker build -t qcast:v0.1 -f ./Dockerfile .'

# Run with 'docker run qcast:v0.1'
# Debug run with 'docker run -v /home/mschikora/samba/scripts/qCAST/scripts:/workdir_app/scripts qcast:v0.1' # developing scripts
# Debug run with 'docker run  -e DISPLAY=$DISPLAY  -v /tmp/.X11-unix:/tmp/.X11-unix:rw -v $(pwd)/app:/app  -v /home/mschikora/samba/scripts/qCAST/scripts:/workdir_app/scripts   qcast:v0.1' # developing scripts




# Run with display 'docker run -u=$(id -u $USER):$(id -g $USER) -e DISPLAY=$DISPLAY -v /home/mschikora/samba/scripts/qCAST/scripts:/workdir_app/scripts --rm qcast:v0.1'

# docker run -u=$(id -u $USER):$(id -g $USER) -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:rw -v $(pwd)/app:/app --rm tkinter_in_docker


# -v $PWD/docker/perSVade_testing_outputs_$tag:/perSVade/installation/test_installation/testing_outputs


##################