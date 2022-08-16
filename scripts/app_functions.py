#!/usr/bin/env python

# Functions of the image analysis pipeline. This should be imported from the main_env

# imports
import os, sys, time, random, string
from datetime import date
import pandas as pd
from openpyxl.styles import PatternFill, Font
from openpyxl.styles.borders import Border, Side
import matplotlib.colors as mcolors

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


def get_matplotlib_color_as_hex(c):

    """Takes a matplotlib color and returns a hex"""

    # find the rgb
    if c in mcolors.BASE_COLORS: return mcolors.rgb2hex(mcolors.BASE_COLORS[c])
    elif c in mcolors.CSS4_COLORS: return mcolors.CSS4_COLORS[c]
    else: raise ValueError("invalid color %s"%c)


def save_colored_plate_layout(df, filename):

    # saves colored plate layout

    # define the tmp
    filename_tmp = "%s.tmp.xlsx"%filename

    # edit the excel
    with pd.ExcelWriter(filename_tmp, engine="openpyxl") as writer:

        # define the sheet_name
        sheet_name = "sheet1"

        # Export DataFrame content
        df.to_excel(writer, sheet_name=sheet_name)

        # define the sheet
        sheet = writer.sheets[sheet_name]   

        # map each col to the fields
        Icol_to_field = dict(zip(range(len(df.columns)) , df.columns))


        # go through each row
        for Irow, row_tuple in enumerate(sheet):

            # define the real Irow
            real_Irow = Irow-1
            if real_Irow<0: continue

            # go through each col
            for Icol, cell in enumerate(row_tuple):

                # define the real Icol
                real_Icol = Icol-1
                if real_Icol<0 or real_Irow<0: continue

                # define the value
                col_name = Icol_to_field[real_Icol]
                value = df[col_name].iloc[real_Irow]

                # define the color
                if value.lower()=="pool": color = "red"
                elif value.lower() in {"h2o", "h20", "water"}: color = "white"
                else:

                    if (real_Icol in {0, 1, 2, 3, 4, 5} and real_Irow in {0, 1, 2, 3}): color = "c"
                    elif (real_Icol in {6, 7, 8, 9, 10, 11} and real_Irow in {4, 5, 6, 7}): color = "c"
                    else: color = "orange"

                # format
                cell.fill = PatternFill("solid", start_color=get_matplotlib_color_as_hex(color)[1:]) # change background color
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style="thin"))
                cell.font = Font(name='Calibri', size=8, bold=False, italic=False, vertAlign=None,  underline='none', strike=False, color=get_matplotlib_color_as_hex("black")[1:])


    os.rename(filename_tmp, filename)

def file_is_empty(path): 
    
    """ask if a file is empty or does not exist """

    if not os.path.isfile(path):
        return_val = True
    elif os.stat(path).st_size==0:
        return_val = True
    else:
        return_val = False
            
    return return_val

def run_get_plate_layout(strains_excel, drugs_excel, outdir):

    """Gets the plate layouts to perform the experiment from the list of strains and drugs. It writes the results into outdir. It generates the 'plate_layout.xlsx' (the picture of the actual table), the 'plate_layout_long.xlsx' (the long format layout) and ... """

    ##### LOAD AND DEBUG #####

    # load 
    df_strains = pd.read_excel(strains_excel)
    df_drugs = pd.read_excel(drugs_excel)

    # debug and format
    if set(df_strains.columns)!={"strain"}: raise ValueError("The strains excel should have these columns: 'strain'")
    if set(df_drugs.columns)!={"plate_batch", "plate", "drug", "concentration"}: raise ValueError("The strains excel should have these columns: 'plate_batch', 'plate', 'drug', 'concentration'")
    if len(df_strains)!=24: raise ValueError("the strains excel should have 24 strains")
    if len(df_drugs)!=len(df_drugs[["plate_batch", "plate"]].drop_duplicates()): raise ValueError("The combination of plate_batch and plate should be unique")

    df_drugs["concentration"] = df_drugs["concentration"].apply(lambda x: str(x).replace(",", ".")) # format as floats the concentration
    for f, function_format in [("plate_batch", str), ("plate", int), ("drug", str), ("concentration", float)]: 
        try: df_drugs[f] = df_drugs[f].apply(function_format)
        except: raise ValueError("The '%s' should be formatable as %s"%(f, function_format))

    strange_plates = set(df_drugs.plate).difference({1, 2, 3, 4})
    if len(strange_plates)>0: raise ValueError("There are strainge numbers in plate: %s"%strange_plates)

    ##########################

    ######### CREATE PLATE LAYOUT ##########

    # create df
    df_plate_layout = pd.DataFrame(index=list("ABCDEFGH"), columns=list(range(1, 13)))

    # define all strains
    all_strains = list(df_strains.strain)

    # fill the first quadrant
    I = 0
    for row in ["A", "B", "C", "D"]:
        for col in range(1, 6+1):
            df_plate_layout.loc[row, col] = all_strains[I]; I+=1

    # fill the second quadrant, mirror of the first
    I = 0
    for row in ["A", "B", "C", "D"]:
        for col in reversed(range(7, 12+1)):
            df_plate_layout.loc[row, col] = all_strains[I]; I+=1

    # fill the thiird quadrant, mirror of the first
    I = 0
    for row in ["E", "F", "G", "H"]:
        for col in reversed(range(1, 6+1)):
            df_plate_layout.loc[row, col] = all_strains[I]; I+=1

    # fill the fourth quadrant, which is the same as the first
    I = 0
    for row in ["E", "F", "G", "H"]:
        for col in range(7, 12+1):
            df_plate_layout.loc[row, col] = all_strains[I]; I+=1

    # save excel colored
    save_colored_plate_layout(df_plate_layout, "%s/plate_layout.xlsx"%outdir)

    ########################################

    # define the plate layout 


    print(df_drugs)
    work_here_on_long_plate_layout


