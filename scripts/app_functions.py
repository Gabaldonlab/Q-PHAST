#!/usr/bin/env python

# Functions of the image analysis pipeline. This should be imported from the main_env

# imports
import os, sys, time, random, string, shutil
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
allowed_image_endings = {"tiff", "jpg", "jpeg", "png", "tif", "gif"}


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

def process_image_rotation_and_contrast(Iimage, nimages, raw_image, processed_image):

    """Generates a processed image based on raw image that has enhanced contrast and left rotation."""

    # log
    image_short_name = "<images>/%s/%s"%(get_dir(raw_image).split("/")[-1], get_file(raw_image))
    print_with_runtime("Improving contrast and rotating image %i/%i: %s"%(Iimage, nimages, image_short_name))

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

def generate_colonyzer_coordinates_one_plate_batch_and_plate(dest_processed_images_dir, coordinate_obtention_dir_plate, sorted_image_names):

    """Generates a 'Colonyzer.txt' file in each dest_processed_images_dir with all the coordinates."""

    # define the dir with the coordinates for one image
    colonizer_coordinates_one_spot = "%s/Colonyzer.txt"%coordinate_obtention_dir_plate
    colonizer_coordinates = "%s/Colonyzer.txt"%dest_processed_images_dir

    # define the latest image to base the coordinates on
    latest_image = sorted_image_names[-1]

    if file_is_empty(colonizer_coordinates):

        # clean
        remove_file(colonizer_coordinates_one_spot)

        # softlink one image into coordinate_obtention_dir to get coordinates
        soft_link_files("%s/%s"%(dest_processed_images_dir, latest_image), "%s/%s"%(coordinate_obtention_dir_plate, latest_image))

        # get the coordinates
        initial_dir = os.getcwd()
        os.chdir(coordinate_obtention_dir_plate)
        parametryzer_std = "%s/parametryzer.std"%coordinate_obtention_dir_plate
        run_cmd("%s/envs/colonyzer_env/bin/parametryzer > %s 2>&1"%(CondaDir, parametryzer_std), env="colonyzer_env")
        os.chdir(initial_dir)

        # checks
        if file_is_empty(colonizer_coordinates_one_spot): raise ValueError("%s should exist. Make sure that you clicked the spots or check %s"%(colonizer_coordinates_one_spot, parametryzer_std))
        remove_file(parametryzer_std)

        # create a colonyzer file with all the info in dest_processed_images_dir/Colonyzer.txt

        # get last line
        last_line_split = open(colonizer_coordinates_one_spot, "r").readlines()[-1].strip().split(",")

        # define the wells
        wells = last_line_split[1]
        if wells!="96": raise ValueError("You set the analysis for %s-well plates, which is incompatible. Make sure that you press 'g' to save the coordinates."%wells)

        # get the coordinates
        coordinates_str = ",".join(last_line_split[2:])

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


def get_barcode_for_filenames_old(filenames_series):

    """Takes a series of filenames and passes them to get_barcode_from_filename to get barcoded values. The barcode cannot exceed 11 chars, so that it is stripped accoringly by this function"""

    # get barcoded items
    barcoded_names  = filenames_series.apply(get_barcode_from_filename)

    # get barcode
    unique_barcodes = set(barcoded_names.apply(lambda x: x.split("-")[0]))
    barcode_to_differentLengths = {b : len(b) for b in unique_barcodes if len(b)!=11}

    # initialize a map between the long and the short barcode
    oldBar_to_newBar = {x:x for x in unique_barcodes.difference(set(barcode_to_differentLengths))}

    # adapt the barcodes
    for barcode, len_barcode in barcode_to_differentLengths.items():

        # if larger
        if len_barcode>11: 

            # understand if there is a common suffix or a common prefix
            
            # common prefic
            if len(set([x[0:2] for x in unique_barcodes]))==1: newbarcode = barcode[len_barcode-11:]

            # common suffix
            elif len(set([x[-2:] for x in unique_barcodes]))==1: newbarcode = barcode[0:11]

            else: raise ValueError("No common suffix or prefix could be found. Please specify IDs that have 11 characters or less in the image filenames")

        # if smaller
        elif len_barcode<11: newbarcode = barcode + "X"*(11-len_barcode)

        # save
        oldBar_to_newBar[barcode] = newbarcode

    # check that everything was ok
    if len(oldBar_to_newBar)!=len(set(oldBar_to_newBar.values())): 
        print("The barcode transformation is:\n", oldBar_to_newBar)
        raise ValueError("The barcodes were not transformed correctly")

    # return
    return barcoded_names.apply(lambda x: "%s-%s"%(oldBar_to_newBar[x.split("-")[0]], "-".join(x.split("-")[1:])))


def get_barcode_for_filenames(filenames_series):

    """Takes a series of filenames and passes them to get_barcode_from_filename to get barcoded values. The barcode cannot exceed 11 chars, so that it is stripped accoringly by this function"""

    # get barcoded items
    barcoded_names  = filenames_series.apply(get_barcode_from_filename)

    # return
    oldBar_to_newBar = {"img0":"img_fitness"}
    return barcoded_names.apply(lambda x: "%s-%s"%(oldBar_to_newBar[x.split("-")[0]], "-".join(x.split("-")[1:])))

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

    # generate the plots with R
    make_an_std
    run_cmd("/workdir_app/scripts/get_fitness_measurements.R %s"%("%s/%s"%(outdir_all, outdir_name)), env="main_env")

def get_df_integrated_fitness_measurements_one_plate_batch_and_plate(images_folder, outdir_all, plate_batch, plate, sorted_image_names, df_plate_layout):

    """Analyzes the images from images_folder, writing into outdir_all."""

    # define the final output
    integrated_data_file = "%s/integrated_data.tbl"%(outdir_all)
    if file_is_empty(integrated_data_file):

        # debug
        #delete_folder(outdir_all)

        # prepare dirs
        make_folder(outdir_all)

        ###### RUN COLONYZER TO GET IMAGE DATA ######

        # move into the images dir
        initial_dir = os.getcwd()
        os.chdir(images_folder)

        # check 
        if file_is_empty("./Colonyzer.txt"): raise ValueError("Colonyzer.txt should exist in %s"%images_folder)

        # define the image names that you expect
        image_names_withoutExtension = set({x.split(".")[0] for x in sorted_image_names})

        # run colonyzer for all parameters
        print_with_runtime("Running colonyzer to get raw fitness data...")
        parms = ("greenlab", "lc", "diffims")
        run_colonyzer_one_set_of_parms(parms, outdir_all, image_names_withoutExtension)

        # go back to the initial dir
        os.chdir(initial_dir)

        #############################################

        ####### RUN FITTING TO GET FITNESS CALCULATIONS ########

        # go through each of the directories of data and generate the image analysis data
        print_with_runtime("Running qfa to get per-spot fitness data...")

        # generate the fitness df
        df_fitness_measurements = get_df_fitness_measurements_one_parm_set(outdir_all, "output_%s"%("_".join(sorted(parms))), plate_batch, plate, df_plate_layout)


        write_integration_of_integrated_data_file

        


        ########################################################

        run_integration_with_plate_layout

        #./scripts/run_image_analysis_4plates_per_image.py -i ./testing/testing_inputs/images --output ./testing/testing_output -pcomb greenlab,lc,diffims --steps colonyzer,visualization,analysis,metadata_analysis --metadata_file ./testing/testing_inputs/metadata.tab

        #optional_args = "--n_wells %i --parm_combinations %s --steps %s"%(opt.n_wells, opt.parm_combinations, opt.steps)
        #image_analysis_cmd = "%s -i %s -o %s %s"%(image_analysis_pipeline, plate_input_Dir, plate_output_Dir, optional_args)


        # 
        adkgjahgd

        # go to the initial dir
        #os.chdir(initial_dir)

        # save and rename


    ###### PREPARE DF #####

    # load df
    df = pd.read_csv(integrated_data_file, sep="\t")

    # add fields
    df["plate"] = plate
    df["plate_batch"] = plate_batch

    # correct the rsquare
    def get_rsquare_to0(rsq):
        if rsq>0: return rsq
        else: return 0.0
    df["rsquare"] = df.rsquare.apply(get_rsquare_to0)

    # get the correct DT_h
    maxDT_h = 25.0
    def get_DT_good_rsq(DT_h, rsq, rsq_tshd=0.9):
        if rsq>=rsq_tshd: return DT_h
        else: return maxDT_h
    df["DT_h_goodR2"] = df.apply(lambda r: get_DT_good_rsq(r["DT_h"], r["rsquare"]), axis=1)

    # add the inverse of DT_h
    df["inv_DT_h_goodR2"] = 1 / df.DT_h_goodR2

    # return
    return df

    #######################

def run_analyze_images(plate_layout_file, images_dir, outdir, keep_tmp_files):

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

    # define dirs
    linked_raw_images_dir = "%s/linked_raw_images"%tmpdir; make_folder(linked_raw_images_dir)
    processed_images_dir = "%s/processed_images"%tmpdir; make_folder(processed_images_dir)
    plate_batch_to_images = {}

    # init the inputs_fn
    inputs_fn = []

    # go through each image
    for plate_batch in sorted(set(df_plate_layout.plate_batch)):

        processed_images_dir_batch = "%s/%s"%(processed_images_dir, plate_batch); make_folder(processed_images_dir_batch)
        linked_raw_images_dir_batch = "%s/%s"%(linked_raw_images_dir, plate_batch); make_folder(linked_raw_images_dir_batch)
        raw_images_dir_batch = "%s/%s"%(images_dir, plate_batch)
        plate_batch_to_images[plate_batch] = set()

        for f in os.listdir(raw_images_dir_batch): 

            # debug non images
            if f.split(".")[-1].lower() not in allowed_image_endings or f.startswith("."):
                print_with_runtime("WARNING: File <images>/%s/%s not considered as an image. Note that only images ending with %s (and not starting with a '.') are considered"%(plate_batch, f, allowed_image_endings))
                continue

            # get the linked image
            linked_raw_image = "%s/%s"%(linked_raw_images_dir_batch, f)
            soft_link_files("%s/%s"%(raw_images_dir_batch, f), linked_raw_image)
            
            # get the  processed image
            year, month, day, hour, minute = get_yyyymmddhhmm_tuple_one_image_name(f)
            year = str(year)
            month = get_int_as_str_two_digits(month); day = get_int_as_str_two_digits(day)
            hour = get_int_as_str_two_digits(hour); minute = get_int_as_str_two_digits(minute)
            processed_image = "%s/img_0_%s%s%s_%s%s.tif"%(processed_images_dir_batch, year, month, day, hour, minute) # we save all images as tif after processing

            # keep inputs
            inputs_fn.append((linked_raw_image, processed_image))

            # keep image
            plate_batch_to_images[plate_batch].add(get_file(processed_image))

        # sort images by date
        plate_batch_to_images[plate_batch] = sorted(plate_batch_to_images[plate_batch], key=get_yyyymmddhhmm_tuple_one_image_name)

        break # debug

    # run
    for I, (r,p) in enumerate(inputs_fn): process_image_rotation_and_contrast(I+1, len(inputs_fn), r, p)

    #######################################

    ##### RUN THE IMAGE ANALYSIS PIPELINE FOR EACH PLATE AND PLATE SET #####
    print_with_runtime("Getting image analysis data for each plate")

    # define the list of inputs, which will be processed below
    inputs_fn = []

    # define a folder that will contain the linked images for each individual processing
    processed_images_dir_each_plate = "%s/processed_images_each_plate"%tmpdir; make_folder(processed_images_dir_each_plate)

    # go through each plate in each plate set and define the coordinates of the plates manually, using the latest timepoint for each plate
    coordinate_obtention_dir = "%s/colonyzer_coordinates"%tmpdir; make_folder(coordinate_obtention_dir)

    for plate_batch, plate in df_plate_layout[["plate_batch", "plate"]].drop_duplicates().values:
        plateID_to_quadrantName = {1:"upper-left", 2:"upper-right", 3:"lower-left", 4:"lower-right"}

        # link all the images to a working dir
        processed_images_dir_batch = "%s/%s"%(processed_images_dir, plate_batch)
        dest_processed_images_dir = "%s/%s_plate%i"%(processed_images_dir_each_plate, plate_batch, plate); make_folder(dest_processed_images_dir)
        for f in os.listdir(processed_images_dir_batch): soft_link_files("%s/%s"%(processed_images_dir_batch, f), "%s/%s"%(dest_processed_images_dir, f))
        
        # define the coordinates dir and generate the colonyzer coordinates
        print_with_runtime('Getting plate coordinates for plate_batch %s and plate %i (%s plate). You should mark the upper-left and lower-right spots of the desired plate, press "spacebar" and then "g" to save...'%(plate_batch, plate, plateID_to_quadrantName[plate]))
        coordinate_obtention_dir_plate = "%s/%s_plate%i"%(coordinate_obtention_dir, plate_batch, plate); make_folder(coordinate_obtention_dir_plate)
        generate_colonyzer_coordinates_one_plate_batch_and_plate(dest_processed_images_dir, coordinate_obtention_dir_plate, plate_batch_to_images[plate_batch])

        # keep dir
        inputs_fn.append((dest_processed_images_dir, plate_batch, plate))

        break

    # go through each plate and plate set and run the fitness calculations
    outdir_fitness_calculations = "%s/fitness_calculations"%tmpdir; make_folder(outdir_fitness_calculations)
    df_fitness_measurements = pd.DataFrame()

    for I, (proc_images_folder, plate_batch, plate) in enumerate(inputs_fn): 

        print_with_runtime("Analyzing images for plate_batch-plate %i/%i: %s-plate%i"%(I+1, len(inputs_fn), plate_batch, plate))
        df_fitness_measurements = df_fitness_measurements.append(get_df_integrated_fitness_measurements_one_plate_batch_and_plate(proc_images_folder, "%s/%s_plate%i"%(outdir_fitness_calculations, plate_batch, plate), plate_batch, plate, plate_batch_to_images[plate_batch], df_plate_layout))

    
    # merge with the plate layout info
    # all_df = all_df.merge(metadata_df, how="left", left_on=["plate", "Row", "Column"], right_on=["plate", "row", "column"], validate="many_to_one")

    dakjghkhadd


    ########################################################################


    #### INTEGRATE THE PLATE SETS ####

    # run the AST calculations based on all plates

    ##################################
    
    jhgadjhgdaad


    ###### CLEAN #####

    # keep only the important folders in outdir
    jadhgjhagjdagdahg

    # clean, unless specified otherwise
    if keep_tmp_files is False: delete_folder(tmpdir)

    #################


 