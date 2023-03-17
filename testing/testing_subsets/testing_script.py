# This is a python script to test that all the subsets testing work

# imports
import os, sys, platform

# define the os_sep
if "/" in os.getcwd(): os_sep = "/"
elif "\\" in os.getcwd(): os_sep = "\\"
else: raise ValueError("unknown OS. This script is %s"%__file__)

# define the current directory
CurDir = os_sep.join(os.path.realpath(__file__).split(os_sep)[0:-1])
main_script = '%s%s..%s..%smain.py'%(CurDir, os_sep, os_sep, os_sep)

# import main functions
sys.path.insert(0, '%s%s..%s..%sscripts'%(CurDir, os_sep, os_sep, os_sep))
import main_functions as fun

# get args
if len(sys.argv)>1: all_args = set(sys.argv[1:])
else: all_args = set()
strange_args = all_args.difference({"out_in_desktop", "auto", "keep_tmp"})
if len(strange_args): raise ValueError("invalid args: %s"%strange_args)

# define the OS
running_os = {"Darwin":"mac", "Linux":"linux", "Windows":"windows"}[platform.system()]

# test each of the samples that should work
print("Testing four different types of data...")
for d in ["Classic_spottest_subset", "AST_48h_subset", "Fitness_only_subset", "Stress_plates_subset"]:
    print("testing %s..."%d)

    # define the dirs
    test_dir = "%s%s%s"%(CurDir, os_sep, d)
    input_dir_source = "%s%sinput"%(test_dir, os_sep)

    if "out_in_desktop" in all_args: 
        output_dir = "%s/Desktop/testing_Q-PHAST_%s"%(os.getenv("HOME"), d)
        input_dir = "%s/Desktop/testing_Q-PHAST_%s_input"%(os.getenv("HOME"), d)

        if not os.path.isdir(input_dir):
            print("Generating input...")
            input_dir_tmp = "%s_tmp"%input_dir
            fun.run_cmd("rsync -rv %s/ %s/"%(input_dir_source, input_dir_tmp))
            os.rename(input_dir_tmp, input_dir)

    else: 
        output_dir = "%s%soutput_Q-PHAST"%(test_dir, os_sep)
        input_dir = input_dir_source

    #fun.delete_folder(output_dir)
    finish_file = "%s%sfinished.txt"%(output_dir, os_sep)

    # run the python script
    if fun.file_is_empty(finish_file):

        cmd = "python %s --os %s --input %s --docker_image mikischikora/q-phast:v1 --output %s --pseudocount_log2_concentration 0.1 --min_nAUC_to_beConsideredGrowing 0.5 --min_points_to_calculate_resistance_auc 4"%(main_script, running_os, input_dir, output_dir)
        if "auto" in all_args: cmd += " --auto_accept --coords_1st_plate"
        if "keep_tmp" in all_args: cmd += " --keep_tmp_files"
        fun.run_cmd(cmd)     
        open(finish_file, "w").write("finished")

# test different plate layouts errors
print("\n\nTesting different plate layouts...")
stress_dir = "%s%sStress_plates_subset"%(CurDir, os_sep)
playouts_dir = "%s%sdifferent_platelayouts"%(stress_dir, os_sep)
if "out_in_desktop" in all_args: testing_playouts_dir = "%s/Desktop/testing_Q-PHAST_plate_layouts"%(os.getenv("HOME"))
else: testing_playouts_dir = "%s%stesting_different_platelayouts"%(stress_dir, os_sep)
fun.make_folder(testing_playouts_dir)

for p in sorted(os.listdir(playouts_dir)):

    # get the numeric pID
    if p[0] in {"~", "."}: continue
    print("testing %s..."%p)
    pID = int(p.split("_")[2])

    #if pID!=12: continue

    # define dirs
    p_dir = "%s%stesting_plate_layout_%i"%(testing_playouts_dir, os_sep, pID); fun.make_folder(p_dir)
    input_dir = "%s%sinput"%(p_dir, os_sep); fun.make_folder(input_dir)
    output_dir = "%s%soutput"%(p_dir, os_sep)
    docker_stderr = "%s%sdocker_stderr.txt"%(output_dir, os_sep)
    finish_file = "%s%sfinished.txt"%(output_dir, os_sep)

    # run the python script
    if fun.file_is_empty(finish_file):

        # create inputs
        if fun.file_is_empty("%s%s%s"%(input_dir, os_sep, p)): fun.copy_file("%s%s%s"%(playouts_dir, os_sep, p), "%s%s%s"%(input_dir, os_sep, p))
        images_dir_source = "%s%sinput%sSC1"%(stress_dir, os_sep, os_sep)
        images_dir_dest = "%s%sSC1"%(input_dir, os_sep); fun.make_folder(images_dir_dest)
        for f in os.listdir(images_dir_source): 
            if fun.file_is_empty("%s%s%s"%(images_dir_dest, os_sep, f)): fun.copy_file("%s%s%s"%(images_dir_source, os_sep, f), "%s%s%s"%(images_dir_dest, os_sep, f))

        # define cmd
        cmd = "python %s --os %s --input %s --docker_image mikischikora/q-phast:v1 --output %s --pseudocount_log2_concentration 0.1 --min_nAUC_to_beConsideredGrowing 0.5 --min_points_to_calculate_resistance_auc 4"%(main_script, running_os, input_dir, output_dir)
        if "keep_tmp" in all_args: cmd += " --keep_tmp_files"
        if "auto" in all_args: cmd += " --auto_accept --coords_1st_plate"

        # run a bit differently for different IDs
        if pID in {5, 11}: cmd += " --break_after step1"

        # redirect stdout
        stdout = "%s%sstdout.txt"%(input_dir, os_sep)
        cmd += " > %s"%stdout

        # map each pID with a line that is expected in the last error line
        pID_to_error_text = {16 : "plate layout is not properly formatted",
                             12 : "We found a strain called '0'",
                             10 : "The subfolder <images>/SC2 should exist",
                             13 : "There can't be empty cells",
                             14 : "one plate for any given drug and concentration",
                             15 : "one plate for any given drug and concentration",
                             17 : "plate layout is not properly formatted",
                             2 : "In the bad spots, there are strange values in plate_batch",
                             4 : "The rows should be A-H letters",
                             6 : "one plate with a concentration of 0.0",
                             7 : "compounds and concentrations layouts do not match",
                             8 : "compounds and concentrations layouts do not match",
                             9 : "not the same between compounds and concentrations layouts"

        }

        # for some cases you require a specific error
        if pID in pID_to_error_text:

            try: fun.run_cmd(cmd)
            except: 
                last_error_line = open(docker_stderr, "r").readlines()[-1]
                if not pID_to_error_text[pID] in last_error_line: raise ValueError("For %s, the last error line should include '%s'. The last error line is '%s'."%(pID, pID_to_error_text[pID], last_error_line))

        # require correct ending as a test
        else: 

            try: fun.run_cmd(cmd)
            except: raise ValueError("Error in %s. Stdout:\n\n%s\nError in %s"%(pID, "".join(open(stdout, "r").readlines()), pID))

        # write finish file
        open(finish_file, "w").write("finished")


print("\n\nSUCCESS!! Q-PHAST works as expected.")
