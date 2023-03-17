#!/usr/bin/env python

# Functions of the image analysis pipeline. This should be imported from the main_env

# imports
import os, sys, time, random, string, shutil, math, itertools, pickle, scipy, zipfile, matplotlib
import copy as cp
from datetime import date
import pandas as pd
from openpyxl.styles import PatternFill, Font
from openpyxl.styles.borders import Border, Side
import matplotlib.colors as mcolors
import multiprocessing as multiproc
import numpy as np
from PIL import Image as PIL_Image
from PIL import ImageEnhance, ImageDraw, ImageFont, ImageColor
import PIL
from sklearn.metrics import auc as sklearn_auc
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from scipy.cluster import hierarchy
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
import traceback

# set parms for matplotlib
#plt.rcParams['font.family'] = 'Arial'
matplotlib.use('Agg')

# define dirs
ScriptsDir = "/workdir_app/scripts"
CondaDir =  "/opt/conda"

# general variables
PipelineName = "Q-PHAST"
blank_spot_names = {"h2o", "h20", "water", "empty", "blank"}
allowed_image_endings = {"tiff", "jpg", "jpeg", "png", "tif", "gif"}
parms_colonyzer = ("greenlab", "lc", "diffims")

# functions
def get_date_and_time_for_print():

    """Gets the date of today"""

    current_day = date.today().strftime("%d/%m/%Y")
    current_time = time.strftime("%H:%M:%S", time.localtime())

    return "[%s, %s]"%(current_day, current_time)

def print_with_runtime(x):

    """prints with runtime info"""

    #str_print = "%s %s"%(get_date_and_time_for_print(), x)
    #run_cmd_simple("echo '%s'"%str_print)
    print(x) # this does not include the time, which is good because docker does not have the correct time


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
    os.makedirs(tmpdir, exist_ok=True)

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

    #print_with_runtime("Debugging inputs to design plate layout ...")

    # load 
    df_strains = pd.read_excel(strains_excel)
    df_drugs = pd.read_excel(drugs_excel)

    # debug and format
    if set(df_strains.columns)!={"strain"}: raise ValueError("The strains excel should have these columns: 'strain'")
    if set(df_drugs.columns)!={"plate_batch", "plate", "drug", "concentration"}: raise ValueError("The strains excel should have these columns: 'plate_batch', 'plate', 'drug', 'concentration'")
    if len(df_strains)!=24: raise ValueError("the strains excel should have 24 strains")
    if len(df_drugs)!=len(df_drugs[["plate_batch", "plate"]].drop_duplicates()): raise ValueError("The combination of plate_batch and plate should be unique")
    if len(df_drugs)!=len(df_drugs[["drug", "concentration"]].drop_duplicates()): raise ValueError("The combination of drug and concentration should be unique")

    df_strains["strain"] = df_strains.strain.apply(lambda s: s.rstrip())    
    for strain in set(df_strains.strain):
        if " " in strain: raise ValueError("The strain names should not have spaces. '%s' is incorrect"%strain)

    for k in df_drugs.keys():
        if any(pd.isna(df_drugs[k])): raise ValueError("The drugs table should be a perfect rectangle. Column %s has spaces"%k)

    for k in df_strains.keys():
        if any(pd.isna(df_strains[k])): raise ValueError("The strains table should be a perfect rectangle. Column %s has spaces"%k)

    df_drugs["concentration"] = df_drugs["concentration"].apply(lambda x: str(x).replace(",", ".")) # format as floats the concentration
    for f, function_format in [("plate_batch", str), ("plate", int), ("drug", str), ("concentration", float)]: 
        try: df_drugs[f] = df_drugs[f].apply(function_format)
        except: raise ValueError("The '%s' should be formatable as %s"%(f, function_format))

    if sum(df_drugs.concentration==0)!=1: raise ValueError("There should be only one plate with a concentration of 0.0")
    strange_plates = set(df_drugs.plate).difference({1, 2, 3, 4})
    if len(strange_plates)>0: raise ValueError("There are strainge numbers in plate: %s"%strange_plates)

    df_strains["strain"] = df_strains.strain.apply(lambda x: x.rstrip().lstrip())

    ##########################

    ######### CREATE PLATE LAYOUT ##########

    #print_with_runtime("Getting plate layout...")

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

    #print_with_runtime("Getting plate layout in long format...")

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

def process_image_rotation_and_contrast(Iimage, nimages, raw_image, processed_image):

    """Generates a processed image based on raw image that has enhanced contrast and left rotation."""

    # log
    image_short_name = "<images>/%s/%s"%(get_dir(raw_image).split("/")[-1], get_file(raw_image))
    #print_with_runtime("Improving contrast and rotating image %i/%i: %s"%(Iimage, nimages, image_short_name))

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

        # check that the macro ended well
        error_lines = [l for l in open(imageJ_std, "r").readlines() if any([x in l.lower() for x in {"error", "fatal"}])]
        if len(error_lines)>0: 
            raise ValueError("imageJ did not work on '%s'. Check '%s' to see what happened."%(image_short_name, imageJ_std.replace("/output", "<output dir>"))); 

        # clean
        for f in [macro_file, imageJ_std]: remove_file(f)

        # keep
        os.rename(processed_image_tmp, processed_image)


def process_image_rotation_and_contrast_all_images_batch(Ibatch, nbatches, raw_outdir, processed_outdir, plate_batch, expected_images, image_ending, enhance_image_contrast):

    """Runs the processing of images for all images in one batch"""

    # log
    if enhance_image_contrast is True: log_txt = "Increasing contrast and processing images"
    elif enhance_image_contrast is False: log_txt = "Processing images"
    log_txt += " for batch %i/%i: %s"%(Ibatch, nbatches, plate_batch)
    print_with_runtime(log_txt)

    # if there are no processed files
    if not os.path.isdir(processed_outdir): 

        # clean
        delete_folder(processed_outdir)

        # make tmp folder where to save things folder
        processed_outdir_tmp = "%s_tmp"%processed_outdir
        delete_folder(processed_outdir_tmp); make_folder(processed_outdir_tmp)

        # define the imageJ binary
        imageJ_binary = "/workdir_app/Fiji.app/ImageJ-linux64"

        # define the contrast as based on enhance_image_contrast
        if enhance_image_contrast is True: line_contrast = 'run("Enhance Contrast...", "saturated=0.3");',
        else: line_contrast = ''

        # create a macro to change the image
        lines = [
                 'input_dir = "%s/";'%(raw_outdir),
                 'list_images = getFileList(input_dir);',
                 'setBatchMode(true);',
                 'for (i=0; i<list_images.length; i++) {',
                 '  open(input_dir+list_images[i]);'
                 '  run("Flip Vertically");',
                 '  run("Rotate 90 Degrees Left");',
                 '  %s'%line_contrast,
                 '  processed_image_name = "%s/" + replace(list_images[i], "%s", "tif");'%(processed_outdir_tmp, image_ending),
                 '  print(processed_image_name);',
                 '  saveAs("tif", processed_image_name);',
                 '  close();',
                 '}',
                 'setBatchMode(false);'
                ]

        macro_file = "%s.processing_script.ijm"%raw_outdir
        remove_file(macro_file)
        open(macro_file, "w").write("\n".join(lines)+"\n")

        # run the macro
        imageJ_std = "%s.generating.std"%processed_outdir_tmp
        run_cmd("%s --headless -macro %s > %s 2>&1"%(imageJ_binary, macro_file, imageJ_std))

        # check that the macro ended well
        error_lines = [l for l in open(imageJ_std, "r").readlines() if any([x in l.lower() for x in {"error", "fatal"}])]
        if len(error_lines)>0: 
            raise ValueError("imageJ did not work on '%s'. Check '%s' to see what happened."%(plate_batch, imageJ_std.replace("/output", "<output dir>"))); 

        # clean
        for f in [macro_file, imageJ_std]: remove_file(f)

        # at the end save
        os.rename(processed_outdir_tmp, processed_outdir)

    # check that all images are there
    missing_images = set(expected_images).difference(set(os.listdir(processed_outdir)))
    if len(missing_images)>0: raise ValueError("There are missing images: %s"%missing_images)

    for f in expected_images: 
        if file_is_empty("%s/%s"%(processed_outdir, f)): raise ValueError("image %s should exist"%f)

def process_image_rotation_and_contrast_PIL(Iimage, nimages, raw_image, processed_image):

    """Generates a processed image based on raw image that has enhanced contrast and left rotation. This is like process_image_rotation_and_contrast (this is what we originally did) but with PIL. This does not work as well as ImageJ."""

    # log
    image_short_name = "<images>/%s/%s"%(get_dir(raw_image).split("/")[-1], get_file(raw_image))
    #print_with_runtime("Improving contrast and rotating image %i/%i: %s"%(Iimage, nimages, image_short_name))

    if file_is_empty(processed_image):

        # define tmp files
        processed_image_tmp = "%s.tmp.%s"%(processed_image, processed_image.split(".")[-1]); remove_file(processed_image_tmp)

        # load image
        image_object = PIL_Image.open(raw_image)

        # rotate 90 deg counter clockwise
        image_object = image_object.rotate(90, PIL.Image.NEAREST, expand = 1)

        # enhance contrast (saturated=0.3)

        #image brightness enhancer
        enhancer = ImageEnhance.Contrast(image_object)
        image_object_processed = enhancer.enhance(10)

        # save
        image_object_processed.save(processed_image_tmp)
        os.rename(processed_image_tmp, processed_image)

        # keep
        os.rename(processed_image_tmp, processed_image)


def get_yyyymmddhhmm_tuple_one_image_name(filename):

    """Returns a tuple with the yyyy, mm, dd, hh, mm for one image name"""

    # get the numbers_str with all images
    numbers_str = ""
    recording_numbers = False

    for x in get_file(filename):

        # start recording once you find some number
        if recording_numbers is False and x.isdigit() and int(x)>0: recording_numbers = True

        # if you are recoding
        if recording_numbers is True and x.isdigit(): numbers_str += x

    # check
    if len(numbers_str)!=12: raise ValueError("We can't define a YYYYMMDDHHMM for file %s"%get_file(filename))

    # get tuple 
    numbers_tuple = (numbers_str[0:4], numbers_str[4:6], numbers_str[6:8], numbers_str[8:10], numbers_str[10:12])
    numbers_tuple = tuple([int(x) for x in numbers_tuple])

    # checks
    for idx, (name, expected_range) in enumerate([("year", (2000, 2500)), ("month", (1, 12)), ("day", (1, 31)), ("hour", (0, 24)), ("minute", (0, 60))]):
        if numbers_tuple[idx]<expected_range[0] or numbers_tuple[idx]>expected_range[1]: print_with_runtime("WARNING: For file %s the parsed %s is %i, which may be incorrect."%(get_file(filename), name, numbers_tuple[idx]))

    return numbers_tuple

def get_int_as_str_two_digits(x):

    """Returns the int as a string with two digits"""

    x = str(x)
    if len(x)==1: x = "0%s"%x
    if len(x)!=2: raise ValueError("%s is invalid"%x)
    return x

def get_manual_coords(colonizer_coordinates_one_spot, coordinate_obtention_dir_plate):

    """Gets manual coords into colonizer_coordinates_one_spot"""

    # run parametryzer
    parametryzer_std = "%s/parametryzer.std"%coordinate_obtention_dir_plate
    run_cmd("%s/envs/colonyzer_env/bin/parametryzer > %s 2>&1"%(CondaDir, parametryzer_std), env="colonyzer_env")

    # checks
    if file_is_empty(colonizer_coordinates_one_spot): raise ValueError("%s should exist. Make sure that you clicked the spots or check %s"%(colonizer_coordinates_one_spot, parametryzer_std))
    remove_file(parametryzer_std)


def get_automatic_coords(colonizer_coordinates_one_spot, coordinate_obtention_dir_plate, latest_image, plate_batch, plate):

    """Gets automatic coords into colonizer_coordinates_one_spot"""

    # run colonyzer
    colonyzer_std = "%s/colonyzer.std"%coordinate_obtention_dir_plate
    try: 

        run_cmd("colonyzer --fmt 96 --remove > %s 2>&1"%colonyzer_std, env="colonyzer_env")
        auto_colonyzer_worked = True

    except:

        print_with_runtime("WARNING: Automatic spot location did not work!! You have to set manually the spots")
        auto_colonyzer_worked = False
        get_manual_coords(colonizer_coordinates_one_spot, coordinate_obtention_dir_plate)


    # create the auto file
    if auto_colonyzer_worked is True:

        # define the coordinates of the upper left and bottom right spots
        df_coords = get_tab_as_df_or_empty_df("%s/Output_Data/%s.out"%(coordinate_obtention_dir_plate, latest_image.rstrip(".tif"))).set_index(["Row", "Column"], drop=True)
        automatic_coords_str = ",".join([str(int(round(pos, 0))) for pos in (df_coords.loc[1, 1].x, df_coords.loc[1, 1].y, df_coords.loc[8, 12].x, df_coords.loc[8, 12].y)])

        # create the colonizer_coordinates_one_spot file as parametryzer does
        lines_parametryzer_output = ["# misc", 
                                     "default,96,%s,%s"%(automatic_coords_str, date.today().strftime("%Y-%m-%d")), 
                                     "#",
                                     "%s,96,%s"%(latest_image, automatic_coords_str)]

        open(colonizer_coordinates_one_spot, "w").write("\n".join(lines_parametryzer_output)+"\n")

        # show the automatic positioning of the image
        print_with_runtime("This is the automatic location of the spots in the image...")
        coords_image = "%s/Output_Images/%s_AREA.png"%(coordinate_obtention_dir_plate, latest_image.rstrip(".tif"))
        coords_image_w, coords_image_h = PIL_Image.open(coords_image).size

        coords_image_resized = "%s.resized.png"%coords_image
        coords_image_resized_object = PIL_Image.open(coords_image).resize((int(coords_image_w*0.4), int(coords_image_h*0.4)))
        coords_image_resized_w, coords_image_resized_h = coords_image_resized_object.size
        coords_image_resized_object.save(coords_image_resized)

        display_image_std = "%s/display_image.std"%coordinate_obtention_dir_plate
        run_cmd("%s/display_image.py %s %i %i 'automatic location for %s-plate%i' > %s 2>&1"%(ScriptsDir, coords_image_resized, coords_image_resized_w, coords_image_resized_h, plate_batch, plate, display_image_std), env="colonyzer_env")
        remove_file(display_image_std)

    # clean
    for folder in ["Output_Images", "Output_Data", "Output_Reports"]: delete_folder("%s/%s"%(coordinate_obtention_dir_plate, folder))
    remove_file(colonyzer_std)



def generate_colonyzer_coordinates_one_plate_batch_and_plate(dest_processed_images_dir, coordinate_obtention_dir_plate, sorted_image_names, automatic_coordinates, plate_batch, plate):

    """Generates a 'Colonyzer.txt' file in each dest_processed_images_dir with all the coordinates."""

    # define the dir with the coordinates for one image
    colonizer_coordinates_one_spot = "%s/Colonyzer.txt"%coordinate_obtention_dir_plate
    colonizer_coordinates = "%s/Colonyzer.txt"%dest_processed_images_dir

    # define the latest image to base the coordinates on
    latest_image = sorted_image_names[-1]

    if file_is_empty(colonizer_coordinates):

        # clean
        remove_file(colonizer_coordinates_one_spot)
        remove_file("%s/%s"%(coordinate_obtention_dir_plate, latest_image))

        # softlink one image into coordinate_obtention_dir to get coordinates
        #soft_link_files("%s/%s"%(dest_processed_images_dir, latest_image), "%s/%s"%(coordinate_obtention_dir_plate, latest_image))

        # move one donwsampled image to coordinate_obtention_dir_plate
        image_object = PIL_Image.open("%s/%s"%(dest_processed_images_dir, latest_image))
        original_w,  original_h = image_object.size
        factor_resize = 0.2
        image_object.resize((int(original_w*factor_resize), int(original_h*factor_resize))).save("%s/%s"%(coordinate_obtention_dir_plate, latest_image), quality=20, optimize=True) # optimize=True
        downsized_w, donwsized_h = PIL_Image.open("%s/%s"%(coordinate_obtention_dir_plate, latest_image)).size

        # get to the folder
        initial_dir = os.getcwd()
        os.chdir(coordinate_obtention_dir_plate)

        # get coordinates automatically
        if automatic_coordinates is True: get_automatic_coords(colonizer_coordinates_one_spot, coordinate_obtention_dir_plate, latest_image, plate_batch, plate)

        # use parametryzer
        else: get_manual_coords(colonizer_coordinates_one_spot, coordinate_obtention_dir_plate)

        # go back to the initial dir
        os.chdir(initial_dir)

        # create a colonyzer file with all the info in dest_processed_images_dir/Colonyzer.txt

        # get last line
        last_line_split = open(colonizer_coordinates_one_spot, "r").readlines()[-1].strip().split(",")

        # define the wells
        wells = last_line_split[1]
        if wells!="96": raise ValueError("You set the analysis for %s-well plates, which is incompatible. Make sure that you press 'g' to save the coordinates."%wells)

        # get the coordinates
        coordinates_str = ",".join(last_line_split[2:])

        # modify the coordinates to take into account that the coordinates image was donwsized by factor_resize
        coordinates_str = ",".join([str(int(int(x)*(1/factor_resize))) for x in coordinates_str.split(",")])

        # check that the coordinates make sense
        expected_w, expected_h = PIL_Image.open("%s/%s"%(dest_processed_images_dir, latest_image)).size
        top_left_x, top_left_y, bottom_right_x, bottom_right_y = [int(x) for x in coordinates_str.split(",")]
        cropped_w = bottom_right_x - top_left_x
        cropped_h = bottom_right_y - top_left_y

        error_log = "Make sure that you are first selecting the upper-left spot and then the lower-right spot."
        for dim, expected_val, cropped_val in [("width", expected_w, cropped_w), ("height", expected_h, cropped_h)]:

            if cropped_val<=0: raise ValueError("The cropped image has <=0 %s. %s"%(dim, error_log))
            if cropped_val>expected_val: raise ValueError("The %s of the cropped image is above the original one. %s"%(dim, error_log))
            if cropped_val<=(expected_val*0.3): raise ValueError("The %s of the cropped image is %s, and the full image has %s. The cropped image should have a %s which is close to the original one. %s"%(dim, cropped_val, expected_val, dim, error_log))

            if cropped_val<=(expected_val*0.5): print_with_runtime("WARNING: The %s of the cropped image is %s, and the full image has %s. The cropped image should have a %s which is close to the original one. %s. If you are sure of this you can skip this warning."%(dim, cropped_val, expected_val, dim, error_log))

        # write
        non_coordinates_lines = [l for l in open(colonizer_coordinates_one_spot, "r").readlines() if l.startswith("#") or not l.startswith(latest_image)]
        coordinates_lines = ["%s,%s,%s\n"%(image, wells, coordinates_str) for image in sorted_image_names]
        
        colonizer_coordinates_tmp = "%s.tmp"%colonizer_coordinates
        open(colonizer_coordinates_tmp, "w").write("".join(non_coordinates_lines + coordinates_lines))
        os.rename(colonizer_coordinates_tmp, colonizer_coordinates)

def run_colonyzer_one_set_of_parms(parms, outdir_all, image_names_withoutExtension):

    """Runs colonyzer for a set of parms. This should be run from a directory where there are imnages"""

    # sort
    sorted_parms = sorted(parms)
    parms_str = "_".join(sorted_parms)
    extra_cmds_parmCombination = "".join([" --%s "%x for x in sorted_parms])

    # change the parms str if blank
    if parms_str=="": parms_str = "noExtraParms"

    # define the outdirs
    outdir = "%s/output_%s"%(outdir_all, parms_str)
    outdir_tmp = "%s_tmp"%outdir

    # check if all images have a data file (which means that they have been analyzed in outdir/Output_Data)
    all_images_analized = False
    Output_Data_dir = "%s/Output_Data"%outdir
    if os.path.isdir(Output_Data_dir):
        Output_Data_content = set(os.listdir(Output_Data_dir))
        if all(["%s.out"%f in Output_Data_content for f in image_names_withoutExtension]): all_images_analized = True

    # run colobyzer 
    if all_images_analized is False:

        # delete and create the outdirs
        delete_folder(outdir)
        delete_folder(outdir_tmp); make_folder(outdir_tmp)

        # run colonizer, which will generate data under . (images_folder)
        colonyzer_exec = "%s/envs/colonyzer_env/bin/colonyzer"%CondaDir
        colonyzer_std = "%s.running_colonyzer.std"%outdir_tmp
        colonyzer_cmd = "%s %s --plots --remove --initpos --fmt 96 > %s 2>&1"%(colonyzer_exec, extra_cmds_parmCombination, colonyzer_std)
        run_cmd(colonyzer_cmd, env="colonyzer_env")
        remove_file(colonyzer_std)

        # once it is donde, move to outdir_tmp
        for folder in ["Output_Images", "Output_Data", "Output_Reports"]: run_cmd("mv %s/ %s/"%(folder, outdir_tmp))

        # change the name, which marks that everything finished well
        os.rename(outdir_tmp, outdir)

def get_barcode_from_filename(filename):

    """Gets a filename like img_0_2090716_1448 and returns the barcode."""

    # get plateID
    plateID = "".join(filename.split("_")[0:2])

    # get timestamp
    d = list(filename.split("_")[2])
    t = list(filename.split("_")[3])
    d_string = "%s%s%s%s-%s%s-%s%s"%(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7])
    t_string = "%s%s-%s%s-00"%(t[0], t[1], t[2], t[3])

    return "%s-%s_%s"%(plateID, d_string, t_string)


def get_barcode_for_filenames(filenames_series):

    """Takes a series of filenames and passes them to get_barcode_from_filename to get barcoded values. The barcode cannot exceed 11 chars, so that it is stripped accoringly by this function"""

    # get barcoded items
    barcoded_names  = filenames_series.apply(get_barcode_from_filename)

    # return
    oldBar_to_newBar = {"img0":"img_fitness"}
    return barcoded_names.apply(lambda x: "%s-%s"%(oldBar_to_newBar[x.split("-")[0]], "-".join(x.split("-")[1:])))

def save_df_as_tab(df, file):

    """Takes a df and saves it as tab"""

    file_tmp = "%s.tmp"%file
    df.to_csv(file_tmp, sep="\t", index=False, header=True)
    os.rename(file_tmp, file)

def get_tab_as_df_or_empty_df(file):

    """Gets df from file or empty df"""

    nlines = len([l for l in open(file, "r").readlines() if len(l)>1])

    if nlines==0: return pd.DataFrame()
    else: return pd.read_csv(file, sep="\t")


def get_df_fitness_measurements_one_parm_set(outdir_all, outdir_name, plate_batch, plate, df_plate_layout):

    """For one plate_batch and plate combination and one parm set, get the fitness measurements with qfa. The outdir_all should be where the colonyzer results are."""

    #### PREPARE FITNESS DATA FOR QFA ANALYSIS ####

    # get the data path
    data_path = "%s/%s/Output_Data"%(outdir_all, outdir_name)

    # generate a df with fitness info of all images
    all_df = pd.DataFrame()

    for f in [x for x in os.listdir(data_path) if x.endswith(".dat")]: 

        # get df
        df = pd.read_csv("%s/%s"%(data_path, f), sep="\t", header=None)

        # append
        all_df = all_df.append(df)

    # add barcode in the first place, instead of the filename
    all_df[0] = get_barcode_for_filenames(all_df[0])

    # sort the values
    all_df = all_df.sort_values(by=[0,1,2])

    # change the NaN by "NA"
    def change_NaN_to_str(cell):
        if pd.isna(cell): return "NA"
        else: return cell

    all_df = all_df.applymap(change_NaN_to_str)

    # write the csv under outdir
    all_df.to_csv("%s/%s/all_images_data.dat"%(outdir_all, outdir_name), sep="\t", index=False, header=False)
    
    ###############################################

    ###### CREATE FILES THAT ARE NECESSARY FOR QFA TO RUN #######

    # create the files that are necessary for the R qfa package to generate the output files

    # keep the plate layout that is interesting here
    df_plate_layout = df_plate_layout[(df_plate_layout.plate_batch==plate_batch) & (df_plate_layout.plate==plate)].set_index(["row", "column"])

    # checks
    if len(df_plate_layout[["drug", "concentration"]].drop_duplicates())!=1: raise ValueError("There should be only one plate and concentration")
    drug = df_plate_layout.drug.iloc[0]
    concentration = df_plate_layout.concentration.iloc[0]


    # experiment descrption: file describing the inoculation times, library and plate number for unique plates. 
    exp_df = pd.DataFrame()

    # get all plates
    for I, plateBarcode in enumerate(set([x.split("-")[0] for x in all_df[0]])): 

        startTime = min(all_df[all_df[0].apply(lambda x: x.startswith(plateBarcode))][0].apply(lambda y: "-".join(y.split("-")[1:])))
        dict_data = {"Barcode":plateBarcode, "Start.Time":startTime, "Treatment": plate_batch, "Medium":"[%s]=%s"%(drug, concentration) ,"Screen":"screen", "Library":"strain", "Plate": plate, "RepQuad":1}

        exp_df = exp_df.append(pd.DataFrame({k: {I+1 : v} for k, v in dict_data.items()}))

    # write
    exp_df.to_csv("%s/%s/ExptDescription.txt"%(outdir_all, outdir_name), sep="\t", index=False, header=True)

    # library description: where you state, for each plate (from 1, 2, 3 ... and as many plates defined in ExptDescription.Plate, the name and the ORF, if interestning)
    lib_df = pd.DataFrame()

    # define the rows and cols
    nWells_ro_NrowsNcols = {96:(8, 12)}

    for barcode, plateID in exp_df[["Barcode", "Plate"]].values:
        for row in range(1, nWells_ro_NrowsNcols[96][0]+1):
            for col in range(1, nWells_ro_NrowsNcols[96][1]+1):

                # get the strain
                strain = df_plate_layout.loc[(row, col), "strain"]

                # add to df
                dict_data = {"Library":"strain", "ORF":strain, "Plate":plateID, "Row":row, "Column":col, "Notes":""}
                lib_df = lib_df.append(pd.DataFrame({k: {plateID : v} for k, v in dict_data.items()}))

    # write
    lib_df.to_csv("%s/%s/LibraryDescriptions.txt"%(outdir_all, outdir_name), sep="\t", index=False, header=True)

    # orf-to-gene to get the strains in the plot
    orf_to_gene_df = pd.DataFrame({0:list(df_plate_layout.strain), 1:list(df_plate_layout.strain)})
    orf_to_gene_df.to_csv("%s/%s/ORF2GENE.txt"%(outdir_all, outdir_name), sep="\t", index=False, header=False)

    #############################################################


    ##### RUN QFA AND SAVE #####

    # generate the plots with R
    fitness_measurements_std = "%s/fitness_measurements.std"%data_path
    run_cmd("/workdir_app/scripts/get_fitness_measurements.R %s > %s 2>&1"%("%s/%s"%(outdir_all, outdir_name), fitness_measurements_std), env="main_env")
    remove_file(fitness_measurements_std)

    # save the df
    df_fitness_measurements_file = "%s/%s/df_fitness_measurements.tab"%(outdir_all, outdir_name)
    os.rename("%s/%s/logRegression_fits.tbl"%(outdir_all, outdir_name), df_fitness_measurements_file)

    ############################

    return get_tab_as_df_or_empty_df(df_fitness_measurements_file)

def get_df_integrated_fitness_measurements_one_plate_batch_and_plate(Ibatch, nbatches, images_folder, outdir_all, plate_batch, plate, sorted_image_names, df_plate_layout):

    """Analyzes the images from images_folder, writing into outdir_all."""

    # log
    print_with_runtime("Analyzing images for plate_batch-plate %i/%i: %s-plate%i"%(Ibatch, nbatches, plate_batch, plate))

    # define the final output
    integrated_data_file = "%s/integrated_data.tbl"%(outdir_all)
    if file_is_empty(integrated_data_file):

        # debug
        #delete_folder(outdir_all)

        # prepare dirs
        make_folder(outdir_all)

        ###### RUN COLONYZER TO GET IMAGE DATA ######

        # clean the hidden files from images_folder
        for f in os.listdir(images_folder):
            if f.startswith("."): remove_file("%s/%s"%(images_folder, f))

        # move into the images dir
        initial_dir = os.getcwd()
        os.chdir(images_folder)

        # check 
        if file_is_empty("./Colonyzer.txt"): raise ValueError("Colonyzer.txt should exist in %s"%images_folder)

        # define the image names that you expect
        image_names_withoutExtension = set({x.split(".")[0] for x in sorted_image_names})

        # run colonyzer for all parameters
        #print_with_runtime("Running colonyzer to get raw fitness data...")
        run_colonyzer_one_set_of_parms(parms_colonyzer, outdir_all, image_names_withoutExtension)

        # go back to the initial dir
        os.chdir(initial_dir)

        #############################################

        ####### RUN FITTING TO GET FITNESS CALCULATIONS ########

        # go through each of the directories of data and generate the image analysis data
        #print_with_runtime("Running qfa to get per-spot fitness data...")

        # generate the fitness df
        df_fitness_measurements = get_df_fitness_measurements_one_parm_set(outdir_all, "output_%s"%("_".join(sorted(parms_colonyzer))), plate_batch, plate, df_plate_layout)

        ########################################################

        ####### ADD EXTRA FIELDS #####

        ##############################

        # add fields
        df_fitness_measurements["plate"] = plate
        df_fitness_measurements["plate_batch"] = plate_batch
        df_fitness_measurements["spotID"] = df_fitness_measurements.apply(lambda r: "%s_%s"%(r["Row"], r["Column"]), axis=1)

        # correct the rsquare
        def get_rsquare_to0(rsq):
            if rsq>0: return rsq
            else: return 0.0
        df_fitness_measurements["rsquare"] = df_fitness_measurements.rsquare.apply(get_rsquare_to0)

        # get the correct DT_h
        maxDT_h = 25.0
        def get_DT_good_rsq(DT_h, rsq, rsq_tshd=0.9):
            if rsq>=rsq_tshd: return DT_h
            else: return maxDT_h
        df_fitness_measurements["DT_h_goodR2"] = df_fitness_measurements.apply(lambda r: get_DT_good_rsq(r["DT_h"], r["rsquare"]), axis=1)

        # add the inverse of DT_h
        df_fitness_measurements["inv_DT_h_goodR2"] = 1 / df_fitness_measurements.DT_h_goodR2

        # save and rename
        save_df_as_tab(df_fitness_measurements, integrated_data_file)


    # return 
    return get_tab_as_df_or_empty_df(integrated_data_file)


def check_no_nans_series(x):

    """Raise value error if nans"""

    if any(pd.isna(x)): raise ValueError("There can't be nans in series %s"%x)


def copy_file(origin_file, dest_file):

    """Copy file if not done file"""

    if file_is_empty(dest_file):

        dest_file_tmp = "%s.tmp"%dest_file
        shutil.copy(origin_file, dest_file_tmp)
        os.rename(dest_file_tmp, dest_file)


def get_fitness_df_with_relativeFitnessEstimates(fitness_df, fitness_estimates):

    """This function adds a set of *_rel fields to fitness_df, which are, for each condition, the fitness relative to the concentration==0 spot."""

    # correct the fitness estimates to avoid NaNs, 0s and infs
    fitEstimate_to_maxNoNInf = {fe : max(fitness_df[fitness_df[fe]!=np.inf][fe]) for fe in fitness_estimates}

    def get_correct_val(x, fitness_estimate):
        
        if x==np.inf: return fitEstimate_to_maxNoNInf[fitness_estimate]
        elif x!=np.nan and type(x)==float: return x
        else: raise ValueError("%s is not a valid %s"%(x, fitness_estimate))
        
    for fe in fitness_estimates: 
        
        # get the non nan and non inf vals
        fitness_df[fe] = fitness_df[fe].apply(lambda x: get_correct_val(x, fe))
        
        # add a pseudocount that is equivalent to the minimum, if there are any negative values
        if any(fitness_df[fe]<0): 
            print_with_runtime("WARNING: There are some negative values in %s, modifying the data with a pseudocount"%fe)
            fitness_df[fe] = fitness_df[fe] + abs(min(fitness_df[fitness_df[fe]<0][fe]))    

    # define a df with the maximum growth rate (the one at concentration==0) for each combination of sampleID. Note that there is one baseline for all drugs
    df_max_gr = fitness_df[fitness_df.concentration==0.0].set_index("sampleID", drop=False)[fitness_estimates]
    all_sampleIDs = set(df_max_gr.index)
    fitEstimate_to_sampleID_to_maxValue = {fe : {sampleID : df_max_gr.loc[sampleID, fe] for sampleID in all_sampleIDs} for fe in fitness_estimates}

    # add the relative fitness estimates
    fitness_estimates_rel = ["%s_rel"%x for x in fitness_estimates]

    def get_btw_0_and_1(x):
            
        if pd.isna(x): return 1.0
        elif x==np.inf: return 1.0
        elif x==-np.inf: return 0.0
        elif x<0: raise ValueError("there can't be any negative values")
        else: return x  

    np.seterr(divide='ignore', invalid="ignore")
    fitness_df[fitness_estimates_rel] = fitness_df.apply(lambda r: pd.Series({"%s_rel"%fe : get_btw_0_and_1(np.divide(r[fe], fitEstimate_to_sampleID_to_maxValue[fe][r["sampleID"]])) for fe in fitness_estimates}), axis=1)

    return fitness_df

def get_MIC_for_EUCASTreplicate(df, fitness_estimate, concs_info, mic_fraction):

    """This function takes a df of one single eucast measurement, and returns the Minimal Inhibitory concentration, where the relative fitness is fitness_estimate, The df should be sorted by concentration."""

    # get the expected concs
    max_expected_conc = concs_info["max_conc"]
    first_concentration = concs_info["first_conc"]
    expected_conc_to_previous_conc = concs_info["conc_to_previous_conc"]

    # check that the df is sorterd by conc
    if sorted(df.concentration)!=list(df.concentration): raise ValueError("the df should be sorted by concentration")

    # get the assayed concs
    assayed_concs = set(df.concentration)

    # calculate MIC
    concentrations_less_than_mic_fraction = df[df[fitness_estimate]<(1-mic_fraction)]["concentration"]

    # define a string for the warnings
    mic_string = "sampleID=%s|fitness_estimate=%s|MIC_%.2f"%(df.sampleID.iloc[0], fitness_estimate, mic_fraction)

    # define the real mic according to missing data

    # when there is no mic conc
    if len(concentrations_less_than_mic_fraction)==0:

        # when the max conc has been considered and no mic is found
        if max_expected_conc in assayed_concs: real_mic = (max_expected_conc*2)

        # else we can't know were the mic is
        else: 
            #print("WARNING: There is no MIC, but the last concentration was not assayed for %s. MIC is set to NaN"%mic_string)
            real_mic = np.nan

    # when there is one
    else:

        # calculate the mic
        mic = min(concentrations_less_than_mic_fraction)

        # calculate the concentration before the mic
        df_conc_before_mic = df[df.concentration<mic]

        # when there is no such df, just keep the mic if there is only the first assayed concentration 
        if len(df_conc_before_mic)==0: 

            # if the mic is the first concentration or the first concentration is already below 1-mic_fraction
            if mic==first_concentration: real_mic = mic    
            elif mic==0.0: real_mic = 0.001 # pseudocount          
            else: 
                #print("WARNING: We cound not find MIC for %s"%mic_string)
                real_mic = np.nan

        else:

            # get the known or expected concentrations
            conc_before_mic = df_conc_before_mic.iloc[-1].concentration
            expected_conc_before_mic = expected_conc_to_previous_conc[mic]

            # if the concentration before mic is not the expected one, just not consider
            if abs(conc_before_mic-expected_conc_before_mic)>=0.001: 
                #print("WARNING: We cound not find MIC for %s"%mic_string)
                real_mic = np.nan
            else: real_mic = mic

    # if there is any missing 
    if real_mic==0: raise ValueError("mic can't be 0. Check how you calculate %s"%fitness_estimate)

    return real_mic


def get_SMG_for_EUCASTreplicate(df, raw_fitness_estimate, MIC, mic_fraction):

    """This function takes a df of one single eucast measurement, and returns the Supra-MIC growth."""

    # check that the df is sorterd by conc
    if sorted(df.concentration)!=list(df.concentration): raise ValueError("the df should be sorted by concentration")

    # define a string for the warnings
    mic_string = "sampleID=%s|raw_fitness_estimate=%s|MIC_%.2f"%(df.sampleID.iloc[0], raw_fitness_estimate, mic_fraction)

    # if the MIC is nan, you can't calculate SMG
    if pd.isna(MIC):
        #print("WARNING: We cound not find SMG for %s, since the MIC is NaN."%mic_string)
        smg = np.nan

    else:

        # define the fitness at conc0 and debug it
        df_conc0 = df[df.concentration==0]
        if len(df_conc0)!=1: raise ValueError("there should be only 1 row in df_conc0")
        fitness_conc0 = df_conc0[raw_fitness_estimate].iloc[0]
        if pd.isna(fitness_conc0) or fitness_conc0<=0 or fitness_conc0==np.inf or fitness_conc0==-np.inf: raise ValueError("invalid fitness_conc0: %s"%fitness_conc0)

        # if you have at least 2 concentrations above MIC, calculate supra mic growth
        df_conc_after_mic = df[df.concentration>MIC]
        if len(df_conc_after_mic)>=2: smg = np.mean(df_conc_after_mic[raw_fitness_estimate]) / fitness_conc0

        else:
            #print("WARNING: We cound not find SMG for %s, since there are only %i concentrations >MIC."%(mic_string, len(df_conc_after_mic)))
            smg = np.nan

    return smg


def get_auc(x, y):

    """Takes an x and a y and returns the area under the curve"""

    return sklearn_auc(x, y)


def get_AUC_for_EUCASTreplicate(df, fitness_estimate, concs_info, concentration_estimate, min_points_to_calculate_auc=4):

    """Takes a df were each row has info about a curve of a single EUCAST and returns the AUC with some corrections"""

    # get the expected concs
    max_expected_conc = concs_info["max_conc"]
    conc0 = concs_info["zero_conc"] 

    # calculate the auc if all the concentrations had a fitness of 1 (which is equal to no-drug if the fitness_estimate=1)
    max_auc = (max_expected_conc-conc0)*1

    # get the assayed concs
    assayed_concs = set(df[concentration_estimate])

    # when you lack less than min_points_to_calculate_auc curves just drop
    if len(df)<min_points_to_calculate_auc: auc = np.nan


    # when they are all 0, just return 0
    elif sum(df[fitness_estimate]==0.0)==len(df): auc = 0.0

    else:

        # if the maximum growth is not measured, and the max measured is growing we discard the measurement, as it may change the results
        if max_expected_conc not in assayed_concs and df.iloc[-1].is_growing: auc = np.nan

        else:

            # get the values
            xvalues = df[concentration_estimate].values
            yvalues = df[fitness_estimate].values

            # if the initial is the first concentration, add the one
            if conc0 not in assayed_concs:
                xvalues = np.insert(xvalues, 0, conc0)
                yvalues = np.insert(yvalues, 0, 1.0)

            # calculate auc, relattive to the 
            auc = get_auc(xvalues, yvalues)/max_auc


    if auc<0.0: 

        #print(df[[concentration_estimate, fitness_estimate, "is_growing"]])
        #print(xvalues, yvalues)
        #print(assayed_concs, conc0)
        raise ValueError("auc can't be 0. Check how you calculate %s"%fitness_estimate)

    return auc


def get_susceptibility_df(fitness_df, fitness_estimates, pseudocount_log2_concentration, min_points_to_calculate_auc, filename, experiment_name):

    """
    Takes a fitness df and returns a df where each row is one sampleID-drug-fitness_estimate combination and there are susceptibility measurements (rAUC, MIC or initial fitness).

    """

    if file_is_empty(filename):

        # init the df that will contain the susceptibility estimates
        df_all = pd.DataFrame()

        # keep
        fitness_df = cp.deepcopy(fitness_df)

        # go through each drug
        for drug in sorted(set(fitness_df[fitness_df.concentration!=0.0].drug)):
            #print_with_runtime("getting susceptibility estimates for %s"%drug)

            # get the df for this drug, adding also the concentration==0 with this drug for normalization
            fitness_df_d = fitness_df[(fitness_df.drug==drug) | (fitness_df.concentration==0.0)]
            fitness_df_d["drug"] = drug

            # define the sorted_concentrations, and only continue if there are >=3
            sorted_concentrations = sorted(set(fitness_df_d.concentration))
            if len(sorted_concentrations)<3: 
                print_with_runtime("WARNING: For drug=%s there are only %i concentrations. Skipping the susceptibility analysis since it needs >=3 concentrations (including 0)."%(drug, len(sorted_concentrations)))
                continue

            # map each drug to the expected concentrations
            concentrations_dict = {"max_conc":max(sorted_concentrations), "zero_conc":sorted_concentrations[0], "first_conc":sorted_concentrations[1], "conc_to_previous_conc":{c:sorted_concentrations[I-1] for I,c in enumerate(sorted_concentrations) if I>0}}

            sorted_log2_concentrations = [np.log2(c + pseudocount_log2_concentration) for c in sorted_concentrations]
            concentrations_dict_log2 = {"max_conc":max(sorted_log2_concentrations), "zero_conc":sorted_log2_concentrations[0], "first_conc":sorted_log2_concentrations[1], "conc_to_previous_conc":{c:sorted_log2_concentrations[I-1] for I,c in enumerate(sorted_log2_concentrations) if I>0}}

            # filter out unsuited spots for relative fitness purposes
            fitness_df_d = fitness_df_d[fitness_df_d.idx_correct_rel_estimates]
            if len(fitness_df_d)==0: raise ValueError("There should be some rows in fitness_df_d. If this is not the case it may be because there are no correct spots in drug=%s"%drug)

            # go through all the relative fitness estimates
            relative_fitness_estimates = ["%s_rel"%f for f in fitness_estimates]
            for fitness_estimate in relative_fitness_estimates:

                # get the raw_fitness_estimate
                raw_fitness_estimate = fitness_estimate.replace("_rel", "")
                if "%s_rel"%raw_fitness_estimate!=fitness_estimate: raise ValueError("invalid fe")

                # define a grouped df, where each index is a unique sample ID
                grouped_df = fitness_df_d[["sampleID", "concentration", "is_growing", "log2_concentration", fitness_estimate, raw_fitness_estimate]].sort_values(by=["sampleID", "concentration"]).groupby("sampleID")

                # init a df with the MICs and AUCs for this concentration and fitness_estimate
                df_f = pd.DataFrame()

                # add MIC:
                for mic_fraction in [0.25, 0.5, 0.75, 0.9]:

                    # add MIC
                    mic_field = "MIC_%i"%(mic_fraction*100)
                    df_f[mic_field] = grouped_df.apply(lambda x: get_MIC_for_EUCASTreplicate(x, fitness_estimate, concentrations_dict, mic_fraction))

                    # print warnings of MIC==nan
                    #df_nan_mic = df_f[pd.isna(df_f[mic_field])]
                    #if len(df_nan_mic)>0: print_with_runtime("WARNING: In drug=%s and fitness estimate=%s, there are %i spots where we could not calculate %s. This is be due to missing spots in some concentration."%(drug, fitness_estimate, len(df_nan_mic), mic_field))

                    # add SMG
                    sample_to_mic = dict(df_f[mic_field]) 
                    smg_field = "SMG_MIC_%i"%(mic_fraction*100)
                    df_f[smg_field] = grouped_df.apply(lambda x: get_SMG_for_EUCASTreplicate(x, raw_fitness_estimate, sample_to_mic[x.name], mic_fraction))

                    # print warnings of SMG==nan
                    #df_nan_smg = df_f[pd.isna(df_f[smg_field])]
                    #if len(df_nan_smg)>0: print_with_runtime("WARNING: In drug=%s and fitness estimate=%s, there are %i spots where we could not calculate %s. This is due to missing spots in some concentration, or because there are <2 concentrations >MIC."%(drug, fitness_estimate, len(df_nan_smg), smg_field))

                # add the rAUC for log2 or not of the concentrations
                for conc_estimate, conc_info_dict in [("concentration", concentrations_dict), ("log2_concentration", concentrations_dict_log2)]:

                    # get a series that map each sampleID to the AUC 
                    df_f["rAUC_%s"%conc_estimate] = grouped_df.apply(lambda x: get_AUC_for_EUCASTreplicate(x, fitness_estimate, conc_info_dict, conc_estimate, min_points_to_calculate_auc=min_points_to_calculate_auc))

                # add the raw fitness of conc==0
                df_conc0 = fitness_df_d[(fitness_df_d["concentration"]==0.0)]
                sample_to_fitness0 = dict(df_conc0[["sampleID", raw_fitness_estimate]].drop_duplicates().set_index("sampleID")[raw_fitness_estimate])
                df_f["raw_fitness_conc0"] = list(map(lambda x: sample_to_fitness0[x], df_f.index))
                check_no_nans_series(df_f["raw_fitness_conc0"])

                # keep df
                df_f = df_f.merge(fitness_df_d[["sampleID", "strain", "replicateID", "row", "column"]].set_index("sampleID").drop_duplicates(),  left_index=True, right_index=True, how="left",  validate="one_to_one")

                df_f["drug"] = drug
                df_f["max_concentration"] = max(sorted_concentrations)
                df_f["fitness_estimate"] = fitness_estimate
                df_all = df_all.append(df_f).reset_index(drop=True)

        # checks 
        for k in set(df_all.keys()).difference({"MIC_25", "MIC_50", "MIC_75", "MIC_90", "SMG_MIC_25", "SMG_MIC_50", "SMG_MIC_75", "SMG_MIC_90", "rAUC_concentration", "rAUC_log2_concentration"}): check_no_nans_series(df_all[k])

        # add exp name
        df_all["experiment_name"] = experiment_name

        # save
        save_df_as_tab(df_all, filename)

    return get_tab_as_df_or_empty_df(filename)

def generate_croped_image(origin_image, cropped_image, plate):

    """Generates a cropped image which is a quadrant (specified by plate) of the origin_image"""

    if file_is_empty(cropped_image):

        # open the image
        image_object = PIL_Image.open(origin_image)
        w, h = image_object.size 

        # map each quadrant (plate) to the coordinates to crop ((left, top, right, bottom)). These are two points (from, to). The upper-left is 0,0 and the lower-left is w,h
        plate_to_coords = {1 : (0, 0, w/2, h/2),
                           2 : (w/2, 0, w, h/2),
                           3 : (0, h/2, w/2, h),
                           4 : (w/2, h/2, w, h) 
                           }
          
        # crop the image
        cropped_image_object = image_object.crop(plate_to_coords[plate])

        # checks
        cropped_w, cropped_h = cropped_image_object.size
        if cropped_w<(w*0.1) or cropped_h<(h*0.1): raise ValueError("The size of the cropped image from %s is invalid: %s. The original w,h size was %s"%(origin_image, cropped_image_object.size, image_object.size ))

        # show the image
        cropped_image_tmp = "%s.tif"%cropped_image
        cropped_image_object.save(cropped_image_tmp)
        os.rename(cropped_image_tmp, cropped_image)

def get_clean_float_value(x):

    """Gets a clean float value"""

    # for non numeric, return the value
    if type(x)==str or pd.isna(x): return x

    # ints
    if int(x)==x: return int(x)

    # round to 3 decimals
    else: return round(x, 3)

def get_mode(all_vals):

    """Gets mode"""

    c = Counter(all_vals)
    all_modes = [k for k, v in c.items() if v == c.most_common(1)[0][1]]
    return min(all_modes)

def get_row_simple_susceptibility_df_one_strain_and_drug(df):

    """Gets a row of a susceptibility df for one drug and strain"""

    # init dict
    data_dict = {"drug":df.drug.iloc[0], "strain":df.strain.iloc[0]}

    # debug
    if len(df)!=len(set(df.replicateID)): raise ValueError("replicateIDs should be unique")

    # go through different fields
    for field_name, field in [("MIC50", "MIC_50"), ("SMG-MIC50", "SMG_MIC_50"), ("rAUC", "rAUC_concentration")]:

        # get the no nan vals
        all_vals = sorted(df[(~pd.isna(df[field]))][field])

        # round
        all_vals = [float(x) for x in all_vals]

        # get the range of all replicates and the median
        if len(all_vals)>0: 
            data_dict["median_%s"%field_name] = np.median(all_vals)
            data_dict["mode_%s"%field_name] = get_mode(all_vals)
            data_dict["mad_%s"%field_name] = scipy.stats.median_absolute_deviation(all_vals)
            data_dict["range_%s"%field_name] = "%s-%s"%(get_clean_float_value(min(all_vals)), get_clean_float_value(max(all_vals)))

        else: 
            data_dict["median_%s"%field_name] = np.nan
            data_dict["mode_%s"%field_name] = np.nan
            data_dict["mad_%s"%field_name] = np.nan
            data_dict["range_%s"%field_name] = "no_data"

        # get the number of replicates
        data_dict["replicates_%s"%field_name] = len(all_vals)

    # add the maximum concentration
    data_dict["max_concentration"] = get_clean_float_value(df.max_concentration.iloc[0])

    return pd.Series(data_dict)

def get_plate_quadrant(r):

    """Takes a row and col and returns the quadrant 1, 2, 3, 4"""

    if r.column in set(range(1,7)):
        if r.row in set(range(1,5)): quadrant = 1
        elif r.row in set(range(5,9)): quadrant = 3

    elif r.column in set(range(7,13)):
        if r.row in set(range(1,5)): quadrant = 2
        elif r.row in set(range(5,9)): quadrant = 4

    return quadrant

def find_nearest(a, a0):

    """Element in nd array `a` closest to the scalar value `a0`"""
    
    # Debug elements that are inf
    if a0 not in [np.inf, -np.inf]:
        a = np.array(a)
        idx = np.abs(a - a0).argmin()
        closest_in_a = a.flat[idx]
        
    elif a0==np.inf:
        closest_in_a = max(a)
        
    elif a0==-np.inf:
        closest_in_a = min(a)        

    return closest_in_a

def get_uniqueVals_df(df): return set.union(*[set(df[col]) for col in df.columns])

def rgb_to_hex(rgb):

    # Helper function to convert colour as RGB tuple to hex string
    rgb = tuple([int(255*val) for val in rgb])
    hex_val = '#%02x%02x%02x'%(rgb[0], rgb[1], rgb[2])

    if len(hex_val)!=7: raise ValueError("%s is not valid"%hex_val)

    return hex_val

def get_value_to_color(values, palette="mako", n=100, type_color="rgb", center=None):

    """TAkes an array and returns the color that each array has. Checj http://seaborn.pydata.org/tutorial/color_palettes.html"""

    # get the colors
    colors = sns.color_palette(palette, n)

    # change the colors
    if type_color=="rgb": colors = colors
    elif type_color=="hex": colors = [rgb_to_hex(c) for c in colors]
    else: raise ValueError("%s is not valid"%palette)

    # if they are strings
    if type(list(values)[0])==str:

        palette_dict = dict(zip(values, colors))
        value_to_color = palette_dict

    # if they are numbers
    else:

        # map eaqually distant numbers to colors
        if center==None:
            min_palette = min(values)
            max_palette = max(values)
        else: 
            max_deviation = max([abs(fn(values)-center) for fn in [min, max]])
            min_palette = center - max_deviation
            max_palette = center + max_deviation

        all_values_palette = list(np.linspace(min_palette, max_palette, n))
        palette_dict = dict(zip(all_values_palette, colors))

        # get value to color
        value_to_color = {v : palette_dict[find_nearest(all_values_palette, v)] for v in values}

    return value_to_color, palette_dict


# define the descriptions of fitness estimates
fe_to_description = {"K" : "Parameter of a generalised logistic model that is fit to the data. Maximum predicted cell density",
                     "r": "Generalised logistic model rate parameter",
                     "nAUC": "Numerical Area Under Curve. This is a model-free fitness estimate",
                     "nr": " Numerical estimate of intrinsic growth rate. Growth rate estimated by fitting smoothing function to log of data, calculating numerical slope estimate across range of data and selecting the maximum estimate (should occur during exponential phase)",
                     "nr_t": "Time at which maximum slope of log observations occurs (~lag phase)",
                     "maxslp": "Numerical estimate of maximum slope of growth curve",
                     "maxslp_t": "Time at which maximum slope of observations occurs (~lag phase)",
                     "MDR": "Maximum Doubling Rate",
                     "MDP": "Maximum Doubling Potential",
                     "DT": "Doubling Time. Estimated from the fit parms at t0. May be biased if there is lag phase",
                     "AUC": "Area Under Curve (from model fit)",
                     "MDRMDP": "Addinall et al. style fitness",
                     "DT_h": "max DT in hours. This is a numerical estimate from data",
                     "DT_h_goodR2": "max DT in hours. This is a numerical estimate from data, only considering fits with r2>0.9",
                     "rsquare": "rsquare between the fit and the data"}

def convert_nans_to_0s(x):
    if pd.isna(x): return 0.0
    else: return x

def get_annotationColor_on_bgcolor(bgcolor, threshold_gray=0.4):

    """Takes a bgcolor and retrives the optimum color to write an annotation on. """

    # change to RGB tuple
    if type(bgcolor)==str and not bgcolor.startswith("#"): bgcolor = mcolors.to_rgb(bgcolor)

    # debug
    elif type(bgcolor)==str and bgcolor.startswith("#"): bgcolor = tuple([x/255 for x in ImageColor.getcolor(bgcolor, "RGB")])

    # get the gray (a number between 0(black) and 1(white))
    gray = np.mean(bgcolor, -1)

    if gray>1: raise ValueError("gray can't be above 1. bgcolor %s is strange"%bgcolor)

    if gray<threshold_gray: return "white"
    else: return "black"

def plot_heatmap_susceptibility(susceptibility_df, plots_dir_all, fitness_estimates, experiment_name, min_nAUC_to_beConsideredGrowing):

    """Plots a heatmap with the susceptibility data for each fitness estimate and drug"""

    # make outdir
    make_folder(plots_dir_all)

    # define the drugs
    all_drugs = sorted(set(susceptibility_df.drug))

    # make one plot for each drug and fitness_estimate
    for drug in all_drugs:
        print_with_runtime("Plotting susceptibility heatmaps for drug=%s..."%(drug))

        relative_fitness_estimates = ["%s_rel"%f for f in fitness_estimates]
        for fitness_estimate in relative_fitness_estimates:

            # define filename
            plots_dir = "%s/%s"%(plots_dir_all, drug); make_folder(plots_dir)
            filename = "%s/%s_susceptibility_heatmap_by_%s.pdf"%(plots_dir, drug, fitness_estimate.replace("_rel", ""))

            if file_is_empty(filename):

                # get the simplified susceptibility_df, with one strain for eacg
                simple_susceptibility_df = susceptibility_df[(susceptibility_df.fitness_estimate==fitness_estimate) & (susceptibility_df.drug==drug)].groupby(["strain"]).apply(get_row_simple_susceptibility_df_one_strain_and_drug).reset_index(drop=True)

                # make clustermap
                df_plot = simple_susceptibility_df[["median_rAUC", "median_MIC50", "median_SMG-MIC50", "strain"]].set_index("strain")
                df_plot_nonans = df_plot.applymap(convert_nans_to_0s)

                # create the df to plot that is compatible with zscore
                df_plot_nonans_zscore = pd.DataFrame(index=df_plot_nonans.index)
                for col in df_plot_nonans.columns:
                    if len(df_plot_nonans[col].unique()) == 1: df_plot_nonans_zscore[col] = 0
                    else: df_plot_nonans_zscore[col] = scipy.stats.zscore(df_plot_nonans[col])

                # init clustermap with the z-score of the three values, so that the strains are clustered based on that
                g = sns.clustermap(df_plot_nonans_zscore, row_cluster=True, col_cluster=False, linecolor="gray", linewidth=0)
                ordered_strains = [s.get_text() for s in g.ax_heatmap.get_yticklabels()]

                # change positions
                hm_height_multiplier = 0.04
                hm_width_multiplier = 0.04
                distance_btw_boxes = 0.01
                rd_width = 0.08
                cbar_width = 0.04

                hm_height = len(df_plot)*hm_height_multiplier
                hm_width = len(df_plot.columns)*hm_width_multiplier

                hm_pos = g.ax_heatmap.get_position()
                cb_pos = g.ax_cbar.get_position()
                hm_y0 = cb_pos.y1 - hm_height
                g.ax_heatmap.set_position([hm_pos.x0, hm_y0, hm_width, hm_height]); hm_pos = g.ax_heatmap.get_position()

                rd_x0 = hm_pos.x0 - rd_width - distance_btw_boxes
                g.ax_row_dendrogram.set_position([rd_x0, hm_pos.y0, rd_width, hm_pos.height]); rd_pos = g.ax_row_dendrogram.get_position()

                # remove colorbar
                g.ax_cbar.remove()
        
                # change axis
                fontsize_all = 16
                max_conc = get_clean_float_value(simple_susceptibility_df.max_concentration.iloc[0])


                estimate_to_label = {"median_rAUC":"rAUC$_{%s}$"%max_conc, "median_MIC50":"MIC$_{50}$", "median_SMG-MIC50":"SMG$_{50}$"}
                g.ax_heatmap.set_xticklabels([estimate_to_label[e] for e in df_plot.columns], rotation=90, fontsize=fontsize_all)
                g.ax_heatmap.set_yticklabels(ordered_strains, fontsize=fontsize_all)
                g.ax_heatmap.set_xlabel("")
                g.ax_heatmap.set_ylabel("strain", fontsize=fontsize_all)
                g.ax_heatmap.set_title(experiment_name+"\n", fontsize=fontsize_all)

                # create the axes for the heatmaps
                cbar_w = hm_height_multiplier*0.9
                cbar_h = hm_height_multiplier*3
                
                x0_cax = rd_pos.x0-distance_btw_boxes-3*cbar_w
                y1_rd = rd_pos.y0+rd_pos.height

                rAUC_cax = g.fig.add_axes([x0_cax, y1_rd - cbar_h, cbar_w, cbar_h])
                MIC_cax = g.fig.add_axes([x0_cax, y1_rd - 2*cbar_h - (distance_btw_boxes)*6, cbar_w, cbar_h])
                SMG_cax = g.fig.add_axes([x0_cax, y1_rd - 3*cbar_h - (2*distance_btw_boxes)*6, cbar_w, cbar_h])

                # change things for each field
                for Ic, (estimate, palette, cax) in enumerate([("rAUC", "gray_r", rAUC_cax), ("MIC50", "Blues", MIC_cax), ("SMG-MIC50","Reds", SMG_cax)]):

                    # get the cmap
                    sorted_vals = sorted(set(df_plot_nonans["median_%s"%estimate]).union({0}))
                    val_to_color = get_value_to_color(sorted_vals, palette=palette, n=len(sorted_vals), type_color="hex", center=None)[0]

                    # go through each strain
                    for Ir, strain in enumerate(ordered_strains):

                        # add the rectangle for the median
                        val = df_plot.loc[strain, "median_%s"%estimate]
                        if pd.isna(val): color = "white"
                        else: color = val_to_color[val]

                        rect = patches.Rectangle((Ic, Ir), 1, 1, linewidth=.5, edgecolor='gray', facecolor=color)
                        g.ax_heatmap.add_patch(rect)

                        # add things to each heatmap
                        df = simple_susceptibility_df[(simple_susceptibility_df.strain==strain)]
                        if len(df)==0: continue
                        if len(df)!=1: raise ValueError("df should be 1")
                        r = df.iloc[0]

                        # add text for few replicates
                        if r["replicates_%s"%estimate] in {0, 1}: g.ax_heatmap.text(Ic+0.5, Ir+0.5, {0:"X", 1:"1"}[r["replicates_%s"%estimate]], color=get_annotationColor_on_bgcolor(color), fontsize=fontsize_all, horizontalalignment="center", verticalalignment="center")

                        # for more replicates, add circles for MAD
                        else:
                            lower_bound_median = max([0, r["median_%s"%estimate] - r["mad_%s"%estimate]])
                            upper_bound_median = r["median_%s"%estimate] + r["mad_%s"%estimate]
                            for Iv, val in enumerate([lower_bound_median, upper_bound_median]): 

                                g.ax_heatmap.scatter([Ic+0.33*(1+Iv)], [Ir+0.5], edgecolor="gray", facecolor=val_to_color[find_nearest(np.array(sorted(set(val_to_color.keys()))), val)],  s=25, linewidth=.4, zorder=2)

                    # add colorbar
                    cmap = plt.get_cmap(palette)
                    norm = plt.Normalize(vmin=0, vmax=max(sorted_vals))
                    cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, ticks=[get_clean_float_value(y) for y in np.linspace(0, max(sorted_vals), 3)])
                    cb.ax.tick_params(labelsize=fontsize_all-4)
                    cax.set_title(estimate_to_label["median_%s"%estimate], fontsize=fontsize_all, pad=10, loc="center")
                    #cb.set_label(estimate_to_label["median_%s"%estimate], fontsize=fontsize_all, rotation=270, labelpad=-1)
                    cb.outline.set_visible(False)


                # add description at the bottom
                description = "rAUC (max [%s]=%s), 50%s Minimum Inhibitory Concentration (MIC)\nand Supra-MIC Growth (SMG) based on fitness estimate '%s'\nSquares: Median; Circles: MAD; 1: One replicate; X: Not available\n\n"%(drug, max_conc, "%", fitness_estimate.replace("_rel", ""))

                description += get_fe_description(fitness_estimate.replace("_rel", ""), 'only_correct_spots', min_nAUC_to_beConsideredGrowing)
                g.ax_heatmap.text(0, len(df_plot) + 3 + (len(description.split("\n"))*0.5), description, horizontalalignment='left', verticalalignment='bottom')

                filename_tmp = "%s.tmp.pdf"%filename
                g.savefig(filename_tmp,  format='pdf', bbox_inches="tight")
                os.rename(filename_tmp, filename)

def plot_heatmaps_concentration_vs_fitness_one_drug_and_fitness_estimate(df_fit, filename, all_strains, fitness_estimate, drug, min_nAUC_to_beConsideredGrowing, experiment_name):

    """Plots the heatmap for one drug and fitness estimate"""

    # skip
    if not file_is_empty(filename): return

    # set parms
    matplotlib.use('Agg')
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42

    # get the number of strains and colors
    nstrains = len(all_strains)

    # define a df with the median and mad across replicates
    if len(df_fit[["concentration", "strain", "row", "column"]].drop_duplicates())!=len(df_fit): raise ValueError("df_fit should be unique")

    def get_r_fit_per_strain_one_conc_and_strain(df): 
        mad_fe = scipy.stats.median_absolute_deviation(df[fitness_estimate])
        median_fe = np.median(df[fitness_estimate])
        upper_bound_median = median_fe + mad_fe
        lower_bound_median = max([0, median_fe-mad_fe])

        return pd.Series({"concentration":df.iloc[0].concentration, "strain":df.iloc[0].strain, "median %s"%fitness_estimate : median_fe, "lower_bound_median":lower_bound_median, "upper_bound_median":upper_bound_median, "# replicates":len(df)})

    df_fit_per_strain = df_fit[["concentration", "strain", "row", "column", fitness_estimate]].groupby(["concentration", "strain"]).apply(get_r_fit_per_strain_one_conc_and_strain).reset_index(drop=True)

    # map nans to 0
    def get_nan_to_0(x):
        if pd.isna(x): return 0
        else: return x

    # get square df
    fontsize_all = 16
    sorted_concentrations = sorted(set(df_fit_per_strain.concentration))
    df_plot = df_fit_per_strain.pivot(index="strain", columns="concentration", values="median %s"%fitness_estimate)[sorted_concentrations].applymap(get_nan_to_0)

    # define the annot df to flag weird concentrations
    def get_annot_for_n_reps(x):
        if pd.isna(x): return "X"
        elif x==1: return "1"
        elif (type(x)==int or int(x)==x) and x>1: return ""
        else: raise ValueError("invalid x: %s"%x)

    df_annot = df_fit_per_strain.pivot(index="strain", columns="concentration", values="# replicates").loc[df_plot.index, df_plot.columns].applymap(get_annot_for_n_reps)

    # get clustermap
    max_val = max(df_fit_per_strain.upper_bound_median)
    g = sns.clustermap(df_plot, row_cluster=True, col_cluster=False, cmap="rocket_r", linecolor="gray", linewidth=0.5, cbar_kws={'label': "median(%s)"%fitness_estimate}, vmin=0, vmax=max_val, annot=df_annot, annot_kws={"size": 13}, fmt="")

    # map the value to color
    all_vals = sorted(get_uniqueVals_df(df_fit_per_strain[["median %s"%fitness_estimate, "upper_bound_median", "lower_bound_median"]]))
    val_to_color = get_value_to_color(all_vals, palette="rocket_r", n=len(all_vals), type_color="hex", center=None)[0]

    # get the ordered ytick labels as in g
    ordered_strains = [s.get_text() for s in g.ax_heatmap.get_yticklabels()]

    # add the MAD for strains with >1 replicate
    for Ic, conc in enumerate(sorted_concentrations):
        for Is, strain in enumerate(ordered_strains):

            # get row of df_fit_per_strain
            df = df_fit_per_strain[(df_fit_per_strain.concentration==conc) & (df_fit_per_strain.strain==strain)]
            if len(df)==0: continue
            if len(df)!=1: raise ValueError("df should be 1")
            r = df.iloc[0]
            if r["# replicates"]<2: continue

            for Iv, val in enumerate([r.lower_bound_median, r.upper_bound_median]): g.ax_heatmap.scatter([Ic+0.33*(1+Iv)], [Is+0.5], edgecolor="gray", facecolor=val_to_color[val],  s=25, linewidth=.4)

    # change positions
    hm_height_multiplier = 0.04
    hm_width_multiplier = 0.04
    distance_btw_boxes = 0.01
    rd_width = 0.08
    cbar_width = 0.04

    hm_height = len(df_plot)*hm_height_multiplier
    hm_width = len(df_plot.columns)*hm_width_multiplier

    hm_pos = g.ax_heatmap.get_position()
    cb_pos = g.ax_cbar.get_position()
    hm_y0 = cb_pos.y1 - hm_height
    #hm_y0 = (hm_pos.y0+hm_pos.height)-hm_height
    g.ax_heatmap.set_position([hm_pos.x0, hm_y0, hm_width, hm_height]); hm_pos = g.ax_heatmap.get_position()

    rd_x0 = hm_pos.x0 - rd_width - distance_btw_boxes
    g.ax_row_dendrogram.set_position([rd_x0, hm_pos.y0, rd_width, hm_pos.height]); rd_pos = g.ax_row_dendrogram.get_position()

    cbar_height = hm_height_multiplier*4
    g.ax_cbar.set_position([rd_pos.x0 - rd_width - distance_btw_boxes*8, rd_pos.y0 + hm_pos.height - cbar_height,cbar_width, cbar_height])

    # labels
    g.ax_heatmap.set_xticklabels(sorted_concentrations, rotation=90, fontsize=fontsize_all)
    g.ax_heatmap.set_yticklabels(ordered_strains, fontsize=fontsize_all)
    g.ax_heatmap.set_xlabel("[%s]"%drug, fontsize=fontsize_all)
    g.ax_heatmap.set_ylabel("strain", fontsize=fontsize_all)
    g.ax_cbar.set_yticklabels([y.get_text() for y in g.ax_cbar.get_yticklabels()], fontsize=fontsize_all)
    g.ax_cbar.set_ylabel(fitness_estimate, fontsize=fontsize_all)

    # add title
    g.ax_heatmap.set_title(experiment_name+"\n", fontsize=fontsize_all)

    # add description at the bottom
    description = "[%s] vs fitness (estimated by '%s')\nSquares: Median; Circles: MAD; 1: One replicate; X: Not available\n\n"%(drug, fitness_estimate)

    description += get_fe_description(fitness_estimate, 'only_correct_spots', min_nAUC_to_beConsideredGrowing)
    g.ax_heatmap.text(0, len(df_plot) + 3 + (len(description.split("\n"))*0.5), description, horizontalalignment='left', verticalalignment='bottom')

    # save
    filename_tmp = "%s.tmp.pdf"%filename
    g.savefig(filename_tmp,  bbox_inches="tight")
    #plt.close(g)
    os.rename(filename_tmp, filename)


def plot_heatmaps_concentration_vs_fitness(df_fitness_measurements, plots_dir_all, fitness_estimates, pseudocount_log2_concentration, min_nAUC_to_beConsideredGrowing, experiment_name):

    """For each drug and fe, make a heatmap where the rows are strains and the columns are concentrations."""

    # make outdir
    make_folder(plots_dir_all)

    # filter dfs
    df_fitness_measurements = cp.deepcopy(df_fitness_measurements[df_fitness_measurements.idx_correct_rel_estimates])

    # define the drugs and strains
    all_drugs = sorted(set(df_fitness_measurements[df_fitness_measurements.concentration!=0].drug))
    all_strains = sorted(set(df_fitness_measurements.strain))

    # log
    print_with_runtime("Plotting drug-vs-fitness heatmaps...")

    # make one plot for each drug and fitness_estimate
    for drug in all_drugs:

        relative_fitness_estimates = ["%s_rel"%f for f in fitness_estimates]
        for fitness_estimate in (fitness_estimates + relative_fitness_estimates):
            #print_with_runtime("plotting the heatmap for %s-%s"%(drug, fitness_estimate))

            # define filename
            plots_dir = "%s/%s"%(plots_dir_all, drug); make_folder(plots_dir)
            filename = "%s/[%s]_vs_%s_heatmap.pdf"%(plots_dir, drug, fitness_estimate)

            if file_is_empty(filename):

                # get dfs
                df_fit = cp.deepcopy(df_fitness_measurements[(df_fitness_measurements.drug==drug) | (df_fitness_measurements.concentration==0)])
                check_no_nans_series(df_fit[fitness_estimate])

                # get heatmap 
                plot_heatmaps_concentration_vs_fitness_one_drug_and_fitness_estimate(df_fit, filename, all_strains, fitness_estimate, drug, min_nAUC_to_beConsideredGrowing, experiment_name)

def chunks(l, n):
    
    """Yield successive n-sized chunks from a list l"""
    
    for i in range(0, len(l), n):
        yield l[i:i + n]

def get_string_split_every_x_words(x, nwords):

    """Gets a string split every nwords"""

    chunks_lists = chunks(x.split(), nwords)
    return "\n".join(map(lambda c: " ".join(c), chunks_lists))


def get_fe_description(fitness_estimate, type_data, min_nAUC_to_beConsideredGrowing):

    """Gets the fitness estimate description."""

    description = "%s: "%fitness_estimate
    if fitness_estimate.endswith("_rel"): description += fe_to_description[fitness_estimate.split("_rel")[0]]
    else: description += fe_to_description[fitness_estimate]

    if fitness_estimate.endswith("_rel"): description += " (relative to concentration==0)"

    if type_data=="only_correct_spots": description += ". The only spots shown are those used in the susceptibility and relative fitness calculations (non-bad spots, w/ concentration==0 that is growing (nAUC>=%s) and non-bad spot, and w/ <2 concentrations being bad spots)."%min_nAUC_to_beConsideredGrowing

    elif type_data=="all_data": description += ". All spots shown."
    else: raise ValueError("invalid type_data")

    return get_string_split_every_x_words(description, 10)



def plot_growth_at_different_drugs_one_fitness_estimate_and_drug(df_fit, filename, all_strains, fitness_estimate, drug, type_data, min_nAUC_to_beConsideredGrowing, strain_to_repID_to_color, experiment_name):

    """For one fitness estimate and drug, plots the lineplots of conc-vs-fitness"""

    # skip if file already generated
    if not file_is_empty(filename): return

    # set matplotlib parms
    matplotlib.use('Agg')
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42

    # get the sorted concentrations
    sorted_concentrations = sorted(set(df_fit.concentration))

    # add the concentration index
    conc_to_IDX = dict(zip(sorted_concentrations, range(len(sorted_concentrations))))
    df_fit["concentration_idx"] = df_fit.concentration.apply(lambda c: conc_to_IDX[c])

    # define the figure layout depending on the number of strains
    nstrains = len(all_strains)
    ncols = 4
    #nrows = int(nstrains/ncols)+1
    nrows = math.ceil(nstrains/4)
    fig = plt.figure(figsize=(ncols*5, nrows*2.9))

    # define the median fitness estimate
    median_fe_conc0 = np.median(df_fit[df_fit.concentration==0][fitness_estimate])

    # init counters (1-based)
    current_col = 0
    current_row = 0

    # add subplots
    for Is, strain in enumerate(all_strains):

        # update the col and row
        if (Is%ncols)==0: 
            current_col = 1
            current_row += 1
        else: current_col += 1

        # get the subplot
        ax = plt.subplot(nrows, ncols, Is+1)

        # define the dfs
        df_plot = df_fit.loc[{strain}]

        # plot
        repID_to_color = strain_to_repID_to_color[strain]
        ax = sns.lineplot(x="concentration_idx", y=fitness_estimate, data=df_plot, hue="replicateID", style="replicateID", palette=repID_to_color, markers=True)

        # add squared bad spots 
        if type_data=="all_data":

            df_plot_bad = df_plot[~df_plot.idx_correct_rel_estimates]
            for I,r in df_plot_bad.iterrows(): plt.scatter(r.concentration_idx, r[fitness_estimate], s=100, edgecolors=repID_to_color[r.replicateID], facecolors="none", marker="s")

        # remove legend
        #ax.get_legend().remove()
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))

        # add lines
        lines_y = [0, 0.5, 1]
        if median_fe_conc0>1: lines_y.append(median_fe_conc0)
        for y in lines_y: plt.axhline(y, color="gray", linestyle="--", linewidth=0.7)

        # change the xtciks to have actual concentrations
        #ax.set_xticks([np.log2(x+pseudocount_log2_concentration) for x in sorted_concentrations])
        ax.set_xticks(sorted(conc_to_IDX.values()))
        ax.set_xticklabels([get_clean_float_value(x) for x in sorted_concentrations], rotation=90)

        # get the description of the fitness estimate
        description = get_fe_description(fitness_estimate, type_data, min_nAUC_to_beConsideredGrowing)

        # add to description
        if type_data=="all_data": description += "\nOutlined spots were discarded in susceptibility and relative fitness analyses."

        # add axes
        if Is==2: ax.set_title("%s\n\n%s"%(experiment_name, strain))
        else: ax.set_title(strain)  

        # add xlabel
        ax.set_xlabel("[%s]"%drug)

        # in the first col of the last row, add text
        if current_col==1 and current_row==nrows:
            upper_ylim = ax.get_ylim()[1]
            ax.text(0, - (2.2*upper_ylim), description, horizontalalignment='left', verticalalignment='bottom')

    # adjust
    plt.subplots_adjust(wspace=0.6, hspace=0.9)

    # save
    filename_tmp = "%s.tmp.pdf"%filename
    fig.savefig(filename_tmp, bbox_inches='tight')
    plt.close(fig)
    os.rename(filename_tmp, filename)



def plot_growth_at_different_drugs(df_fitness_measurements, plots_dir_all, fitness_estimates, min_nAUC_to_beConsideredGrowing, pseudocount_log2_concentration, experiment_name, type_data="only_correct_spots", only_absolute_estimates=False):

    """
    
    Plots, for each drug and fitness estimate, the growith curves. Note that df_fitness_measurements has the following measures:
    
    """

    # make outdir
    make_folder(plots_dir_all)

    # map each replicateID to a color
    strain_to_repID_to_color = {}
    for s in sorted(set(df_fitness_measurements.strain)):
        all_reps = sorted(set(df_fitness_measurements[df_fitness_measurements.strain==s].replicateID))

        if len(all_reps)<=10: palette_reps = "tab10"
        else: palette_reps = "tab20"
        strain_to_repID_to_color[s] = get_value_to_color(all_reps, palette=palette_reps, n=len(all_reps), type_color="hex")[0]

    # filter dfs
    if type_data=="only_correct_spots": df_fitness_measurements = cp.deepcopy(df_fitness_measurements[df_fitness_measurements.idx_correct_rel_estimates])
    elif type_data=="all_data": df_fitness_measurements = cp.deepcopy(df_fitness_measurements)
    else: raise ValueError("invalid type_data")

    # keep less strains and concs DEBUG
    #df_fitness_measurements = df_fitness_measurements[(df_fitness_measurements.concentration<0.2)]
    #df_fitness_measurements = df_fitness_measurements[(df_fitness_measurements.strain.isin({ "Cp-wt2", "Cp-wt1", "Ct-wt", "H20"}))]

    # define the drugs and strains
    all_drugs = sorted(set(df_fitness_measurements[df_fitness_measurements.concentration!=0].drug))
    all_strains = sorted(set(df_fitness_measurements.strain))

    # define the quadrant in the plate
    df_fitness_measurements["plate_quadrant"] = df_fitness_measurements.apply(get_plate_quadrant, axis=1)   

    # define the inputs of the parallel function
    inputs_fn = []

    # log
    print_with_runtime("plotting drug-vs-fitness curves (%s)..."%(type_data))

    # make one plot for each drug and fitness_estimate
    for drug in all_drugs:

        relative_fitness_estimates = ["%s_rel"%f for f in fitness_estimates]
        for fitness_estimate in (fitness_estimates + relative_fitness_estimates):

            if only_absolute_estimates is True and fitness_estimate.endswith("_rel"): continue

            # define filename
            plots_dir = "%s/%s"%(plots_dir_all, drug); make_folder(plots_dir)
            filename = "%s/[%s]_vs_%s_lines_%s.pdf"%(plots_dir, drug, fitness_estimate, {"all_data":"all", "only_correct_spots":"only_correct"}[type_data])

            if file_is_empty(filename):

                # get dfs
                df_fit = cp.deepcopy(df_fitness_measurements[(df_fitness_measurements.drug==drug) | (df_fitness_measurements.concentration==0)].set_index("strain"))
                df_fit["drug"] = drug

                # load inputs_fn
                inputs_fn.append((df_fit, filename, all_strains, fitness_estimate, drug, type_data, min_nAUC_to_beConsideredGrowing, strain_to_repID_to_color, experiment_name))

    # run in parallel
    if len(inputs_fn)>0: run_function_in_parallel(inputs_fn, plot_growth_at_different_drugs_one_fitness_estimate_and_drug, ntries=2)

def run_function_in_parallel(inputs_fn, parallel_fun, ntries=1):

    """Runs any function in parallel"""

    # init float that indicates if it worked
    fun_worked = False

    # try some times
    for tryI in range(1, ntries+1):

        try:

            # run
            with multiproc.Pool(multiproc.cpu_count()) as pool:

                pool.starmap(parallel_fun, inputs_fn, chunksize=1)
                pool.close()
                pool.terminate()

            # keep that it worked
            fun_worked = True
            break

        except Exception as err:

            # if it is the last one, print and error
            if tryI==ntries: 
                traceback.print_tb(err.__traceback__)
                raise ValueError("Function %s did not work. Check the error traceback above."%(parallel_fun))

    # debug. If you arrived here it should have worked
    if fun_worked is False: raise ValueError("Function did not work")

def get_only_element_of_list(x):

    """Takes a list with only one element"""

    if len(x)!=1: raise ValueError("list should have 1 element")
    return x[0]


def parse_excel_positions_plate_layout(df_all):

    """Gets the raw excel dataframe and gets the upper-most position of each interesting table"""

    # init vars
    n_plate_batch = 0
    n_strains_pos = 0
    compounds_pos = concentrations_pos = bad_spots_pos = strains_pos = None

    # iterate through rows and columns
    for Ir in df_all.index:
        for Ic in df_all.columns:
            val = df_all.loc[Ir, Ic]

            # the plate batch defines some tables
            if val=="plate_batch": 
                n_plate_batch+=1

                if n_plate_batch==1: compounds_pos = (Ir, Ic)
                elif n_plate_batch==2: concentrations_pos = (Ir, Ic)
                elif n_plate_batch==3: bad_spots_pos = (Ir, Ic)


            # define the strains pos
            if concentrations_pos is None: continue # it is below the concentrations

            if df_all.loc[Ir-1, Ic]=="1" and df_all.loc[Ir-3, Ic]=="Strains distribution" and df_all.loc[Ir, Ic-1]=="A":

                # validate that there are 12 columns
                if list(df_all.loc[Ir-1, list(range(Ic, Ic+12))])==list(map(str, range(1, 13))):

                    # validate that there are 8 rows A-H
                    if list(df_all.loc[list(range(Ir, Ir+8)), Ic-1])==['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                        n_strains_pos+=1
                        strains_pos = (Ir, Ic)

    # checks
    if n_plate_batch!=3: raise ValueError("There should be 3 cells named plate_batch in plate layout")
    if n_strains_pos!=1: raise ValueError("There can be only one position with strains")
    list_results = (compounds_pos, concentrations_pos, bad_spots_pos, strains_pos)
    if any([x is None for x in list_results]): raise ValueError("There are none values in %s"%(str(list_results)))

    return list_results

def get_df_drugs(df_all, comp, conc):

    """Gets a df with plate_batch, plate, drug, concentration. It takes the excel with all files and the compounds and concentrations locations"""

    # get the plate batches and make sure that they are the same in compounds and concentrations
    plate_batches_comp = []
    for val in df_all.loc[comp[0]+1:, comp[1]]:
        if val=="nan": break
        plate_batches_comp.append(val)

    plate_batches_conc = []
    for val in df_all.loc[conc[0]+1:, conc[1]]:
        if val=="nan": break
        plate_batches_conc.append(val)

    if plate_batches_comp!=plate_batches_conc: raise ValueError("the plate_batches are not the same between compounds and concentrations layouts")

    # fill the df_drugs
    df_drugs = pd.DataFrame()
    for Ib, plate_batch in enumerate(plate_batches_comp):
        for plate in range(1, 5):

            drug = df_all.loc[comp[0]+Ib+1, comp[1]+plate]
            concentration = df_all.loc[conc[0]+Ib+1, conc[1]+plate]

            if drug=="nan" and concentration=="nan": continue
            elif drug=="nan" and concentration!="nan":  raise ValueError("compounds and concentrations layouts do not match")
            elif drug!="nan" and concentration=="nan":  raise ValueError("compounds and concentrations layouts do not match")

            row_drugs = pd.DataFrame({0:{"plate_batch":plate_batch, "plate":plate, "drug":drug, "concentration":concentration}}).transpose()
            df_drugs = df_drugs.append(row_drugs).reset_index(drop=True)


    # formats
    df_drugs["concentration"] = df_drugs["concentration"].apply(lambda x: str(x).replace(",", ".")) # format as floats the concentration

    for f, function_format in [("plate_batch", str), ("plate", int), ("drug", str), ("concentration", float)]: 
        try: df_drugs[f] = df_drugs[f].apply(function_format)
        except: raise ValueError("The '%s' should be formatable as %s"%(f, function_format))

    # checks
    strange_plates = set(df_drugs.plate).difference({1, 2, 3, 4})
    if len(strange_plates)>0: raise ValueError("There are strainge numbers in plate: %s"%strange_plates)

    return df_drugs

def get_df_strains_layout(df_all, strains_pos):

    """Gets df strains layout in 96-well-plate"""

    # init df
    df_strains_layout = pd.DataFrame(index=list("ABCDEFGH"), columns=list(range(1, 13)))

    # add from df_all and strains_pos
    for Ir, row in enumerate(df_strains_layout.index):
        for Ic, col in enumerate(df_strains_layout.columns):

            strain_name = df_all.loc[strains_pos[0]+Ir, strains_pos[1]+Ic].lstrip().rstrip()
            df_strains_layout.loc[row, col] = strain_name

            # checks
            if strain_name in {"nan", "", '0'}: raise ValueError("We found a strain called '%s'. There can't be empty cells in the 96-strain grid of the plate layout. If you have empty spots, specify them as 'H2O' or 'empty'. Note that '0' counts also as empty cell."%(strain_name))

    # change index
    df_strains_layout.index = list(range(1, 9))

    return df_strains_layout

def get_df_plate_layout_long_with_bad_spots(df_plate_layout_long, df_all, bad_spots_pos):

    """Adds the bad spot as a True/False from df_all"""

    # define the number of bad spots
    all_plate_batches = set(df_plate_layout_long.plate_batch)
    set_nbadspots = {len([x for x in df_all.loc[bad_spots_pos[0]+1:, bad_spots_pos[1]+I].values if x!="nan"]) for I in range(4)}
    if len(set_nbadspots)!=1: raise ValueError("The bad_spots are not properly formatted. Make sure that it is a table with non-empty cells.")
    n_badspots = next(iter(set_nbadspots))

    if n_badspots>0:

        # load the df with the bad spots and format
        df_bad_spots = df_all.loc[bad_spots_pos[0]+1:bad_spots_pos[0]+1+n_badspots, bad_spots_pos[1]:bad_spots_pos[1]+3].reset_index(drop=True)
        for Ir, r in df_bad_spots.iterrows():
            if any(r.apply(str)=="nan"): raise ValueError("There are empty cells in the bad spots, which is not allowed")

        # change the columns
        df_bad_spots.columns = ["plate_batch", "plate", "row", "column"]

        # check the rows
        letter_to_number = dict(zip(list("ABCDEFGH"), range(1,9)))
        strange_rows = set(df_bad_spots["row"]).difference(set(letter_to_number))
        if len(strange_rows)>0: raise ValueError("Error in plate layout. In the bad spots, there are strange rows: %s. The rows should be A-H letters."%(strange_rows))

        # change rows to numbers
        df_bad_spots["row"] = df_bad_spots.row.apply(lambda x: letter_to_number[x])

        for f, function_format in [("plate_batch", str), ("plate", int), ("row", int), ("column", int)]: 
            try: df_bad_spots[f] = df_bad_spots[f].apply(function_format)
            except: raise ValueError("The '%s' should be formatable as %s"%(f, function_format))

        # checks
        for k in df_bad_spots.keys():
            strange_values = set(df_bad_spots[k]).difference(set(df_plate_layout_long[k]))
            if len(strange_values)>0: raise ValueError("Error in plate layout. In the bad spots, there are strange values in %s: %s. Make sure that the bad spots have the same values of %s as the 'Compunds' and 'Concentrations'."%(k, strange_values, k))

        # merge
        df_bad_spots["bad_spot"] = True
        df_plate_layout_long = df_plate_layout_long.merge(df_bad_spots.drop_duplicates(), on=["plate_batch", "plate", "row", "column"], how="left", validate="one_to_one")

        def get_nan_to_False(x):
            if pd.isna(x): return False
            else: return True
        df_plate_layout_long["bad_spot"] = df_plate_layout_long.bad_spot.apply(get_nan_to_False)

    else: df_plate_layout_long["bad_spot"] = False

    # log
    print_with_runtime("There are %i manually-defined bad spots that will be removed from the analysis"%(sum(df_plate_layout_long.bad_spot)))

    return df_plate_layout_long


def get_df_plate_layout_and_all_drugs(plate_layout_file, images_dir):


    """Loads a df with the plate layout and also returns all the drugs to test. Also tests if everything is correct. The plate layout is the excel with complex lines and rows."""

    #print("Parsing plate layout...")

    # parse excel and get initial positions of the different tables
    df_all = pd.read_excel(plate_layout_file).reset_index(drop=True).applymap(str)
    df_all.columns = list(range(len(df_all.columns)))
    compounds_pos, concentrations_pos, bad_spots_pos, strains_pos = parse_excel_positions_plate_layout(df_all)

    # define the experiment name
    header_name_exp = df_all.loc[1, 10]
    if header_name_exp!="Name of the experiment": raise ValueError("The row 2, column 11 of the plate layout should contain a cell called 'Name of the experiment', which is not the case. This suggests that the plate layout is not properly formatted. This cell contains this: '%s'"%header_name_exp)

    experiment_name = str(df_all.loc[3, 10]).rstrip().lstrip()
    if experiment_name in {"nan", ""}: experiment_name = "Q-PHAST-experiment"
    experiment_name = str(experiment_name)
    print_with_runtime("The experiment name is '%s'"%experiment_name)

    # define the df_drugs as in the old setting
    df_drugs = get_df_drugs(df_all, compounds_pos, concentrations_pos)

    # check that the concentrations are unique
    if len(df_drugs[["drug", "concentration"]].drop_duplicates())!=len(df_drugs): raise ValueError("In the plate layout, the combination of drug & concentration is not unique. There should be only one plate for any given drug and concentration.")

    # define whether to measire susceptibility as a function of the concentrations
    measure_susceptibility = True
    if sum(df_drugs.concentration==0)==0: 
        #print("WARNING: There are no concentration==0 plates. Skipping the susceptibility measurements.")
        measure_susceptibility = False

    elif sum(df_drugs.concentration==0)!=1: raise ValueError("There should be only one plate with a concentration of 0.0")
    if sum(df_drugs.concentration!=0)==0: raise ValueError("there have to be some non-0 concentrations")

    # define the df_strains_layout (which has the strains in the 96-well-plate layout)
    df_strains_layout = get_df_strains_layout(df_all, strains_pos)

    # create the long df for the plate
    df_plate_layout_long_core = pd.concat([pd.DataFrame({"column":[col]*8, "strain":df_strains_layout[col], "row":list(df_strains_layout.index)}) for col in df_strains_layout.columns]).sort_values(by=["row", "column"]).reset_index(drop=True)

    # create a single df_plate_layout_long with a copy of df_plate_layout_long_core for each combination of plate_batch, plate
    def get_df_plate_layout_long_one_row_df_drugs(r):
        df = cp.deepcopy(df_plate_layout_long_core)
        for f in r.keys(): df[f] = r[f]
        return df
    df_plate_layout_long = pd.concat([get_df_plate_layout_long_one_row_df_drugs(r) for I,r in df_drugs.iterrows()])

    # add the 'bad_spot', which allows tunning
    df_plate_layout_long = get_df_plate_layout_long_with_bad_spots(df_plate_layout_long, df_all, bad_spots_pos)

    # checks
    if len(df_plate_layout_long)!=len(df_plate_layout_long.drop_duplicates()): raise ValueError("The df should be unique")

    # format
    df_plate_layout_long = df_plate_layout_long[["plate_batch", "plate", "row", "column", "strain", "drug", "concentration", "bad_spot"]].reset_index(drop=True)

    # debugs
    for f, expected_values in [("plate", set(range(1, 5))), ("row", set(range(1, 9))), ("column", set(range(1, 13)))]:
        strange_vals = set(df_plate_layout_long[f]).difference(expected_values)
        if len(strange_vals)>0: raise ValueError("There are strange values in %s: %s"%(f, strange_vals))

    for plate_batch in set(df_plate_layout_long.plate_batch):
        if not os.path.isdir("%s/%s"%(images_dir, plate_batch)): raise ValueError("The subfolder <images>/%s should exist. Make sure that there is one sub-folder with images for each plate batch (specified in the plate layout) inisde the input folder."%plate_batch)

    # define all the drugs
    all_drugs = sorted(set(df_plate_layout_long[df_plate_layout_long.concentration!=0.0].drug))

    # more debugs on drugs
    if measure_susceptibility is True and len(df_plate_layout_long[df_plate_layout_long.concentration==0.0])!=96: raise ValueError("There should be only one plate batch with concentration==0")


    for d in all_drugs:
        df_d = df_plate_layout_long[(df_plate_layout_long.drug==d) & (df_plate_layout_long.concentration!=0)]
        set_strainTuples = {tuple(df_d[df_d.concentration==conc].strain) for conc in set(df_d.concentration)}

        if len(set_strainTuples)!=1: raise ValueError("ERROR: This script expects the strains in each spot to be the same in all analyzed plates of the same drug. This did not happen for drug=%s. Check the provided plate layouts."%d)

        if measure_susceptibility is True:
            tuple_strains_no_drug = tuple(df_plate_layout_long[df_plate_layout_long.concentration==0].strain)
            if next(iter(set_strainTuples))!=tuple_strains_no_drug: raise ValueError("For drug %s, the strains are not equal to drug==0 (they should be)"%(d))

        for conc in sorted(set(df_d.concentration)):
            if sum(df_d.concentration==conc)!=96: raise ValueError("There should be 96 spots in the df_plate_layout_long with concentration==%s. This is not the case, which may be because you provided multiple plates with this concentration for drug %s, which is not allowed. There should be only one plate with this concentration."%(conc, d))

    return df_plate_layout_long, all_drugs, measure_susceptibility, experiment_name

def get_df_plate_layout_and_all_drugs_from_long_format(plate_layout_file, images_dir):


    """Loads a df with the plate layout and also returns all the drugs to test. Also tests if everything is correct"""

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
        if not os.path.isdir("%s/%s"%(images_dir, plate_batch)): raise ValueError("The subfolder <images>/%s should exist. Make sure that there is one sub-folder with images for each plate batch (specified in the plate layout) inisde the input folder."%plate_batch)


    # define all the drugs
    all_drugs = sorted(set(df_plate_layout[df_plate_layout.concentration!=0.0].drug))

    # more debugs on drugs
    if len(df_plate_layout[df_plate_layout.concentration==0.0])!=96: raise ValueError("There should be only one plate batch (with 96 rows in the plate layout table) with concentration==0")

    tuple_strains_no_drug = tuple(df_plate_layout[df_plate_layout.concentration==0].strain)

    for d in all_drugs:
        df_d = df_plate_layout[(df_plate_layout.drug==d) & (df_plate_layout.concentration!=0)]
        set_strainTuples = {tuple(df_d[df_d.concentration==conc].strain) for conc in set(df_d.concentration)}

        if len(set_strainTuples)!=1: raise ValueError("ERROR: This script expects the strains in each spot to be the same in all analyzed plates of the same drug. This did not happen for drug=%s. Check the provided plate layouts."%d)

        if next(iter(set_strainTuples))!=tuple_strains_no_drug: raise ValueError("For drug %s, the strains are not equal to drug==0 (they should be)"%(d))
    

    return df_plate_layout, all_drugs


def save_folder_as_zip(input_dir_path, zip_filename):

    """Converts a folder to .zip."""

    # init a tmp file
    zip_filename_tmp = "%s.tmp.zip"%zip_filename

    # Create a new zip file and open it in write mode
    with zipfile.ZipFile(zip_filename_tmp, "w") as zip_file:

        # Iterate over all the files and folders in the input directory
        for root, dirs, files in os.walk(input_dir_path):
            for file in files:

                # Add each file in the input directory to the zip file
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, input_dir_path))

    # keep
    delete_folder(input_dir_path)
    os.rename(zip_filename_tmp, zip_filename)
    

def run_analyze_images_process_images(plate_layout_file, images_dir, outdir, enhance_image_contrast):

    """Takes the images and generates processed images that are cropped to be one in each plate"""

    #### LOAD INPUTS ####

    # get plate layout df
    #print_with_runtime("Debugging inputs ...")
    df_plate_layout, all_drugs, measure_susceptibility, experiment_name = get_df_plate_layout_and_all_drugs(plate_layout_file, images_dir)

    # define the tmpdir
    tmpdir = "%s/tmp"%outdir
    make_folder(tmpdir)   

    # create a .zip file that contains a subset of the inputs and 

    # exteded outdir
    extended_outdir = "%s/extended_outputs"%outdir
    make_folder(extended_outdir)

    #####################

    # save the plate layout into extended_outputs
    copy_file(plate_layout_file, "%s/plate_layout.xlsx"%extended_outdir)

    ##### CREATE THE PROCESSED IMAGES #####

    print_with_runtime("Getting processed images ...")
    print_with_runtime("Parsing directories to get images and check that they are properly named...")

    # define dirs
    linked_raw_images_dir = "%s/linked_raw_images"%tmpdir; make_folder(linked_raw_images_dir)
    processed_images_dir = "%s/processed_images"%tmpdir; make_folder(processed_images_dir)
    plate_batch_to_images = {}
    plate_batch_to_raw_images = {}
    plate_batch_to_raw_outdir = {}
    plate_batch_to_processed_outdir = {}
    all_endings = set()

    # init the inputs to softlink images in parallel
    inputs_fn_linking = []
    
    # go through each image
    for plate_batch in sorted(set(df_plate_layout.plate_batch)):

        # define files and 
        processed_images_dir_batch = "%s/%s"%(processed_images_dir, plate_batch)
        linked_raw_images_dir_batch = "%s/%s"%(linked_raw_images_dir, plate_batch)
        raw_images_dir_batch = "%s/%s"%(images_dir, plate_batch)
        plate_batch_to_images[plate_batch] = set()
        plate_batch_to_raw_images[plate_batch] = set()

        # save folders
        plate_batch_to_raw_outdir[plate_batch] = linked_raw_images_dir_batch
        plate_batch_to_processed_outdir[plate_batch] = processed_images_dir_batch

        # make the raw folder with linked images
        #if not os.path.isdir(processed_images_dir_batch): delete_folder(linked_raw_images_dir_batch) # if processed dir is not created, remove (only to debug)
        make_folder(linked_raw_images_dir_batch)

        for f in os.listdir(raw_images_dir_batch): 

            # debug non images
            if f.split(".")[-1].lower() not in allowed_image_endings or f.startswith("."):
                print_with_runtime("WARNING: File <images>/%s/%s not considered as an image. Note that only images ending with %s (and not starting with a '.') are considered"%(plate_batch, f, allowed_image_endings))
                continue

            # define the file ending
            year, month, day, hour, minute = get_yyyymmddhhmm_tuple_one_image_name(f)
            year = str(year)
            month = get_int_as_str_two_digits(month); day = get_int_as_str_two_digits(day)
            hour = get_int_as_str_two_digits(hour); minute = get_int_as_str_two_digits(minute)
            image_name = "img_0_%s%s%s_%s%s"%(year, month, day, hour, minute) # define the name of the image

            # define the ending
            image_ending = f.split(".")[-1].lower(); all_endings.add(image_ending)

            # get the linked image into inputs_fn_linking
            linked_raw_image = "%s/%s.%s"%(linked_raw_images_dir_batch, image_name, image_ending)
            inputs_fn_linking.append(("%s/%s"%(raw_images_dir_batch, f), linked_raw_image))
            
            # get the  processed image
            processed_image = "%s/%s.tif"%(processed_images_dir_batch, image_name) # we save all images as tif after processing

            # keep image
            plate_batch_to_images[plate_batch].add(get_file(processed_image))
            plate_batch_to_raw_images[plate_batch].add(get_file(linked_raw_image))

        # sort images by date
        plate_batch_to_images[plate_batch] = sorted(plate_batch_to_images[plate_batch], key=get_yyyymmddhhmm_tuple_one_image_name)

        plate_batch_to_raw_images[plate_batch] = sorted(plate_batch_to_raw_images[plate_batch], key=get_yyyymmddhhmm_tuple_one_image_name)

    # checks
    if len(all_endings)!=1: raise ValueError("All files should end with the same. These are the endings: %s"%all_endings)

    # linking images
    print_with_runtime("Linking images in parallel on %i threads..."%multiproc.cpu_count())
    run_function_in_parallel(inputs_fn_linking, soft_link_files)

    # log
    start_time_rotation_contrast = time.time()

    # rotate each plate set at the same time (not in parallel)
    for I, plate_batch in enumerate(sorted(plate_batch_to_images)): process_image_rotation_and_contrast_all_images_batch(I+1, len(plate_batch_to_raw_outdir),plate_batch_to_raw_outdir[plate_batch], plate_batch_to_processed_outdir[plate_batch], plate_batch, plate_batch_to_images[plate_batch], image_ending, enhance_image_contrast)

    # log
    #print_with_runtime("Rotating images and Improving contrast took %.3f seconds"%(time.time()-start_time_rotation_contrast))

    #######################################


    ######## CREATE FILE TO REPRODUCE #########
    print("Generating reduced inputs...")

    # create a folder that contains the plate_layout.xlsx and a subset of 4 images for each input file
    reduced_input_dir = "%s/reduced_input_dir"%extended_outdir
    reduced_input_dir_file = "%s.zip"%reduced_input_dir

    if file_is_empty(reduced_input_dir_file):

        # create dir
        delete_folder(reduced_input_dir); make_folder(reduced_input_dir)

        # add the plate layout
        copy_file(plate_layout_file, "%s/plate_layout.xlsx"%reduced_input_dir)

        # copy a subset of images
        for plate_batch, sorted_raw_images in plate_batch_to_raw_images.items():
            subset_images = [sorted_raw_images[int(idx)] for idx in np.linspace(0, len(sorted_raw_images)-1, 4)]
            plate_batch_dir = "%s/%s"%(reduced_input_dir, plate_batch); make_folder(plate_batch_dir)
            for img in subset_images: copy_file("%s/%s/%s"%(linked_raw_images_dir, plate_batch, img), "%s/%s"%(plate_batch_dir, img))

        # compress and save
        save_folder_as_zip(reduced_input_dir, reduced_input_dir_file)

    ###########################################

    ########## CROP IMAGES #########

    print_with_runtime("Cropping images...")

    # define the list of inputs, which will be processed below
    inputs_fn_cropping = []

    # define a folder that will contain the linked images for each individual processing
    processed_images_dir_each_plate = "%s/processed_images_each_plate"%tmpdir; make_folder(processed_images_dir_each_plate)

    # crop the images
    for plate_batch, plate in df_plate_layout[["plate_batch", "plate"]].drop_duplicates().values:
        plateID_to_quadrantName = {1:"upper-left", 2:"upper-right", 3:"lower-left", 4:"lower-right"}

        # crop all the images (only desired quadrant) to a working dir. Only get files        
        processed_images_dir_batch = "%s/%s"%(processed_images_dir, plate_batch)
        dest_processed_images_dir = "%s/%s_plate%i"%(processed_images_dir_each_plate, plate_batch, plate); make_folder(dest_processed_images_dir)
        for f in plate_batch_to_images[plate_batch]: inputs_fn_cropping.append(("%s/%s"%(processed_images_dir_batch, f), "%s/%s"%(dest_processed_images_dir, f), plate))

    # get the cropped images
    #print_with_runtime("Cropping images in parallel on %i threads..."%multiproc.cpu_count())
    run_function_in_parallel(inputs_fn_cropping, generate_croped_image)

    ################################

def run_analyze_images_run_colonyzer(outdir_images):

    """Runs colonyzer on the images that are in outdir_images, which contains 2 images"""

    # define the outdir
    outdir_colonyzer = "%s/outdir_colonyzer"%outdir_images
    delete_folder(outdir_colonyzer); make_folder(outdir_colonyzer)

    # check
    if len(os.listdir(outdir_images))==0: raise ValueError("outdir_one_image can't be empty")

    # clean the hidden files from outdir_one_image
    for f in os.listdir(outdir_images):
        if f.startswith("."): remove_file("%s/%s"%(outdir_one_image, f))

    # move into the images dir
    initial_dir = os.getcwd()
    os.chdir(outdir_images)

    # check 
    if file_is_empty("./Colonyzer.txt"): raise ValueError("Colonyzer.txt should exist in %s"%outdir_images)

    # define the image names that you expect
    image_names_withoutExtension = set({x.split(".")[0] for x in os.listdir(outdir_images) if x.endswith(".tif") and not x.startswith(".")})

    # run colonyzer for all parameters
    run_colonyzer_one_set_of_parms(parms_colonyzer, outdir_colonyzer, image_names_withoutExtension)

    # go back to the initial dir
    os.chdir(initial_dir)

    ############################

def run_analyze_images_run_colonyzer_subset_images_one_plate(processed_images_dir_each_plate, colonyzer_runs_subset_dir, d):

    """Runs colonyzer on one plate (d) from processed_images_dir_each_plate, colonyzer_runs_subset_dir contains the images"""

    # define dirs
    outdir = "%s/%s"%(colonyzer_runs_subset_dir, d) # place where to put the images
    source_dir =  "%s/%s"%(processed_images_dir_each_plate, d) # origin of the images

    if not os.path.isdir(outdir):

        # make tmp folder
        outdir_tmp = "%s_tmp"%outdir
        delete_folder(outdir_tmp); make_folder(outdir_tmp)

        # define the sorted images
        sorted_image_names = sorted({f for f in os.listdir(source_dir) if not f.startswith(".") and f not in {"Colonyzer.txt.tmp", "Colonyzer.txt"}}, key=get_yyyymmddhhmm_tuple_one_image_name)

        # add files in outdir_tmp to get images
        for f in [sorted_image_names[0], sorted_image_names[-1], "Colonyzer.txt"]: soft_link_files("%s/%s"%(source_dir,f), "%s/%s"%(outdir_tmp,f))
        
        # move into the images dir
        initial_dir = os.getcwd()
        os.chdir(outdir_tmp)

        # define the image names that you expect
        image_names_withoutExtension = set({x.split(".")[0] for x in os.listdir(outdir_tmp) if x.endswith(".tif") and not x.startswith(".")})

        # run colonyzer for all parameters
        run_colonyzer_one_set_of_parms(parms_colonyzer, outdir_tmp, image_names_withoutExtension)
        os.rename(outdir_tmp, outdir)

def run_analyze_images_run_colonyzer_subset_images(outdir):

    """Runs colonyzer on a subset of 2 images with the generated Colonyzer.txt file"""

    start_time = time.time()

    # define dirs
    tmpdir = "%s/tmp"%outdir
    processed_images_dir_each_plate = "%s/processed_images_each_plate"%tmpdir
    colonyzer_runs_subset_dir = "%s/colonyzer_runs_subset"%tmpdir; make_folder(colonyzer_runs_subset_dir)

    # define the inputs function to run colonyzer
    inputs_fn = [(processed_images_dir_each_plate, colonyzer_runs_subset_dir, d) for d in os.listdir(processed_images_dir_each_plate)]

    #print_with_runtime("Checking coordinates in parallel on %i threads..."%multiproc.cpu_count())
    run_function_in_parallel(inputs_fn, run_analyze_images_run_colonyzer_subset_images_one_plate)

    # give permissions
    run_cmd("chmod -R 777 %s"%colonyzer_runs_subset_dir)
    #print("colonyzer-based grid check took %.2fs"%(time.time()-start_time))




def is_outlier(L, x, multiplier=2.5):

    """
    Determines whether x is an outlier in L using the interquartile range method.

    Args:
        L (list of floats): The list of floats to check for outliers.
        x (float): The float to check for outlier status.

    Returns:
        bool: True if x is an outlier in L, False otherwise.
    """

    q1, q3 = np.percentile(L, [25, 75])
    iqr = q3 - q1
    lower_threshold = q1 - (multiplier * iqr)
    upper_threshold = q3 + (multiplier * iqr)

    # make sure that it is a max of 0
    lower_threshold = max([lower_threshold, 0])

    # define outlier boolean
    is_outlier_bool = (x < lower_threshold) or (x > upper_threshold)

    return (is_outlier_bool, (lower_threshold, upper_threshold))


def generate_df_w_potential_bad_spots(df_fitness_measurements, min_nAUC_to_beConsideredGrowing):

    """Generate an df with the potential bad spots"""

    # keep
    df_fitness_measurements = cp.deepcopy(df_fitness_measurements)

    # init df with manually-defined bad spots
    num_to_letter = dict(zip(range(1,9), "ABCDEFGH"))
    df_bad_spots = df_fitness_measurements[df_fitness_measurements.bad_spot==True]
    df_bad_spots["row"] = df_bad_spots.row.apply(lambda x: num_to_letter[x])
    df_bad_spots["bad_spot_reason"] = "manual setting in plate layout"

    fields_spot = ["plate_batch", "plate", "drug", "concentration", "row", "column", "strain", "bad_spot_reason"]
    df_bad_spots = df_bad_spots[fields_spot]

    # for the other spots, add them automatically
    df_fitness_measurements = df_fitness_measurements[df_fitness_measurements.bad_spot==False]

    # get automatic bad spots
    def get_bad_spot_reason_one_spot(r, nAUC_list, DT_h_list):

        # if none of them are growing, it can't be a bad spot
        median_nAUC = np.median(nAUC_list)
        if median_nAUC<min_nAUC_to_beConsideredGrowing and r.nAUC<min_nAUC_to_beConsideredGrowing: return ""

        # define a list of reasons that indicate that this could be a bad spot
        reasons_bad_spot = []

        outlier_nAUC, range_nAUC = is_outlier(nAUC_list, r.nAUC)
        #outlier_DT_h, range_DT_h = is_outlier(DT_h_list, r.DT_h)

        if outlier_nAUC==True: reasons_bad_spot.append("nAUC=%.2f outside (%.2f, %.2f)"%(r.nAUC, range_nAUC[0], range_nAUC[1]))
        #if outlier_DT_h==True: reasons_bad_spot.append("DT_h=%.2f outside (%.2f, %.2f)"%(r.DT_h, range_DT_h[0], range_DT_h[1]))

        # if by both measures this is a bad spot
        if len(reasons_bad_spot)==1: return "; ".join(reasons_bad_spot)

        # else it is not
        else: return ""

    def get_df_bad_spots_one_strain_and_plate(df):


        # if there are <3 replicates, return an empty df
        if len(df)<3: return pd.DataFrame(columns=fields_spot) 

        # define if it is a bad spot
        df["bad_spot_reason"] = df[["nAUC", "DT_h"]].apply(get_bad_spot_reason_one_spot, nAUC_list=list(df.nAUC), DT_h_list=list(df.DT_h), axis=1)

        # return bad spots (if any)
        df = df[df.bad_spot_reason!=""]
        return df[fields_spot]

    df_bad_spots_automatic = df_fitness_measurements.groupby(["plate_batch", "plate", "strain"]).apply(get_df_bad_spots_one_strain_and_plate)
    df_bad_spots_automatic["row"] = df_bad_spots_automatic.row.apply(lambda x: num_to_letter[x])

    if len(df_bad_spots_automatic)>0: print_with_runtime("WARNING: We found %i (not defined) potential bad spots. We detected them based on a typical outlier-detection method: the Interquartile Range (IQR, which is Q3-Q1) approach. For each strain, in each plate batch and concentration, we calculated Q1, Q3 and IQR for nAUC. Potential bad spots have nAUC outside the (Q1 - 2.5·IQR, Q3 + 2.5·IQR) range for their strain. This method is approximate, so in a subsequent step you'll need to validate which of these spots are actually bad spots."%(len(df_bad_spots_automatic)))

    # merge
    df_bad_spots = df_bad_spots.append(df_bad_spots_automatic)


    # return
    return df_bad_spots[fields_spot].sort_values(by=["plate_batch", "plate", "strain", "row", "column"])

def make_flat_listOflists(LoL):

    return list(itertools.chain.from_iterable(LoL))

def generate_simplified_fitness_table(fitness_df, fitness_estimates, filename, experiment_name):

    """Genrates a table where each row is one combination of plate_batch, plate, and strain, and it contains summary stats about the fitness estimates, discarding the bad spots"""

    # keep df
    fitness_df = cp.deepcopy(fitness_df)
    fitness_df = fitness_df[~fitness_df.bad_spot]

    # define a function that takes a slice of the df with the strains of one plate, and returns a row with summary stats
    def get_row_simple_fitness_df_one_plate_batch_plate_and_strain(df):

        # checks
        if len(df[["drug", "concentration", "strain"]].drop_duplicates())!=1: raise ValueError("df should be len==1")

        # init dict
        data_dict = {"plate_batch":df.plate_batch.iloc[0], "plate":df.plate.iloc[0], "drug":df.drug.iloc[0], "concentration":df.concentration.iloc[0], "strain":df.strain.iloc[0], "# replicates":len(df)}

        # debug
        if len(df)!=len(set(df.replicateID)): raise ValueError("replicateIDs should be unique")
        for f in fitness_estimates: 
            check_no_nans_series(df[f])
            if any(df[f]==np.inf): raise ValueError("there can't be infs in f")
            if any(df[f]==-np.inf): raise ValueError("there can't be -infs in f")
            if any(df[f]<0): raise ValueError("there can't be <0s in f")

        # go through different fitness_estimates
        for fe in fitness_estimates:

            # round
            all_vals = [float(x) for x in df[fe]]

            # get the range of all replicates and the median
            data_dict["median_%s"%fe] = get_clean_float_value(np.median(all_vals))
            data_dict["mode_%s"%fe] = get_clean_float_value(get_mode(all_vals))
            data_dict["mad_%s"%fe] = get_clean_float_value(scipy.stats.median_absolute_deviation(all_vals))
            data_dict["range_%s"%fe] = "%s-%s"%(get_clean_float_value(min(all_vals)), get_clean_float_value(max(all_vals)))

        return pd.Series(data_dict)


    # get simple fitness df
    simple_fitness_df = fitness_df.groupby(["plate_batch", "plate", "strain"]).apply(get_row_simple_fitness_df_one_plate_batch_plate_and_strain).reset_index(drop=True)

    # write 
    fields_fe = make_flat_listOflists([["median_%s"%fe, "mode_%s"%fe, "mad_%s"%fe, "range_%s"%fe] for fe in fitness_estimates])
    simple_fitness_df["experiment_name"] = experiment_name
    simple_fitness_df = simple_fitness_df[['drug', 'concentration', 'strain', '# replicates', 'experiment_name'] + fields_fe].sort_values(by=['drug', 'concentration', 'strain'], ascending=True)

    save_df_as_tab(simple_fitness_df, filename)
    simple_fitness_df.to_excel("%s.xlsx"%(filename.rstrip(".csv")), index=False)


def get_df_fitness_measurements_with_extra_fields_when_conc0_is_available(fitness_df):

    """Takes the fitness df and adds some fields"""

    # keep
    fitness_df = cp.deepcopy(fitness_df)

    # add whether the concentration 0 is a bad spot or is growing
    fitness_df_conc0 = fitness_df[fitness_df.concentration==0].set_index("replicateID")
    if len(fitness_df_conc0)!=96: raise ValueError("There should be 96 spots with conc==0")

    repID_to_is_growing_conc0 = dict(fitness_df_conc0.is_growing)
    repID_to_is_bad_spots_conc0 = dict(fitness_df_conc0.bad_spot)

    fitness_df["conc0_is_growing"] = fitness_df.replicateID.apply(lambda repID: repID_to_is_growing_conc0[repID])
    fitness_df["conc0_is_bad_spot"] = fitness_df.replicateID.apply(lambda repID: repID_to_is_bad_spots_conc0[repID])

    if len(set(fitness_df.conc0_is_growing).difference({True, False}))>0: raise ValueError("conc0_is_growing should be boolean")
    if len(set(fitness_df.conc0_is_bad_spot).difference({True, False}))>0: raise ValueError("conc0_is_bad_spot should be boolean")

    nspots_conc0_not_growing = len(set(fitness_df[~fitness_df.conc0_is_growing].replicateID))
    nspots_conc0_bad_spot = len(set(fitness_df[fitness_df.conc0_is_bad_spot].replicateID))

    if nspots_conc0_not_growing>0: print_with_runtime("WARNING: There are %i spots where the concentration==0 is not growing. These will be discarded from the susceptibility analysis, and also from the simplified relative fitness table."%nspots_conc0_not_growing)
    if nspots_conc0_bad_spot>0: print_with_runtime("WARNING: There are %i spots where the concentration==0 is a bad spot. These will be discarded from the susceptibility analysis, and also from the simplified relative fitness table."%nspots_conc0_bad_spot)

    # for each spot, define the number of concentrations (not including 0) that are a bad spot
    fitness_df_conc0 = fitness_df[fitness_df.concentration==0]
    fitness_df_conc0["n_non0_concentrations_bad_spot"] = 0

    fitness_df_no_conc0 = fitness_df[fitness_df.concentration!=0]
    initial_len_fitness_df_no_conc0 = len(fitness_df_no_conc0)

    def get_df_with_n_non0_concentrations_bad_spot_one_replicate_and_drug(df):
        if len(set(df.concentration))!=len(df): raise ValueError("concentration should be unique")
        df["n_non0_concentrations_bad_spot"] = sum(df.bad_spot==True)
        return df

    fitness_df_no_conc0 = fitness_df_no_conc0.groupby(["drug", "replicateID"]).apply(get_df_with_n_non0_concentrations_bad_spot_one_replicate_and_drug)
    if initial_len_fitness_df_no_conc0!=len(fitness_df_no_conc0): raise ValueError("fitness_df_no_conc0 changed it's len")

    fitness_df = fitness_df_conc0.append(fitness_df_no_conc0)

    return fitness_df


def save_object(obj, filename):
    
    """ This is for saving python objects """

    filename_tmp = "%s.tmp"%filename
    remove_file(filename_tmp)
    
    with open(filename_tmp, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

    os.rename(filename_tmp, filename)

def load_object(filename):
    
    """ This is for loading python objects  in a fast way"""
    
    return pickle.load(open(filename,"rb"))


def generate_merged_image_test_bad_spot(plate_batch, plate, row, column, df_offsets, df_growth, merged_images_bad_spots_dir, processed_images_dir_each_plate, plate_batch_to_images, box_size):

    """Generates one merged image for a bad spot"""

    # define the final merged image
    final_image = "%s/%s_%s_%s_%s.tif"%(merged_images_bad_spots_dir, plate_batch, plate, row, column)
    if file_is_empty(final_image):

        # checks
        if len(df_offsets[["row", "column"]].drop_duplicates())!=len(df_offsets): raise ValueError("combinations should be unique")
        if len(df_offsets)<3: raise ValueError("There have to be >=3 replicates to infer bad spots")

        ###### CREATE IMAGES ####

        # define images
        all_images = plate_batch_to_images[plate_batch]
        if len(all_images)<3: raise ValueError("There are <3 images for plate_batch %s. This does not allow for a proper analysis"%plate_batch)

        # get subset of images
        subset_images = [all_images[int(idx)] for idx in np.linspace(0, len(all_images)-1, 3)]

        # Open the four images
        dir_images = "%s/%s_plate%i"%(processed_images_dir_each_plate, plate_batch, plate)
        image1 = PIL_Image.open("%s/%s"%(dir_images, subset_images[0]))
        image2 = PIL_Image.open("%s/%s"%(dir_images, subset_images[1]))
        image3 = PIL_Image.open("%s/%s"%(dir_images, subset_images[2]))

        # Get the size of the first input image
        width, height = image1.size
        #compression = image1.info.get('compression', 'tiff_lzw')

        # add the bad spots in the first three quadrants
        for img in [image1, image2, image3]:

            # init draw object
            draw = ImageDraw.Draw(img)

            # one square for each offset
            for I, r in df_offsets.iterrows():

                # define locations
                x = r.XOffset
                y = r.YOffset

                # add rectangle
                if r.row==row and r.column==column: color = "red"
                else: color = "black"
                draw.rectangle((x, y, x + box_size, y + box_size), outline=color, width=8) # x0, y0, x1, y1

        # define a size of the textbox to add ttiles
        size_textbox = int(height/10)

        # Create a new image with the size of the first input image and mode 'RGB'
        merged_image = PIL_Image.new('RGB', (2*width, 2*height + 2*size_textbox), (255, 255, 255))

        # Paste the four input images into the merged image
        merged_image.paste(image1, (0, size_textbox))
        merged_image.paste(image2, (width, size_textbox))
        merged_image.paste(image3, (0, height + size_textbox*2))

        #########################

        ###### CREATE GROWTH CURVES PLOT ######

        # define is potential bad spot
        df_growth["type spot"] = ((df_growth.row==row) & (df_growth.column==column)).map({True:"potential bad spot", False:"other spots"})
        df_growth["spot"] = df_growth.row + df_growth.column.apply(str)


        # checks
        if len(df_growth[["Expt.Time", "spot"]].drop_duplicates())!=len(df_growth): raise ValueError("for each spot there should be one timepoint for one timepoint")

        # init figure to mimic the ones of the images
        dpi = 100
        fig_size = (width/dpi, height/dpi)
        fig = plt.figure(figsize=fig_size)

        # create
        sns.set(font_scale=2)
        df_growth["hours"] = df_growth["Expt.Time"] * 24
        ax = sns.lineplot(data=df_growth, x="hours", y="Growth", hue="type spot", units="spot",  estimator=None, lw=3, palette={"potential bad spot":"red", "other spots":"black"})

        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Cell density (AU)")

        # save
        filename_curves = "%s.growth_curves.png"%final_image
        fig.savefig(filename_curves, bbox_inches='tight', dpi=dpi)
        plt.close(fig)

        # add to the merged image
        image_curves = PIL_Image.open(filename_curves)
        merged_image.paste(image_curves, (width + size_textbox, height + int(size_textbox*2.5)))

        #######################################

        #### ADD TITLES AND SAVE ######

        # add the titles of the images
        draw_merged = ImageDraw.Draw(merged_image)

        # define the font 
        fontsize = int(width/18)
        font = ImageFont.truetype("/opt/conda/envs/main_env/lib/python3.6/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSansMono.ttf", fontsize)

        # define the titles of the four quadrants
        title_texts = []
        for image_name in subset_images:
            day = image_name.split("_")[-2]
            timepoint = image_name.split("_")[-1].split(".")[0]
            title_texts.append("%s/%s/%s, %s:%s"%(day[0:4], day[4:6], day[6:8], timepoint[0:2], timepoint[2:4]))

        # add the title of the curves
        title_texts.append("Growth curves")

        # add titles
        for I,text in enumerate(title_texts):

            # get the text size
            w, h = draw.textsize(text, font=font)

            # get coords
            if I==0:
                text_x = int((width - w) / 2)
                text_y = int((size_textbox - h) / 2)

            elif I==1:
                text_x = width + int((width - w) / 2)
                text_y = int((size_textbox - h) / 2)

            elif I==2:
                text_x = int((width - w) / 2)
                text_y = size_textbox + height + int((size_textbox - h) / 2)

            elif I==3:
                text_x = width + int((width - w) / 2)
                text_y = size_textbox + height + int((size_textbox - h) / 2)
            
            # add 
            draw_merged.text((text_x, text_y), text, fill="black", font=font)

        # generate downsized_image_file
        original_w, original_h = merged_image.size
        factor_resize = 900/original_w
        merged_image = merged_image.resize((int(original_w*factor_resize), int(original_h*factor_resize)))

        # remove the image of the curves
        remove_file(filename_curves)

        # Save the merged image with the same compression level as the first image
        final_image_tmp = "%s.tmp.tif"%final_image
        merged_image.save(final_image_tmp)
        os.rename(final_image_tmp, final_image)

        ###############################

def run_analyze_images_get_fitness_measurements(plate_layout_file, images_dir, outdir, pseudocount_log2_concentration, min_nAUC_to_beConsideredGrowing):

    """Generates the fitness measurements."""

    #### LOAD DATA ####

    # get plate layout df
    df_plate_layout, all_drugs, measure_susceptibility, experiment_name = get_df_plate_layout_and_all_drugs(plate_layout_file, images_dir)

    # define the tmpdir
    tmpdir = "%s/tmp"%outdir
    if not os.path.isdir(tmpdir): raise ValueError("tmpdir should exist")

    # define the extended_outdir
    extended_outdir = "%s/extended_outputs"%outdir
    if not os.path.isdir(extended_outdir): raise ValueError("extended_outdir should exist")

    # define several dirs of the final output
    growth_curves_dir = "%s/growth_curves"%extended_outdir; make_folder(growth_curves_dir) # a dir with a plot for each growth curve

    ###################

    ##### RUN THE IMAGE ANALYSIS PIPELINE FOR EACH PLATE AND PLATE SET #####

    # define the iterable inputs_fn_coords 
    inputs_fn_coords = []
    plate_batch_to_images = {}
    processed_images_dir_each_plate = "%s/processed_images_each_plate"%tmpdir

    # go through each set of processed images
    for d in sorted([x for x in os.listdir(processed_images_dir_each_plate) if not x.startswith(".")]):

        # get full path of the folder with the cropped images
        dest_processed_images_dir = "%s/%s"%(processed_images_dir_each_plate, d)

        # get plate batch and plate and add
        plate_batch, plate = d.split("_plate"); plate = int(plate)    
        inputs_fn_coords.append((dest_processed_images_dir, plate_batch, plate))

        # add the images
        plate_batch_to_images[plate_batch] = sorted({f for f in os.listdir(dest_processed_images_dir) if not f.startswith(".") and f not in {"Colonyzer.txt.tmp", "Colonyzer.txt"}}, key=get_yyyymmddhhmm_tuple_one_image_name)



    # go through each plate and plate set and run the fitness calculations
    outdir_fitness_calculations = "%s/fitness_calculations"%tmpdir; make_folder(outdir_fitness_calculations)
    inputs_fn_fitness = []

    for I, (proc_images_folder, plate_batch, plate) in enumerate(inputs_fn_coords): inputs_fn_fitness.append((I+1, len(inputs_fn_coords), proc_images_folder, "%s/%s_plate%i"%(outdir_fitness_calculations, plate_batch, plate), plate_batch, plate, plate_batch_to_images[plate_batch], cp.deepcopy(df_plate_layout)))

    print_with_runtime("Analyzing images in parallel on %i threads..."%multiproc.cpu_count())
    run_function_in_parallel(inputs_fn_fitness, get_df_integrated_fitness_measurements_one_plate_batch_and_plate)

    # integrate the results of the fitness
    print_with_runtime("Integrating fitness datasets...")

    # define the merging fields
    merge_fields = ["plate_batch", "plate", "row", "column"]

    # define the fields
    df_growth_fields = merge_fields + ['X.Offset', 'Y.Offset', 'Area', 'Trimmed', 'Threshold', 'Intensity', 'Edge.Pixels', 'redMean', 'greenMean', 'blueMean', 'redMeanBack', 'greenMeanBack', 'blueMeanBack', 'Edge.Length', 'Tile.Dimensions.X', 'Tile.Dimensions.Y', 'x', 'y', 'Diameter', 'Date.Time', 'Inoc.Time', 'Timeseries.order', 'Expt.Time', 'Growth']

    df_fitness_measurements = pd.DataFrame()
    df_growth_measurements_all_timepoints = pd.DataFrame()
    for I, (proc_images_folder, plate_batch, plate) in enumerate(inputs_fn_coords): 

        # get the fitness df
        df_fitness_measurements_batch =  get_tab_as_df_or_empty_df("%s/%s_plate%i/integrated_data.tbl"%(outdir_fitness_calculations, plate_batch, plate))
        df_fitness_measurements = df_fitness_measurements.append(df_fitness_measurements_batch)

        # get the growth measurements for all time points
        df_growth_measurements = get_tab_as_df_or_empty_df("%s/%s_plate%i/output_diffims_greenlab_lc/processed_all_data.tbl"%(outdir_fitness_calculations, plate_batch, plate))
        df_growth_measurements["plate_batch"] = plate_batch
        df_growth_measurements["plate"] = plate

        # change
        df_growth_measurements = df_growth_measurements.rename(columns={"Row":"row", "Column":"column"})[df_growth_fields]

        # print nans in blueMeanBack
        df_test = df_growth_measurements[df_growth_measurements[["blueMeanBack", "greenMeanBack", "redMeanBack"]].apply(pd.isna, axis=1).apply(any, axis=1)][["Growth", "Expt.Time"]]
        if len(df_test)>0: raise ValueError("There are NaNs in columns blueMeanBack, greenMeanBack, redMeanBack of df_growth_measurements for %s plate %i. This could be because there are no spots growing in the plate, which means that this plate cannot be analyzed. If this is the case, you may skip this plate by leaving it empty in the plate layout excel."%(plate_batch, plate))

        # keep
        df_growth_measurements_all_timepoints = df_growth_measurements_all_timepoints.append(df_growth_measurements)

        # keep the growth curves in the final output
        copy_file("%s/%s_plate%i/output_diffims_greenlab_lc/output_plots.pdf"%(outdir_fitness_calculations, plate_batch, plate), "%s/batch_%s-plate%i.pdf"%(growth_curves_dir, plate_batch, plate))

    # add the plate layout info
    df_growth_measurements_all_timepoints = df_growth_measurements_all_timepoints.merge(df_plate_layout, how="left", left_on=merge_fields, right_on=merge_fields, validate="many_to_one").reset_index(drop=True)

    # keep some fields and merge the df_fitness_measurements
    df_fitness_measurements = df_fitness_measurements.rename(columns={"Row":"row", "Column":"column"})
    df_fitness_measurements_interesting_fields = merge_fields + ['spotID', 'Inoc.Time', 'XOffset', 'YOffset', 'K', 'r', 'g', 'v', 'objval', 'd0', 'nAUC', 'nSTP', 'nr', 'nr_t', 'maxslp', 'maxslp_t', 'Gene', 'MDP', 'MDR', 'MDRMDP', 'glog_maxslp', 'DT', 'AUC', 'rsquare', 'DT_h', 'DT_h_goodR2', 'inv_DT_h_goodR2']
    df_fitness_measurements = df_fitness_measurements[df_fitness_measurements_interesting_fields]
    df_fitness_measurements = df_fitness_measurements.merge(df_plate_layout, how="left", left_on=merge_fields, right_on=merge_fields, validate="one_to_one").reset_index(drop=True)

    # checks
    for k in df_fitness_measurements.keys(): check_no_nans_series(df_fitness_measurements[k])
    for k in set(df_growth_measurements_all_timepoints.keys()).difference({"redMean", "greenMean", "blueMean"}): check_no_nans_series(df_growth_measurements_all_timepoints[k])


    # add exp name
    df_growth_measurements_all_timepoints["experiment_name"] = experiment_name

    # save the dataframe with all the timepoonts
    save_df_as_tab(df_growth_measurements_all_timepoints.drop(['bad_spot'], axis=1), "%s/growth_measurements_all_timepoints.csv"%extended_outdir)

    ########################################################################

    ####### GENERATE FILES DERIVED FROM THE INTEGRATED ANALYSIS OF FITNESS DF #########
    print_with_runtime("Detecting bad spots...")

    # create an df with the potential bad spots
    df_bad_spots = generate_df_w_potential_bad_spots(df_fitness_measurements, min_nAUC_to_beConsideredGrowing)

    # add fields to the fitness df that are necessary to run the subsequent calculations
    number_to_letter = dict(zip(range(1,9), list("ABCDEFGH")))
    df_fitness_measurements["replicateID"] = df_fitness_measurements.row.apply(lambda x: number_to_letter[x]) + df_fitness_measurements.column.apply(str)
    df_fitness_measurements["sampleID"] = df_fitness_measurements.strain + "_" + df_fitness_measurements.replicateID
    df_fitness_measurements["log2_concentration"] = np.log2(df_fitness_measurements.concentration + pseudocount_log2_concentration)
    df_fitness_measurements["is_growing"]  = df_fitness_measurements.nAUC>=min_nAUC_to_beConsideredGrowing # the nAUC to be considered growing

    # create merged images to validate bad spots
    df_bad_spots_auto = df_bad_spots[df_bad_spots.bad_spot_reason!="manual setting in plate layout"]
    if len(df_bad_spots_auto)>0:

        # make folder
        merged_images_bad_spots_dir = "%s/merged_images_bad_spots"%tmpdir
        delete_folder(merged_images_bad_spots_dir); make_folder(merged_images_bad_spots_dir)

        # define a df with the spot locations
        df_offsets = cp.deepcopy(df_fitness_measurements[["plate_batch", "plate", "row", "column", "strain", "XOffset", "YOffset"]])
        df_offsets["numeric_row"] = df_offsets.row
        num_to_letter = dict(zip(range(1,9), "ABCDEFGH"))
        df_offsets["row"] = df_offsets.row.apply(lambda x: num_to_letter[x])

        # define a df with the growth at different timepoints
        df_growth_all = cp.deepcopy(df_growth_measurements_all_timepoints[["plate_batch", "plate", "row", "column", "strain", "Growth", "Expt.Time"]]).set_index(["plate_batch", "plate", "strain"], drop=False)
        df_growth_all["row"] = df_growth_all.row.apply(lambda x: num_to_letter[x])

        # define the box size as the mean of distance between adjacent boxes. This is specific to each plate
        df_offsets = df_offsets.set_index(["numeric_row", "column"], drop=False)
        plate_batch_and_plate_to_box_size = {}
        for plate_batch, plate in df_bad_spots_auto[["plate_batch", "plate"]].drop_duplicates().values:
            df_offsets_plate = df_offsets[(df_offsets.plate_batch==plate_batch) & (df_offsets.plate==plate)]

            box_size_rows = [df_offsets_plate.loc[(n_row+1, 1), "YOffset"] - df_offsets_plate.loc[(n_row, 1), "YOffset"] for n_row in range(1,8)]
            box_size_cols = [df_offsets_plate.loc[(1, col+1), "XOffset"] - df_offsets_plate.loc[(1, col), "XOffset"] for col in range(1,12)]

            plate_batch_and_plate_to_box_size[(plate_batch, plate)] = int(np.mean(box_size_rows + box_size_cols))

        # run generation of images in parallel
        #print_with_runtime("Generating bad-spot images in parallel in %i threads..."%multiproc.cpu_count())
        df_offsets = df_offsets.set_index(["plate_batch", "plate", "strain"])
        inputs_fn_bad_spots = [(r.plate_batch, r.plate, r.row, r.column, cp.deepcopy(df_offsets.loc[{(r.plate_batch, r.plate, r.strain)}]), cp.deepcopy(df_growth_all.loc[{(r.plate_batch, r.plate, r.strain)}].reset_index(drop=True)), merged_images_bad_spots_dir, processed_images_dir_each_plate, plate_batch_to_images, plate_batch_and_plate_to_box_size[(r.plate_batch, r.plate)]) for I, r in df_bad_spots_auto.iterrows()]
        run_function_in_parallel(inputs_fn_bad_spots, generate_merged_image_test_bad_spot)

    # save files, marking the end
    save_object(df_fitness_measurements, "%s/df_fitness_measurements.py"%tmpdir)
    save_df_as_tab(df_bad_spots, "%s/df_bad_spots_automatic.tab"%tmpdir)

    ###################################################################################


def run_analyze_images_get_rel_fitness_and_susceptibility_measurements(plate_layout_file, images_dir, outdir, keep_tmp_files, pseudocount_log2_concentration, min_nAUC_to_beConsideredGrowing, min_points_to_calculate_resistance_auc):

    """
    Writes the integrated fitness and susceptibility measurements.
    """

    print("Getting final tables and plots...")

    ######## PROCESS INPUTS #######

    # get plate layout df
    df_plate_layout, all_drugs, measure_susceptibility, experiment_name = get_df_plate_layout_and_all_drugs(plate_layout_file, images_dir)

    # define the tmpdir
    tmpdir = "%s/tmp"%outdir
    if not os.path.isdir(tmpdir): raise ValueError("tmpdir should exist")

    # define the extended_outdir
    extended_outdir = "%s/extended_outputs"%outdir
    if not os.path.isdir(extended_outdir): raise ValueError("extended_outdir should exist")

    ###############################


    ####### GENERAL FILES GENERATION #######

    # init a list with the files to keep in main
    files_main_output = []

    # load the fitness df
    df_fitness_measurements = load_object("%s/df_fitness_measurements.py"%tmpdir)

    # load df with bad spots and write it to outdir as an excel
    df_bad_spots = get_tab_as_df_or_empty_df("%s/bad_spots_validated.csv"%tmpdir)

    if len(df_bad_spots)>0: 
        df_bad_spots["experiment_name"] = experiment_name
        df_bad_spots[['plate_batch', 'plate', 'row', 'column', 'drug', 'concentration', 'strain', 'experiment_name', 'bad_spot_reason']].sort_values(by=["plate_batch", "plate", "strain", "row", "column"]).to_excel("%s/bad_spots.xlsx"%extended_outdir, index=False)

    else: print_with_runtime("There are no bad spots, so that bad_spots.xlsx will not be generated.")

    # change to numbers
    letter_to_number = dict(zip(list("ABCDEFGH"), range(1,9)))
    df_bad_spots["row"] = df_bad_spots.row.apply(lambda x: letter_to_number[x])

    # add bad spot
    spot_fields = ["plate_batch", "plate", "row", "column"]
    df_fitness_measurements["spotID"] = df_fitness_measurements[spot_fields].apply(tuple, axis=1)
    df_bad_spots["spotID"] = df_bad_spots[spot_fields].apply(tuple, axis=1)
    all_spots = set(df_fitness_measurements.spotID)
    bad_spots = set(df_bad_spots.spotID)

    if len(set(df_fitness_measurements.spotID))!=len(df_fitness_measurements): raise ValueError("spotID should be unique")
    strange_bad_spots = bad_spots.difference(all_spots)
    if len(strange_bad_spots)>0: raise ValueError("Strange bad spots: %s"%strange_bad_spots)

    # add to df_fitness_measurements
    df_fitness_measurements["bad_spot"] = df_fitness_measurements.spotID.isin(bad_spots)

    # add the experiment name
    df_fitness_measurements["experiment_name"] = experiment_name

    # log
    print_with_runtime("There are a total of %i validated bad spots (both manually-defined and automatically-predicted)."%(sum(df_fitness_measurements.bad_spot)))

    # create simple raw fitness table
    generate_simplified_fitness_table(df_fitness_measurements, ["nAUC"], "%s/fitness_measurements_simple.csv"%extended_outdir, experiment_name)
    files_main_output.append("fitness_measurements_simple.xlsx")

    ########################################

    if measure_susceptibility is True:

        #### INTEGRATE THE PLATE SETS TO MEASURE SUSCEPTIBILITY ####

        # run the AST calculations based on all plates
        print_with_runtime("Getting the relative fitness and susceptibility measurements. Adding %s as a pseudocount to calculate log2 concentrations. Considering spots with a  nAUC<%s to be not growing. rAUC calculations are only made on strains with at least %s (including 0) concentrations..."%(pseudocount_log2_concentration, min_nAUC_to_beConsideredGrowing, min_points_to_calculate_resistance_auc))

        # debugs
        for d in all_drugs:

            # check that you have the expected samples
            expected_nsamples = len(set(df_fitness_measurements[(df_fitness_measurements.drug==d)].sampleID))
            if sum(df_fitness_measurements.concentration==0.0)!=expected_nsamples: raise ValueError("There should be %i wells with concentration==0 for drug==%s. Note that this script expects the strains in each spot to be the same in all analyzed plates of the same drug."%(expected_nsamples, d))

        # add fields to the df_fitness_measurements that are only possible if the susceptibility is 0
        df_fitness_measurements = get_df_fitness_measurements_with_extra_fields_when_conc0_is_available(df_fitness_measurements)

        # three fields added:
        """ 
        conc0_is_growing: whether the concentration 0 is growing
        conc0_is_bad_spot: whether the concentration 0 is a bad spot
        n_non0_concentrations_bad_spot: the number of non-0 concentrations that are bad spots for a given replicate and drug
        """

        # init variables
        fitness_estimates  = ["K", "r", "nr", "nr_t", "maxslp", "maxslp_t", "MDP", "MDR", "MDRMDP", "DT", "AUC", "DT_h", "nAUC", "DT_h_goodR2"]
        fitness_estimates_susc = ["K", "r", "nr", "maxslp", "MDP", "MDR", "MDRMDP", "AUC", "nAUC"] # these are estimates that are correlated to growth rate


        # get the fitness df with relative values (for each drug, the fitness relative to the concentration==0), and save these measurements
        df_fitness_measurements = get_fitness_df_with_relativeFitnessEstimates(df_fitness_measurements, fitness_estimates)


        # add an idx that indicates if the row is valid for relative fitness an susceptibility measurements
        df_fitness_measurements["idx_correct_rel_estimates"] = ((df_fitness_measurements.conc0_is_growing) & ~(df_fitness_measurements.conc0_is_bad_spot) & (df_fitness_measurements.n_non0_concentrations_bad_spot<2) & ~(df_fitness_measurements.bad_spot))

        print_with_runtime("There are %i/%i spots that are valid for susceptibility and integrated relative fitness estimates. These are non-bad spots with a concentration==0 that is growing and is not a bad spot. In addtion, these have <2 non-0 concentrations that are bad spots."%(sum(df_fitness_measurements["idx_correct_rel_estimates"]), len(df_fitness_measurements)))

        # save the fitness df
        save_df_as_tab(df_fitness_measurements, "%s/fitness_measurements.csv"%extended_outdir)

        # create simple rel fitness table, only considering spots where the conc0 is growing, and only those with some concentration
        generate_simplified_fitness_table(df_fitness_measurements[(df_fitness_measurements.idx_correct_rel_estimates) & (df_fitness_measurements.concentration>0)], ["nAUC_rel"], "%s/relative_fitness_measurements_simple.csv"%extended_outdir, experiment_name)
        files_main_output.append("relative_fitness_measurements_simple.xlsx")

        # measure susceptibility
        drug_to_nconcs = df_fitness_measurements[df_fitness_measurements.concentration!=0][["drug", "concentration"]].drop_duplicates().groupby("drug").apply(len)
  
        if any(drug_to_nconcs>=2):

            # get the susceptibility df
            susceptibility_df = get_susceptibility_df(df_fitness_measurements, fitness_estimates_susc, pseudocount_log2_concentration, min_points_to_calculate_resistance_auc, "%s/susceptibility_measurements.csv"%extended_outdir, experiment_name)

            # generate a reduced, simple, susceptibility_df
            simple_susceptibility_df = susceptibility_df[(susceptibility_df.fitness_estimate=="nAUC_rel")].groupby(["drug", "strain"]).apply(get_row_simple_susceptibility_df_one_strain_and_drug).reset_index(drop=True)
            for f in ['median_MIC50', 'mode_MIC50', 'mad_MIC50', 'median_SMG-MIC50', 'mode_SMG-MIC50', 'mad_SMG-MIC50', 'median_rAUC', 'mode_rAUC', 'mad_rAUC']: simple_susceptibility_df[f] = simple_susceptibility_df[f].apply(get_clean_float_value)

            simple_susceptibility_df["experiment_name"] = experiment_name
            save_df_as_tab(simple_susceptibility_df, "%s/susceptibility_measurements_simple.csv"%extended_outdir)
            simple_susceptibility_df.to_excel("%s/susceptibility_measurements_simple.xlsx"%extended_outdir, index=False)
            files_main_output.append("susceptibility_measurements_simple.xlsx")

        else: print_with_runtime("All drugs have <2 non-0 concentrations, so that the susceptibility analysis is skipped.")
    
        ############################################################

        ######### MAKE PLOTS ##########

        # make lineplots of concentration-vs-fitness
        outdir_drug_vs_fitness_extended = "%s/drug_vs_fitness_lines"%extended_outdir
        plot_growth_at_different_drugs(df_fitness_measurements, outdir_drug_vs_fitness_extended, fitness_estimates, min_nAUC_to_beConsideredGrowing, pseudocount_log2_concentration, experiment_name, type_data="only_correct_spots", only_absolute_estimates=False)

        # make lineplots of concentration-vs-fitness with all spots (also non-bad spots)
        outdir_drug_vs_fitness_extended_all_spots = "%s/drug_vs_fitness_lines_all_spots"%extended_outdir
        plot_growth_at_different_drugs(df_fitness_measurements, outdir_drug_vs_fitness_extended_all_spots, fitness_estimates, min_nAUC_to_beConsideredGrowing, pseudocount_log2_concentration, experiment_name, type_data="all_data", only_absolute_estimates=True)

        # make the heatmap of the susceptibility measures
        if any(drug_to_nconcs>=2): plot_heatmap_susceptibility(susceptibility_df, "%s/susceptibility_heatmaps"%extended_outdir, fitness_estimates_susc, experiment_name, min_nAUC_to_beConsideredGrowing)

        # make heatmap of concentration-vs-fitness
        outdir_heatmaps_extended = "%s/drug_vs_fitness_heatmaps"%extended_outdir
        plot_heatmaps_concentration_vs_fitness(df_fitness_measurements, outdir_heatmaps_extended, fitness_estimates, pseudocount_log2_concentration, min_nAUC_to_beConsideredGrowing, experiment_name)

        ###############################

    else: 
        print_with_runtime("WARNING: You did not provide concentration==0, so that the susceptibility and relative fitness measurements are not generated.")
        save_df_as_tab(df_fitness_measurements, "%s/fitness_measurements.csv"%extended_outdir)

    #### RESTRUCTURE ####

    # main files
    for f in files_main_output: os.rename("%s/%s"%(extended_outdir, f), "%s/%s"%(outdir, f))

    # plots
    summary_plots_dir = "%s/summary_plots"%outdir; make_folder(summary_plots_dir)
    some_plots_generated = False

    for drug in all_drugs:

        # make dir
        summary_plots_dir_drug = "%s/%s"%(summary_plots_dir, drug); make_folder(summary_plots_dir_drug)

        # copy various plots
        all_interesting_plots = make_flat_listOflists([["%s/%s"%(root, f) for f in files if f.endswith(".pdf") and "_nAUC" in f and (f.startswith("[%s]_"%drug) or f.startswith("%s_"%drug))] for (root, dirs, files) in os.walk(extended_outdir)])

        if len(all_interesting_plots)>0:
            for f in all_interesting_plots: copy_file(f, "%s/%s"%(summary_plots_dir_drug, get_file(f)))
            some_plots_generated = True

        else: delete_folder(summary_plots_dir_drug)

    if some_plots_generated is False: delete_folder(summary_plots_dir)

    #####################

    ###### CLEAN #####

    # clean, unless specified otherwise
    if keep_tmp_files is False: delete_folder(tmpdir)

    #################


 




