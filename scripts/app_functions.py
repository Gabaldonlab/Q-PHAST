#!/usr/bin/env python

# Functions of the image analysis pipeline. This should be imported from the main_env

# imports
import os, sys, time, random, string
import copy as cp
from datetime import date
import pandas as pd
from openpyxl.styles import PatternFill, Font
from openpyxl.styles.borders import Border, Side
import matplotlib.colors as mcolors
import multiprocessing as multiproc

# define dirs
ScriptsDir = "/workdir_app/scripts"
CondaDir =  "/opt/conda"

# general variables
PipelineName = "qCAST"
blank_spot_names = {"h2o", "h20", "water", "empty", "blank"}


# functions
def get_date_and_time_for_print():

    """Gets the date of today"""

    current_day = date.today().strftime("%d/%m/%Y")
    current_time = time.strftime("%H:%M:%S", time.localtime())

    return "[%s, %s]"%(current_day, current_time)

def print_with_runtime(x):

    """prints with runtime info"""

    str_print = "%s %s"%(get_date_and_time_for_print(), x)
    run_cmd_simple("echo '%s'"%str_print)


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
                elif value.lower() in blank_spot_names: color = "white"
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

    """Gets the plate layouts to perform the experiment from the list of strains and drugs. It writes the results into outdir. It generates the 'plate_layout.xlsx' (the picture of the actual table), the 'plate_layout_long.xlsx' (the long format layout)"""

    ##### LOAD AND DEBUG #####

    print_with_runtime("Debugging inputs to design plate layout ...")

    # load 
    df_strains = pd.read_excel(strains_excel)
    df_drugs = pd.read_excel(drugs_excel)

    # debug and format
    if set(df_strains.columns)!={"strain"}: raise ValueError("The strains excel should have these columns: 'strain'")
    if set(df_drugs.columns)!={"plate_batch", "plate", "drug", "concentration"}: raise ValueError("The strains excel should have these columns: 'plate_batch', 'plate', 'drug', 'concentration'")
    if len(df_strains)!=24: raise ValueError("the strains excel should have 24 strains")
    if len(df_drugs)!=len(df_drugs[["plate_batch", "plate"]].drop_duplicates()): raise ValueError("The combination of plate_batch and plate should be unique")
    if len(df_drugs)!=len(df_drugs[["drug", "concentration"]].drop_duplicates()): raise ValueError("The combination of drug and concentration should be unique")

    df_drugs["concentration"] = df_drugs["concentration"].apply(lambda x: str(x).replace(",", ".")) # format as floats the concentration
    for f, function_format in [("plate_batch", str), ("plate", int), ("drug", str), ("concentration", float)]: 
        try: df_drugs[f] = df_drugs[f].apply(function_format)
        except: raise ValueError("The '%s' should be formatable as %s"%(f, function_format))

    if not all([sum((df_drugs.drug==drug) & (df_drugs.concentration==0))==1 for drug in set(df_drugs.drug)]): raise ValueError("all drugs should have a single concentration of 0.0")
    strange_plates = set(df_drugs.plate).difference({1, 2, 3, 4})
    if len(strange_plates)>0: raise ValueError("There are strainge numbers in plate: %s"%strange_plates)

    df_strains["strain"] = df_strains.strain.apply(lambda x: x.rstrip().lstrip())

    ##########################

    ######### CREATE PLATE LAYOUT ##########

    print_with_runtime("Getting plate layout...")

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

    ########## GET THE LONG PLATE LAYOUT #############

    print_with_runtime("Getting plate layout in long format...")

    # change the index
    df_plate_layout.index = list(range(1, 9))

    # create the long df for the plate
    df_plate_layout_long_core = pd.concat([pd.DataFrame({"column":[col]*8, "strain":df_plate_layout[col], "row":list(df_plate_layout.index)}) for col in df_plate_layout.columns]).sort_values(by=["row", "column"]).reset_index(drop=True)

    # create a single df_plate_layout_long with a copy of df_plate_layout_long_core for each combination of plate_batch, plate
    def get_df_plate_layout_long_one_row_df_drugs(r):
        df = cp.deepcopy(df_plate_layout_long_core)
        for f in r.keys(): df[f] = r[f]
        return df
    df_plate_layout_long = pd.concat([get_df_plate_layout_long_one_row_df_drugs(r) for I,r in df_drugs.iterrows()])

    # add the 'bad_spot', which allows tunning
    df_plate_layout_long["bad_spot"] = 'F'

    # checks
    if len(df_plate_layout_long)!=len(df_plate_layout_long.drop_duplicates()): raise ValueError("The df should be unique")

    # save
    plate_layout_long_file = "%s/plate_layout_long.xlsx"%outdir; plate_layout_long_file_tmp = "%s.tmp.xlsx"%plate_layout_long_file
    df_plate_layout_long[["plate_batch", "plate", "row", "column", "strain", "drug", "concentration", "bad_spot"]].reset_index(drop=True).to_excel(plate_layout_long_file_tmp, index=False)
    os.rename(plate_layout_long_file_tmp, plate_layout_long_file)

    ##################################################

def get_fullpath(x):

    """Takes a path and substitutes it bu the full path"""

    # normal
    if x.startswith("/"): return x

    # a ./    
    elif x.startswith("./"): return "%s/%s"%(os.getcwd(), "/".join(x.split("/")[1:]))

    # others (including ../)
    else: return "%s/%s"%(os.getcwd(), x)

def soft_link_files(origin, target):

    """This function takes an origin file and makes it accessible through a link (target)"""

    if file_is_empty(target):

        # rename as full paths
        origin = get_fullpath(origin)
        target = get_fullpath(target)

        # check that the origin exists
        if file_is_empty(origin): raise ValueError("The origin %s should exist"%origin)

        # remove previous lisqnk
        try: run_cmd("rm %s > /dev/null 2>&1"%target)
        except: pass

        soft_linking_std = "%s.softlinking.std"%(target)
        run_cmd("ln -s %s %s > %s 2>&1"%(origin, target, soft_linking_std))
        remove_file(soft_linking_std)

    # check that it worked
    if file_is_empty(target): raise ValueError("The target %s should exist"%target)

def get_dir(filename): return "/".join(filename.split("/")[0:-1])

def get_file(filename): return filename.split("/")[-1]

def process_image_rotation_and_contrast(raw_image, processed_image):

    """Generates a processed image based on raw image that has enhanced contrast and left rotation."""

    print_with_runtime("Improving contrast and rotating image <images>/%s/%s"%(get_dir(processed_image).split("/")[-1], get_file(processed_image)))

    if file_is_empty(processed_image):

        # define the imageJ binary
        imageJ_binary = "/workdir_app/Fiji.app/ImageJ-linux64"

        # define tmp files
        processed_image_tmp = "%s.tmp.%s"%(processed_image, processed_image.split(".")[-1]); remove_file(processed_image_tmp)

        # create a macro to change the image
        lines = ['raw_image = "%s";'%raw_image,
                 'processed_image = "%s";'%processed_image_tmp,
                 'open(raw_image);',
                 'run("Flip Vertically");',
                 'run("Rotate 90 Degrees Left");'
                 'run("Enhance Contrast...", "saturated=0.3");',
                 'saveAs("tif", "%s");'%(processed_image_tmp),
                 'close();'
                ]

        macro_file = "%s.processing_script.ijm"%raw_image
        remove_file(macro_file)
        open(macro_file, "w").write("\n".join(lines)+"\n")

        # run the macro
        imageJ_std = "%s.generating.std"%processed_image_tmp
        run_cmd("%s --headless -macro %s > %s 2>&1"%(imageJ_binary, macro_file, imageJ_std))

        # clean
        for f in [macro_file, imageJ_std]: remove_file(f)

        # keep
        os.rename(processed_image_tmp, processed_image)

def run_analyze_images(plate_layout_file, images_dir, outdir):

    """
    Runs the analyze_images module.
    """

    ##### LOAD AND DEBUG #####

    print_with_runtime("Debugging inputs ...")

    # get layout
    df_plate_layout = pd.read_excel(plate_layout_file)[["plate_batch", "plate", "row", "column", "strain", "drug", "concentration", "bad_spot"]]

    # debugs
    df_plate_layout["concentration"] = df_plate_layout["concentration"].apply(lambda x: str(x).replace(",", ".")) # format as floats the concentration
    df_plate_layout["bad_spot"] = df_plate_layout.bad_spot.apply(lambda x: {"F":False, "T":True}[x])
    for f, function_format in [("plate_batch", str), ("plate", int), ("row", int), ("column", int), ("strain", str), ("drug", str), ("concentration", float), ("bad_spot", bool)]: 
        try: df_plate_layout[f] = df_plate_layout[f].apply(function_format)
        except: raise ValueError("The '%s' should be formatable as %s"%(f, function_format))

    for f, expected_values in [("plate", set(range(1, 5))), ("row", set(range(1, 9))), ("column", set(range(1, 13)))]:
        strange_vals = set(df_plate_layout[f]).difference(expected_values)
        if len(strange_vals)>0: raise ValueError("There are strange values in %s: %s"%(f, strange_vals))

    for plate_batch in set(df_plate_layout.plate_batch):
        if not os.path.isdir("%s/%s"%(images_dir, plate_batch)): raise ValueError("The subfolder <images>/%s should exist"%plate_batch)

    # define the tmpdir
    tmpdir = "%s/tmp"%outdir
    make_folder(tmpdir)

    ##########################

    ##### CREATE THE PROCESSED IMAGES #####

    print_with_runtime("Getting processed images ...")

    # get inputs_fn
    linked_raw_images_dir = "%s/linked_raw_images"%tmpdir; make_folder(linked_raw_images_dir)
    processed_images_dir = "%s/processed_images"%tmpdir; make_folder(processed_images_dir)
    inputs_fn = []

    for plate_batch in sorted(set(df_plate_layout.plate_batch)):

        processed_images_dir_batch = "%s/%s"%(processed_images_dir, plate_batch); make_folder(processed_images_dir_batch)
        linked_raw_images_dir_batch = "%s/%s"%(linked_raw_images_dir, plate_batch); make_folder(linked_raw_images_dir_batch)
        raw_images_dir_batch = "%s/%s"%(images_dir, plate_batch)

        for f in os.listdir(raw_images_dir_batch): 

            # debug non images
            image_endings = {"tiff", "jpg", "jpeg", "png", "tif", "gif"}
            if f.split(".")[-1].lower() not in image_endings or f.startswith("."):
                print_with_runtime("WARNING: File <images>/%s/%s not considered as an image. Note that only images ending with %s (and not starting with a '.') are considered"%(plate_batch, f, image_endings))
                continue

            # get the linked image
            linked_raw_image = "%s/%s"%(linked_raw_images_dir_batch, f)
            processed_image = "%s/%s"%(processed_images_dir_batch, f)  
            soft_link_files("%s/%s"%(raw_images_dir_batch, f), linked_raw_image)

            # keep inputs to process image
            inputs_fn.append((linked_raw_image, processed_image))

    # run in parallel
    threads = multiproc.cpu_count()
    print_with_runtime("Running processing in parallel with %i threads..."%threads)

    with multiproc.Pool() as pool:
        pool.starmap(process_image_rotation_and_contrast, inputs_fn, chunksize=1)
        pool.close()
        pool.terminate()


    #######################################
    
    jhgadjhgdaad


    ###### CLEAN #####

    # keep some files to outdir
    jadhgjhagjdagdahg

    # clean
    delete_folder(tmpdir)

    #################


 