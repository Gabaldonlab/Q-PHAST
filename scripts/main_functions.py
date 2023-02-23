# Functions that can be run in any OS

# universal imports
import os, sys, argparse, shutil, subprocess

# environment checks
print("Testing that the python packages are correctly installed...")
try: 

    # try to import PIL and tk
    from PIL import Image as PIL_Image
    from PIL import ImageTk
    import tkinter as tk

except:

    # log
    print("ERROR: Some of the python libraries necessary to run this are not installed. You can install them with Anaconda Navigator, as explained in https://github.com/Gabaldonlab/Q-PHAST.")

    # tk debug
    try: import tkinter as tk
    except:
        print("ERROR: the library 'tkinter' is not installed. You can install it with Anaconda Navigator, as explained in https://github.com/Gabaldonlab/Q-PHAST.")
        sys.exit(1)

    # PIL debug
    try:
        from PIL import Image as PIL_Image
        from PIL import ImageTk

    except:
        print("ERROR: the library 'pillow' is not installed. You can install it with Anaconda Navigator, as explained in https://github.com/Gabaldonlab/Q-PHAST.")
        sys.exit(1)

    # exit
    sys.exit(1)

print("All python packages are correctly installed.")

# specific (non-general) imports
from pathlib import Path
import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
import subprocess
import webbrowser
from PIL import Image as PIL_Image
from PIL import ImageTk
from datetime import date

# define general variables
window_width = 400 # width of all windows
pipeline_name = "Q-PHAST"

# functions
def get_fullpath(x): return os.path.realpath(x)

def get_fullpath_old(x):

    """Takes a path and substitutes it bu the full path"""

    if opt.os in {"linux", "mac"}:
        if x.startswith("/"): return x

        # a ./    
        elif x.startswith("./"): return "%s/%s"%(os.getcwd(), "/".join(x.split("/")[1:]))

        # others (including ../)
        else: return "%s/%s"%(os.getcwd(), x)

    elif opt.os=="windows":
        if Path(x).is_absolute() is True: return x

        # a .\
        elif x.startswith(".\\"): return "%s\\%s"%(os.getcwd(), "\\".join(x.split("\\")[1:]))

        # others (including ..\)
        else: return "%s\\%s"%(os.getcwd(), x)

    else: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

def run_cmd(cmd):

    """Runs os.system in cmd"""

    out_stat = os.system(cmd) 
    if out_stat!=0: raise ValueError("\n%s\n did not finish correctly. Out status: %i"%(cmd, out_stat))

def make_folder(f):

    if not os.path.isdir(f): os.mkdir(f)


def remove_file(f):

    if os.path.isfile(f): os.unlink(f)

def delete_folder(f):

    if os.path.isdir(f): shutil.rmtree(f)

def file_is_empty(path): 
    
    """ask if a file is empty or does not exist """

    if not os.path.isfile(path): return True
    elif os.stat(path).st_size==0: return True
    else: return False

def get_os_sep(): return {"windows":"\\", "linux":"/", "mac":"/"}[opt.os]

def copy_file(origin_file, dest_file):

    """Copies file"""

    dest_file_tmp = "%s.tmp"%dest_file
    shutil.copy(origin_file, dest_file_tmp)
    os.rename(dest_file_tmp, dest_file)

def generate_os_window():

    """Generates the OS selection window"""

    window = tk.Tk(); window.geometry("%ix150"%(window_width))
    window.title(pipeline_name)

    tk.Label(window, text="\nSelect the Operating System:", font=('Arial bold',15)).pack(side=tk.TOP)
    for os_name in ["linux", "mac", "windows"]: 

        def set_os(x = os_name):
            opt.os = x
            window.destroy()

        tk.Button(window, text=os_name, padx=20, pady=15, font=('Arial bold',13), command=set_os).pack(side=tk.LEFT, expand=True) 

    window.mainloop()
    if opt.os is None: raise ValueError("You should select the OS")

def generate_closing_window(text_print):

    """Generates a closing window, depending on the os"""

    # define a function that closes window
    def close_window(): 
        window.destroy()

    # init window
    window = tk.Tk(); window.geometry("%ix50"%(window_width))
    window.title(pipeline_name)

    # add label
    tk.Label(window, text="\n%s"%text_print, font=('Arial bold',15)).pack(side=tk.TOP)

    # close after 1s
    window.after(3000, close_window)

    # in MAC do some extra steps
    if opt.os in {"mac"}:

        # run and close. this works on mac only
        while True:
            try: window.update()
            except: break

    # in other OSs
    elif opt.os in {"windows", "linux"}: 

        # run window
        window.mainloop()

    else: raise ValueError("OS %s is invalid"%opt.os)


def generate_docker_image_window():

    """Generates the image selection window"""

    try: docker_images = ["%s:%s"%(l.split()[0], l.split()[1]) for l in str(subprocess.check_output("docker images", shell=True)).split("\\n") if not l.startswith("b'REPOSITORY") and len(l.split())>2 and 'mikischikora/q-phast' in l and not '<none>' in l]
    except: raise ValueError("The docker command 'docker images' did not work properly. Are you sure that docker is running?")

    image_w = 60
    window = tk.Tk(); window.geometry("%ix%i"%(window_width, image_w + len(docker_images)*image_w))
    window.title(pipeline_name)

    tk.Label(window, text="\nSelect the docker image:", font=('Arial bold',15)).pack(side=tk.TOP)
    for docker_img in docker_images: 

        def set_docker_image(x = docker_img):
            opt.docker_image = x
            window.destroy()

        tk.Button(window, text=docker_img, padx=30, pady=10, font=('Arial bold',13), command=set_docker_image).pack(side=tk.TOP, expand=True) 

    window.mainloop()
    if opt.docker_image is None: raise ValueError("You should select the docker image")


def generate_module_window():

    """ generate a window that defines the module"""

    window = tk.Tk()
    window.geometry("%ix150"%(window_width))
    window.title(pipeline_name)

    tk.Label(window, text="\nSelect the module:", font=('Arial bold',15)).pack(side=tk.TOP)

    for module, module_name in [("get_plate_layout", "plate_layout"), ("analyze_images", "analyze_images")]: 

        def set_module(x = module):
            opt.module = x
            window.destroy()

        tk.Button(window, text="%s"%(module_name), padx=15, pady=15, font=('Arial bold',13), command=set_module).pack(side=tk.LEFT, expand=True)

    window.mainloop()
    if opt.module is None: raise ValueError("You should select the module")

def generate_replace_window():

    """Generates the replace window"""

    window = tk.Tk()
    window.geometry("%ix210"%(window_width))
    window.title(pipeline_name)

    tk.Label(window, text='\nRemove the output folder\nand re-do all analyses?\n', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text="(set 'No' to re-start from a previous run)\n", font=('Arial bold',12)).pack(side=tk.TOP)

    for rep_value, replace_text in [(True, "Yes"), (False, "No")]: 

        def set_replace(x = rep_value):
            opt.replace = x
            window.destroy()

        tk.Button(window, text="%s"%(replace_text), padx=15, pady=15, font=('Arial bold',13), command=set_replace).pack(side=tk.LEFT, expand=True)

    window.mainloop()

def get_last_part_of_string(x, max_size=15):

    """Gets a string and return the last part of it"""

    if len(x)>max_size: return "...%s"%(x[-max_size:])
    else: return x

def generate_get_plate_layout_window():

    """Generates the window of get plate layout"""

    # init window
    window = tk.Tk()
    window.geometry("%ix500"%(window_width))
    window.title(pipeline_name)

    # text
    tk.Label(window, text='\nModule get_plate_layout', font=('Arial bold',15)).pack(side=tk.TOP)

    # info disclaymer
    help_label = tk.Label(window, text='[Click here] to see example files\n', font=('Arial bold', 13))
    help_label.pack(side=tk.TOP)
    help_label.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://github.com/Gabaldonlab/qCAST/tree/main/testing/testing_subset"))

    # add the strains
    tk.Label(window, text='1) select the strains excel:', font=('Arial bold',15)).pack(side=tk.TOP)
    def define_strains(): 
        opt.strains = askopenfilename(filetypes=[("All files", "*.*")])
        strains_button["text"] = get_last_part_of_string(opt.strains)

    strains_button = tk.Button(window, text="Browse files", padx=15, pady=15, font=('Arial bold',13), command=define_strains)
    strains_button.pack(side=tk.TOP, expand=True)

    # add the drugs
    tk.Label(window, text='2) select the drugs excel:', font=('Arial bold',15)).pack(side=tk.TOP)
    def define_drugs(): 
        opt.drugs = askopenfilename(filetypes=[("All files", "*.*")])
        drugs_button["text"] = get_last_part_of_string(opt.drugs)

    drugs_button = tk.Button(window, text="Browse files", padx=15, pady=15, font=('Arial bold',13), command=define_drugs)
    drugs_button.pack(side=tk.TOP, expand=True)

    # run
    tk.Label(window, text='3) click to Run:', font=('Arial bold',15)).pack(side=tk.TOP)
    def run_module(): window.destroy()
    tk.Button(window, text="Run", padx=15, pady=15, font=('Arial bold',13), command=run_module).pack(side=tk.TOP, expand=True)

    window.mainloop()
    if opt.strains is None or opt.drugs is None: raise ValueError("You should provide an excel for both strains and drugs")
    if opt.drugs==opt.strains: raise ValueError("The drugs and strains excels can't be the same")

def get_plate_layout_file_from_input_dir(input_dir):

    """Gets an excel file name from the input dir"""

    # get the excel files
    possible_excel_files = [f for f  in os.listdir(opt.input) if f.endswith(".xlsx") and not f.startswith(".")]
    if len(possible_excel_files)==0: raise ValueError("There should be one (just one) excel file in the input folder")

    return possible_excel_files[0]


def generate_analyze_images_window_mandatory():

    """Generates one window for the image analysis"""

    # init window
    window = tk.Tk()
    window.geometry("%ix600"%(window_width))
    window.title(pipeline_name)

    # text
    tk.Label(window, text='\nProvide mandatory inputs', font=('Arial bold',15)).pack(side=tk.TOP)

    # add help label
    help_label = tk.Label(window, text='[Click here] to see example files\n', font=('Arial bold', 13))
    help_label.pack(side=tk.TOP)
    help_label.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://github.com/Gabaldonlab/Q-PHAST/tree/main/testing/testing_subsets"))

    # add the input folder
    tk.Label(window, text="\n1) select input folder:", font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text="(folder with plate layout and images\none subfolder for each plate_batch)", font=('Arial bold',13)).pack(side=tk.TOP)

    def define_input(): 
        opt.input = askdirectory()
        input_button["text"] = get_last_part_of_string(opt.input)

    input_button = tk.Button(window, text="Browse folders", padx=15, pady=15, font=('Arial bold',13), command=define_input)
    input_button.pack(side=tk.TOP, expand=True)

    # add the output folder
    tk.Label(window, text="\n2) select output folder:", font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text="(folder to generate output)", font=('Arial bold',13)).pack(side=tk.TOP)

    def define_output(): 
        opt.output = askdirectory()
        output_button["text"] = get_last_part_of_string(opt.output)

    output_button = tk.Button(window, text="Browse folders", padx=15, pady=15, font=('Arial bold',13), command=define_output)
    output_button.pack(side=tk.TOP, expand=True)

    # run and capture the entries
    tk.Label(window, text='\n3) click to Run:', font=('Arial bold',15)).pack(side=tk.TOP, expand=True)
    def run_module(): 

        # run
        window.destroy()
    
    tk.Button(window, text="Run", padx=15, pady=15, font=('Arial bold',13), command=run_module).pack(side=tk.TOP, expand=True)

    # run and debug
    window.mainloop()

    # checks
    if opt.input is None or opt.output is None: raise ValueError("You should provide both input and output folders")
    if not os.path.isdir(opt.input): raise ValueError("You should select a valid input folder")
    if not os.path.isdir(opt.output): raise ValueError("You should select a valid output folder")
    get_plate_layout_file_from_input_dir(opt.input)


def generate_analyze_images_window_optional():

    """Generates one window for the image analysis"""


    # init window
    window = tk.Tk()
    window.geometry("%ix850"%(window_width))
    window.title(pipeline_name)

    # text
    tk.Label(window, text='\nTune optional parameters', font=('Arial bold',15)).pack(side=tk.TOP)
    #tk.Label(window, text="(optional parameters)\n", font=('Arial bold',13)).pack(side=tk.TOP)

    # add the keep_tmp_files
    tk.Label(window, text='\n1) Keep temporary files?', font=('Arial bold',15)).pack(side=tk.TOP)

    def set_keep_tmp_files_True():
        opt.keep_tmp_files = True
        keep_tmp_files_True_button["font"] = ('Arial bold',18)
        keep_tmp_files_False_button["font"] = ('Arial bold',11)

    def set_keep_tmp_files_False():
        opt.keep_tmp_files = False
        keep_tmp_files_True_button["font"] = ('Arial bold',11)
        keep_tmp_files_False_button["font"] = ('Arial bold',18)

    keep_tmp_files_True_button = tk.Button(window, text="Yes", padx=15, pady=10, font=('Arial bold',11), command=set_keep_tmp_files_True)
    keep_tmp_files_False_button = tk.Button(window, text="No", padx=15, pady=10, font=('Arial bold',18), command=set_keep_tmp_files_False)

    keep_tmp_files_True_button.pack(side=tk.TOP, expand=True)
    keep_tmp_files_False_button.pack(side=tk.TOP, expand=True)

    # add the entry of the pseudocount_log2_concentration
    tk.Label(window, text='\n2) pseudocount concentration:', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text='(float added to concentrations\nfor susceptibility measures)', font=('Arial bold',13)).pack(side=tk.TOP)
    pseudocount_log2_concentration_entry = tk.Entry(window, font=('Arial bold',13))
    pseudocount_log2_concentration_entry.insert(0, str(opt.pseudocount_log2_concentration))
    pseudocount_log2_concentration_entry.pack(side=tk.TOP, expand=True)

    # add the entry of the min_nAUC_to_beConsideredGrowing
    tk.Label(window, text='\n3) min nAUC growing:', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text='(minimum nAUC (float)\nto be considered growing)', font=('Arial bold',13)).pack(side=tk.TOP)
    min_nAUC_to_beConsideredGrowing_entry = tk.Entry(window, font=('Arial bold',13))
    min_nAUC_to_beConsideredGrowing_entry.insert(0, str(opt.min_nAUC_to_beConsideredGrowing))
    min_nAUC_to_beConsideredGrowing_entry.pack(side=tk.TOP, expand=True)

    # add the entry of the min_points_to_calculate_resistance_auc
    tk.Label(window, text='\n4) min concentrations rAUC:', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text='(minimum # concentrations \nnecessary to calculate rAUC)', font=('Arial bold',13)).pack(side=tk.TOP)
    min_points_to_calculate_resistance_auc_entry = tk.Entry(window, font=('Arial bold',13))
    min_points_to_calculate_resistance_auc_entry.insert(0, str(opt.min_points_to_calculate_resistance_auc))
    min_points_to_calculate_resistance_auc_entry.pack(side=tk.TOP, expand=True)

    # run and capture the entries
    tk.Label(window, text='\n5) click to Run:', font=('Arial bold',15)).pack(side=tk.TOP, expand=True)
    def run_module(): 

        # get the extra measurements
        opt.pseudocount_log2_concentration = float(pseudocount_log2_concentration_entry.get())
        opt.min_nAUC_to_beConsideredGrowing = float(min_nAUC_to_beConsideredGrowing_entry.get())
        opt.min_points_to_calculate_resistance_auc = int(min_points_to_calculate_resistance_auc_entry.get())

        # run
        window.destroy()
    
    tk.Button(window, text="Run", padx=15, pady=15, font=('Arial bold',13), command=run_module).pack(side=tk.TOP, expand=True)

    # run and debug
    window.mainloop()

def run_docker_cmd(docker_cmd, final_files, print_cmd=True):

    """Runs docker cmd with proper debugging"""

    # debug
    if all([not file_is_empty(f) for f in final_files]) and len(final_files)>0: 
        print("All files are already generated, skipping this step...")
        return

    # add the run_app.py command
    docker_cmd += ' %s bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate main_env > /dev/null 2>&1 && /workdir_app/scripts/run_app.py 2>/output/docker_stderr.txt"'%opt.docker_image

    # log
    if print_cmd is True: print("Running docker image with the following cmd:\n---\n%s\n---\n"%docker_cmd)

    # define the docker stderr
    docker_stderr = "%s%sdocker_stderr.txt"%(opt.output, get_os_sep())

    # run
    try: run_cmd(docker_cmd)
    except: 
        print("\n\nERROR: The run of the pipeline failed. This is the error log (check it to fix the error):\n---\n%s\n---\nExiting with code 1!"%("".join(open(docker_stderr, "r").readlines())))
        sys.exit(1)

    # clean
    remove_file(docker_stderr)




def get_coords_one_image_GUIapp(colonizer_coordinates_one_spot, coordinate_obtention_dir_plate, latest_image, backbone_title):

    """Generates the colonizer_coordinates_one_spot file, which has the colonyzer coordinates for the one image in coordinate_obtention_dir_plate. This function generates the GUI app to select the points."""

    # define the name
    image_name = "%s%s%s"%(coordinate_obtention_dir_plate, get_os_sep(), latest_image)

    # get the size of the image
    image_w, image_h = PIL_Image.open(image_name).size

    # start the window     
    window = tk.Tk()  
    window.geometry("%ix%i"%(image_w, image_h))

    # define image that can be added to canvas
    img = ImageTk.PhotoImage(PIL_Image.open(image_name))  

    # create canvas 
    canvas = tk.Canvas(window, width = image_w, height = image_h)  
    canvas.pack()  
    canvas.create_image(0, 0, anchor=tk.constants.NW, image=img) 

    # define the title
    initial_tilte = "%s. Click upper-left spot."%backbone_title
    window.title(initial_tilte)

    # init variables
    dict_data = {"n_left_clicks":0}
    expected_keys = ["upper_left_X", "upper_left_Y", "lower_left_X", "lower_left_Y"]
    for k in expected_keys: dict_data[k] = -1

    # define the effect of the left click to insert coordinates
    def save_coordinates_on_left_click(event):

        # update clicks
        dict_data["n_left_clicks"]+=1

        # action of the first click: define upper left sport
        if dict_data["n_left_clicks"]==1:

            canvas.create_rectangle(event.x-3, event.y-3, event.x+3, event.y+3, fill="green")
            window.title("%s. Click lower-right spot | Double-click to re-start"%backbone_title)
            dict_data["upper_left_X"] = event.x
            dict_data["upper_left_Y"] = event.y

        # action of the second click: define lower right
        elif dict_data["n_left_clicks"]==2:

            # create rectange of the spot
            canvas.create_rectangle(event.x-3, event.y-3, event.x+3, event.y+3, fill="red")
            window.title("%s. Enter to accept points | Double-click to re-start"%backbone_title)

            # define the width of the rectangle
            w_one_spot_rows = (event.y - dict_data["upper_left_Y"])/7
            w_one_spot_cols = (event.x - dict_data["upper_left_X"])/11
            w_one_spot = (w_one_spot_rows + w_one_spot_cols)/2
            half_w_one_spot = w_one_spot*0.5

            # create one rect of each spot
            canvas.create_rectangle(dict_data["upper_left_X"]-half_w_one_spot, dict_data["upper_left_Y"]-half_w_one_spot, dict_data["upper_left_X"]+half_w_one_spot, dict_data["upper_left_Y"]+half_w_one_spot, width=1)
            canvas.create_rectangle(event.x-half_w_one_spot, event.y-half_w_one_spot, event.x+half_w_one_spot, event.y+half_w_one_spot, width=1)

            # keep the coordinates
            dict_data["lower_left_X"] = event.x
            dict_data["lower_left_Y"] = event.y

    canvas.bind("<Button-1>", save_coordinates_on_left_click)

    # define the effect of the secondary click to restore everything
    def restart_canvas(r_event):

        # remove objects from canvas and reload image
        canvas.delete("all")
        canvas.create_image(0, 0, anchor=tk.constants.NW, image=img) 

        # restart dict
        dict_data["n_left_clicks"] = 0
        for k in expected_keys: dict_data[k] = -1

        # reset title
        window.title(initial_tilte)

    canvas.bind("<Double-1>", restart_canvas)

    # button to destroy
    def destroy_w(e): window.destroy()
    window.bind("<Return>", destroy_w)

    # run the window while not all the coordinates have been defined
    window.mainloop() 

    # checks
    for k in expected_keys:
        if dict_data[k]==-1: raise ValueError("%s should be set. Make sure that you clicked all the spots."%k)

    # write the colonizer_coordinates_one_spot
    coordinates_str = ",".join([str(dict_data[k]) for k in expected_keys])
    lines = ["######", 
             "default,96,%s,%s"%(coordinates_str, date.today()),
             "######",
             "%s,96,%s"%(latest_image, coordinates_str),
             ""]

    open(colonizer_coordinates_one_spot, "w").write("\n".join(lines))


def get_coordinates_are_correct_by_running_colonyzer_one_image(dest_processed_images_dir, plate_batch, plate, sorted_image_names, docker_cmd, factor_resize):

    """For a given plate batch and plate, check if the images are correct"""


    #### RUN COLONYZER #######
    print("checking that coordinates are correct...")

    # create a dir for analyze_images_run_colonyzer
    tmpdir = get_os_sep().join(dest_processed_images_dir.split(get_os_sep())[0:-2])
    images_for_colonyzer_dir = "%s%simages_for_colonyzer"%(tmpdir, get_os_sep())
    delete_folder(images_for_colonyzer_dir); make_folder(images_for_colonyzer_dir)

    # add necessary files
    for f in [sorted_image_names[0], sorted_image_names[-1], "Colonyzer.txt.tmp"]:
        if f=="Colonyzer.txt.tmp": dest_f = "Colonyzer.txt"
        else: dest_f = f
        shutil.copy("%s%s%s"%(dest_processed_images_dir, get_os_sep(), f), "%s%s%s"%(images_for_colonyzer_dir, get_os_sep(), dest_f))

    # run module analyze_images_run_colonyzer to run colonyzer on images_for_colonyzer_dir
    run_docker_cmd('%s -e MODULE=analyze_images_run_colonyzer -v "%s":/images_for_colonyzer'%(docker_cmd, images_for_colonyzer_dir), [], print_cmd=False)

    ##########################

    ########### GUI APP TO VALIDATE COORDINATES #############

    # define the latest name
    latest_image = sorted_image_names[-1]
    image_name = "%s%soutdir_colonyzer%soutput_diffims_greenlab_lc%sOutput_Images%s%s_AREA.png"%(images_for_colonyzer_dir, get_os_sep(), get_os_sep(), get_os_sep(), get_os_sep(), latest_image.split(".tif")[0])
    downsized_image_name = "%s%sresized_last_image.png"%(images_for_colonyzer_dir, get_os_sep())

    # generate downsized_image_name
    image_object = PIL_Image.open(image_name)
    original_w, original_h = image_object.size
    image_object.resize((int(original_w*factor_resize), int(original_h*factor_resize))).save(downsized_image_name, optimize=True)
    image_w = original_w*factor_resize
    image_h = original_h*factor_resize

    # start the window     
    window = tk.Tk()  
    window.geometry("%ix%i"%(image_w, image_h))

    # define image that can be added to canvas
    img = ImageTk.PhotoImage(PIL_Image.open(downsized_image_name))  

    # create canvas 
    canvas = tk.Canvas(window, width = image_w, height = image_h)  
    canvas.pack()  
    canvas.create_image(0, 0, anchor=tk.constants.NW, image=img) 

    # define the title
    window.title("%s-plate%i, %s. Press 'Y' to accept coordinates | Press 'N' to reject"%(plate_batch, plate, latest_image))

    # create buttons to set correct_coords
    dict_data = {"correct_coords":None}
    def yes_click(e): 
        dict_data["correct_coords"] = True
        window.destroy()

    def no_click(e): 
        dict_data["correct_coords"] = False
        window.destroy()

    window.bind("<y>", yes_click)
    window.bind("<n>", no_click)

    # run the window
    window.mainloop() 

    # debug
    if dict_data["correct_coords"] is None: raise ValueError("you shoud click 'Y' or 'N'")

    #########################################################

    delete_folder(images_for_colonyzer_dir)
    return dict_data["correct_coords"]


def generate_colonyzer_coordinates_one_plate_batch_and_plate_inHouseGUI(dest_processed_images_dir, coordinate_obtention_dir_plate, sorted_image_names, plate_batch, plate, docker_cmd):

    """Generates a 'Colonyzer.txt' file in each dest_processed_images_dir with all the coordinates."""

    # define the dir with the coordinates for one image
    colonizer_coordinates_one_spot = "%s%sColonyzer.txt"%(coordinate_obtention_dir_plate, get_os_sep())
    colonizer_coordinates = "%s%sColonyzer.txt"%(dest_processed_images_dir, get_os_sep())

    # define the latest image to base the coordinates on
    latest_image = sorted_image_names[-1]

    if file_is_empty(colonizer_coordinates):

        # clean
        remove_file(colonizer_coordinates_one_spot)
        remove_file("%s%s%s"%(coordinate_obtention_dir_plate, get_os_sep(), latest_image))

        # move one resized image to coordinate_obtention_dir_plate. It should have a width of 700
        image_object = PIL_Image.open("%s%s%s"%(dest_processed_images_dir, get_os_sep(), latest_image))
        original_w,  original_h = image_object.size
        factor_resize = 900/original_w
        image_object.resize((int(original_w*factor_resize), int(original_h*factor_resize))).save("%s%s%s"%(coordinate_obtention_dir_plate, get_os_sep(), latest_image), optimize=True)
        downsized_w, donwsized_h = PIL_Image.open("%s%s%s"%(coordinate_obtention_dir_plate, get_os_sep(), latest_image)).size

        # get coordinates
        get_coords_one_image_GUIapp(colonizer_coordinates_one_spot, coordinate_obtention_dir_plate, latest_image, "%s-plate%i, %s"%(plate_batch, plate, latest_image))

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
        expected_w, expected_h = PIL_Image.open("%s%s%s"%(dest_processed_images_dir, get_os_sep(), latest_image)).size
        top_left_x, top_left_y, bottom_right_x, bottom_right_y = [int(x) for x in coordinates_str.split(",")]
        cropped_w = bottom_right_x - top_left_x
        cropped_h = bottom_right_y - top_left_y

        error_log = "Make sure that you are first selecting the upper-left spot and then the lower-right spot."
        for dim, expected_val, cropped_val in [("width", expected_w, cropped_w), ("height", expected_h, cropped_h)]:

            if cropped_val<=0: raise ValueError("The cropped image has <=0 %s. %s"%(dim, error_log))
            if cropped_val>expected_val: raise ValueError("The %s of the cropped image is above the original one. %s"%(dim, error_log))
            if cropped_val<=(expected_val*0.3): raise ValueError("The %s of the cropped image is %s, and the full image has %s. The cropped image should have a %s which is close to the original one. %s"%(dim, cropped_val, expected_val, dim, error_log))
            if cropped_val<=(expected_val*0.5): print("WARNING: The %s of the cropped image is %s, and the full image has %s. The cropped image should have a %s which is close to the original one. %s. If you are sure of this you can skip this warning."%(dim, cropped_val, expected_val, dim, error_log))

        # write tmp file
        non_coordinates_lines = [l for l in open(colonizer_coordinates_one_spot, "r").readlines() if l.startswith("#") or not l.startswith(latest_image)]
        coordinates_lines = ["%s,%s,%s\n"%(image, wells, coordinates_str) for image in sorted_image_names]
        colonizer_coordinates_tmp = "%s.tmp"%colonizer_coordinates
        open(colonizer_coordinates_tmp, "w").write("".join(non_coordinates_lines + coordinates_lines))

        # check if the coordinates are correct by manual inspection. If they are not, continue to try again
        #if get_coordinates_are_correct_by_running_colonyzer_one_image(dest_processed_images_dir, plate_batch, plate, sorted_image_names, docker_cmd, factor_resize) is False: continue

        # final save
        os.rename(colonizer_coordinates_tmp, colonizer_coordinates)


def get_yyyymmddhhmm_tuple_one_image_name(filename):

    """Returns a tuple with the yyyy, mm, dd, hh, mm for one image name"""

    # get the numbers_str with all images
    numbers_str = ""
    recording_numbers = False

    for x in filename:

        # start recording once you find some number
        if recording_numbers is False and x.isdigit() and int(x)>0: recording_numbers = True

        # if you are recoding
        if recording_numbers is True and x.isdigit(): numbers_str += x

    # check
    if len(numbers_str)!=12: raise ValueError("We can't define a YYYYMMDDHHMM in %s"%filename)

    # get tuple 
    numbers_tuple = (numbers_str[0:4], numbers_str[4:6], numbers_str[6:8], numbers_str[8:10], numbers_str[10:12])
    numbers_tuple = tuple([int(x) for x in numbers_tuple])

    # checks
    for idx, (name, expected_range) in enumerate([("year", (2000, 2500)), ("month", (1, 12)), ("day", (1, 31)), ("hour", (0, 24)), ("minute", (0, 60))]):
        if numbers_tuple[idx]<expected_range[0] or numbers_tuple[idx]>expected_range[1]: print_with_runtime("WARNING: For file %s the parsed %s is %i, which may be incorrect."%(filename, name, numbers_tuple[idx]))

    return numbers_tuple


def validate_colonyzer_coordinates_one_plate_batch_and_plate_GUI(tmpdir, plate_batch, plate, sorted_image_names):

    """This function opens an image for a given plate and asks for the user input. If the colonyzer coordinates are bad, it removes the coordinates and also the colonyzer_subset runs"""

    # define dirs
    processed_images_dir_plate = "%s%sprocessed_images_each_plate%s%s_plate%i"%(tmpdir, get_os_sep(), get_os_sep(), plate_batch, plate)
    colonyzer_runs_subset_dir_plate = "%s%scolonyzer_runs_subset%s%s_plate%i"%(tmpdir, get_os_sep(), get_os_sep(), plate_batch, plate)
    colonyzer_coords = "%s%sColonyzer.txt"%(processed_images_dir_plate, get_os_sep())

    # define the latest name with area infered
    latest_image = sorted_image_names[-1]
    image_name = "%s%soutput_diffims_greenlab_lc%sOutput_Images%s%s_AREA.png"%(colonyzer_runs_subset_dir_plate, get_os_sep(), get_os_sep(), get_os_sep(), latest_image.split(".tif")[0])
    downsized_image_name = "%s.downsized.png"%(image_name)

    # generate downsized_image_name
    image_object = PIL_Image.open(image_name)
    original_w, original_h = image_object.size
    factor_resize = 900/original_w
    image_object.resize((int(original_w*factor_resize), int(original_h*factor_resize))).save(downsized_image_name, optimize=True)
    image_w = original_w*factor_resize
    image_h = original_h*factor_resize

    # start the window     
    window = tk.Tk()  
    window.geometry("%ix%i"%(image_w, image_h))

    # define image that can be added to canvas
    img = ImageTk.PhotoImage(PIL_Image.open(downsized_image_name))  

    # create canvas 
    canvas = tk.Canvas(window, width = image_w, height = image_h)  
    canvas.pack()  
    canvas.create_image(0, 0, anchor=tk.constants.NW, image=img) 

    # define the title
    window.title("%s-plate%i, %s. Press 'Y' to accept coordinates | Press 'N' to reject"%(plate_batch, plate, latest_image))

    # create buttons to set correct_coords
    dict_data = {"correct_coords":None}
    def yes_click(e): 
        dict_data["correct_coords"] = True
        window.destroy()

    def no_click(e): 

        remove_file(colonyzer_coords)
        delete_folder(colonyzer_runs_subset_dir_plate)

        dict_data["correct_coords"] = False
        window.destroy()

    window.bind("<y>", yes_click)
    window.bind("<n>", no_click)

    # run the window
    window.mainloop() 

    # debug and log
    if dict_data["correct_coords"] is True: print("Selected coordinates are correct for %s-plate%s."%(plate_batch, plate))
    elif dict_data["correct_coords"] is False: print("Selected coordinates are incorrect for %s-plate%s. Repeating coorinate selection..."%(plate_batch, plate))
    else: raise ValueError("you shoud click 'Y' or 'N'")


def get_colonyzer_coordinates_GUI(outdir, docker_cmd):

    """Generates the colonyzer coordinates for each plate from outdir"""

    # define dirs
    tmpdir = "%s%stmp"%(outdir, get_os_sep())
    coordinate_obtention_dir = "%s%scolonyzer_coordinates"%(tmpdir, get_os_sep()); make_folder(coordinate_obtention_dir)
    processed_images_dir_each_plate = "%s%sprocessed_images_each_plate"%(tmpdir, get_os_sep())

    # go through each set of processed images and generate the args list
    all_dirs = [x for x in os.listdir(processed_images_dir_each_plate) if not x.startswith(".")]
    args_coordinates = []
    for I, d in enumerate(sorted(all_dirs)):

        # get full path of the folder with the cropped images
        dest_processed_images_dir = "%s%s%s"%(processed_images_dir_each_plate, get_os_sep(), d)

        # get plate batch and plate
        plate_batch, plate = d.split("_plate"); plate = int(plate)

        # define the path where the coordinates will be calculated
        coordinate_obtention_dir_plate = "%s%s%s_plate%i"%(coordinate_obtention_dir, get_os_sep(), plate_batch, plate); make_folder(coordinate_obtention_dir_plate)

        # define the images name
        sorted_images = sorted({f for f in os.listdir(dest_processed_images_dir) if not f.startswith(".") and f not in {"Colonyzer.txt.tmp", "Colonyzer.txt"}}, key=get_yyyymmddhhmm_tuple_one_image_name)

        # keep
        args_coordinates.append((dest_processed_images_dir, coordinate_obtention_dir_plate, sorted_images, plate_batch, plate))

    # define the final coordinate files
    final_files = ["%s%sColonyzer.txt"%(x[0], get_os_sep()) for x in args_coordinates]
    final_file_correct = "%s%scoordinates_checking_worked_well.txt"%(tmpdir, get_os_sep())

    # keep trying to generate these files while they are not generated
    while any([file_is_empty(x) for x in final_files]) or file_is_empty(final_file_correct):

        # define the missing files
        missing_final_files = [x for x in final_files if file_is_empty(x)]

        # get the corrdinates files
        for I, (dest_processed_images_dir, coordinate_obtention_dir_plate, sorted_images, plate_batch, plate) in enumerate(args_coordinates):

            if file_is_empty("%s%sColonyzer.txt"%(dest_processed_images_dir, get_os_sep())):

                print('Getting coordinates for plate_batch %s and plate %i %i/%i'%(plate_batch, plate, I+1, len(all_dirs)))
                generate_colonyzer_coordinates_one_plate_batch_and_plate_inHouseGUI(dest_processed_images_dir, coordinate_obtention_dir_plate, sorted_images, plate_batch, plate, docker_cmd)

        # generate a succes window
        generate_closing_window("Coordinates set. Checking them...")

        # run colonyzer in parallel using a subset of the images 
        run_docker_cmd("%s -e MODULE=analyze_images_run_colonyzer_subset_images"%(docker_cmd), [], print_cmd=False)

        # show the images for validation, and remove the colonyzer coordinates that did not work well
        print("Validation of the coordinates...")
        for I, (dest_processed_images_dir, coordinate_obtention_dir_plate, sorted_images, plate_batch, plate) in enumerate(args_coordinates):
            print('Validating coordinates for plate_batch %s and plate %i %i/%i'%(plate_batch, plate, I+1, len(all_dirs)))
            validate_colonyzer_coordinates_one_plate_batch_and_plate_GUI(tmpdir, plate_batch, plate, sorted_images)

        # create the final file indicating that this worked well
        if not any([file_is_empty(x) for x in final_files]): open(final_file_correct, "w").write("coodinates selection worked well...")

        # generate a success 
        generate_closing_window("Coordinates validated. Running analysis...")

