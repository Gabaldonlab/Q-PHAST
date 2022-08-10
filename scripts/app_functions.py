#!/usr/bin/env python

# Functions of the image analysis pipeline. This should be imported from the main_env

# imports
import os, sys, time, random, string
from datetime import date

# define dirs
ScriptsDir = "/workdir_app/scripts"
CondaDir =  "/opt/conda"

# general variables
PipelineName = "qCAST"

# functions
def get_date_and_time_for_print():

    """Gets the date of today"""

    current_day = date.today().strftime("%d/%m/%Y")
    current_time = time.strftime("%H:%M:%S", time.localtime())

    return "[%s, %s]"%(current_day, current_time)

def print_with_runtime(x):

    """prints with runtime info"""

    str_print = "%s %s"%(get_date_and_time_for_print(), x)
    run_cmd_simple("echo %s"%str_print)


def id_generator(size=10, chars=string.ascii_uppercase + string.digits, already_existing_ids=set()):

    """ already_existing_ids is a set that indicates whihc IDs can't be picked """

    ID = ''.join(random.choice(chars) for _ in range(size))
    while ID in already_existing_ids:
        ID = ''.join(random.choice(chars) for _ in range(size))

    return ID

def remove_file(f):

    if os.path.isfile(f): 

        try: run_cmd("rm %s > /dev/null 2>&1"%f)
        except: pass

def delete_folder(f):

    if os.path.isdir(f): shutil.rmtree(f)


def make_folder(f):

    if not os.path.isdir(f): os.mkdir(f)

def delete_file_or_folder(f):

    """Takes a path and removes it"""

    if os.path.isdir(f): shutil.rmtree(f)
    if os.path.isfile(f): os.unlink(f)

def run_cmd_simple(cmd):

    """Runs os.system in cmd"""

    out_stat = os.system(cmd) 
    if out_stat!=0: raise ValueError("\n%s\n did not finish correctly. Out status: %i"%(cmd, out_stat))


def run_cmd(cmd, env='main_env'):

    """This function runs a cmd with a given env"""

    # define the cmds
    SOURCE_CONDA_CMD = "source %s/etc/profile.d/conda.sh > /dev/null 2>&1"%CondaDir
    cmd_prefix = "%s && conda activate %s > /dev/null 2>&1 &&"%(SOURCE_CONDA_CMD, env)

    # define the cmd
    cmd_to_run = "%s %s"%(cmd_prefix, cmd)

    # define a tmpdir to write the bash scripts
    tmpdir = '/workdir_app/.tmpdir_cmds'
    make_folder(tmpdir)

    # define a bash script to print the cmd and run
    nchars = 15
    already_existing_ids = {f.split(".sh")[0] for f in os.listdir(tmpdir) if len(f)==(nchars+3) and f.endswith(".sh")} # +3 for the ".sh"
    bash_script = "%s/%s.sh"%(tmpdir, id_generator(size=nchars, already_existing_ids=already_existing_ids, chars=string.ascii_uppercase))

    # write the bash script
    open(bash_script, "w").write(cmd_to_run+"\n")

    # run
    out_stat = os.system("bash %s"%bash_script) 
    if out_stat!=0: raise ValueError("\n%s\n did not finish correctly. Out status: %i"%(cmd_to_run, out_stat))

    # remove the script
    run_cmd_simple("rm %s"%bash_script)