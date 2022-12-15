




def run_analyze_images(plate_layout_file, images_dir, outdir, keep_tmp_files, pseudocount_log2_concentration, min_nAUC_to_beConsideredGrowing, min_points_to_calculate_resistance_auc, automatic_coordinates):

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
    
    # define the tmpdir
    tmpdir = "%s/tmp"%outdir
    make_folder(tmpdir)

    # define several dirs of the final output
    growth_curves_dir = "%s/growth_curves"%outdir; make_folder(growth_curves_dir) # a dir with a plot for each growth curve

    ##########################

    ##### CREATE THE PROCESSED IMAGES #####

    print_with_runtime("Getting processed images ...")
    print_with_runtime("Parsing directories to get images and check that they are properly named...")

    # define dirs
    linked_raw_images_dir = "%s/linked_raw_images"%tmpdir; make_folder(linked_raw_images_dir)
    processed_images_dir = "%s/processed_images"%tmpdir; make_folder(processed_images_dir)
    plate_batch_to_images = {}
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

        # sort images by date
        plate_batch_to_images[plate_batch] = sorted(plate_batch_to_images[plate_batch], key=get_yyyymmddhhmm_tuple_one_image_name)

    # checks
    if len(all_endings)!=1: raise ValueError("All files should end with the same. These are the endings: %s"%all_endings)

    # linking images
    print_with_runtime("Linking images in parallel on %i threads..."%multiproc.cpu_count())
    run_function_in_parallel(inputs_fn_linking, soft_link_files)

    # log
    start_time_rotation_contrast = time.time()

    # rotate each plate set at the same time (not in parallel)
    for I, plate_batch in enumerate(sorted(plate_batch_to_images)): process_image_rotation_and_contrast_all_images_batch(I+1, len(plate_batch_to_raw_outdir),plate_batch_to_raw_outdir[plate_batch], plate_batch_to_processed_outdir[plate_batch], plate_batch, plate_batch_to_images[plate_batch], image_ending)

    # log
    print_with_runtime("Rotating images and Improving contrast took %.3f seconds"%(time.time()-start_time_rotation_contrast))

    #######################################

    ##### RUN THE IMAGE ANALYSIS PIPELINE FOR EACH PLATE AND PLATE SET #####
    print_with_runtime("Getting image analysis data for each plate")

    # define the list of inputs, which will be processed below
    inputs_fn_coords = []
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

        # keep dirs
        inputs_fn_coords.append((dest_processed_images_dir, plate_batch, plate))

    # get the cropped images
    print_with_runtime("Cropping images in parallel on %i threads..."%multiproc.cpu_count())
    run_function_in_parallel(inputs_fn_cropping, generate_croped_image)

    # go through each plate in each plate set and define the coordinates of the plates manually, using the latest timepoint for each plate
    coordinate_obtention_dir = "%s/colonyzer_coordinates"%tmpdir; make_folder(coordinate_obtention_dir)

    for I,(dest_processed_images_dir, plate_batch, plate) in enumerate(inputs_fn_coords):

        print_with_runtime('Getting coordinates for plate_batch %s and plate %i (%s plate) %i/%i. Click on the upper-left and lower-right spots, then "spacebar" and "g" to save...'%(plate_batch, plate, plateID_to_quadrantName[plate], I+1, len(inputs_fn_coords)))
        coordinate_obtention_dir_plate = "%s/%s_plate%i"%(coordinate_obtention_dir, plate_batch, plate); make_folder(coordinate_obtention_dir_plate)
        generate_colonyzer_coordinates_one_plate_batch_and_plate(dest_processed_images_dir, coordinate_obtention_dir_plate, plate_batch_to_images[plate_batch], automatic_coordinates, plate_batch, plate)

    # go through each plate and plate set and run the fitness calculations
    outdir_fitness_calculations = "%s/fitness_calculations"%tmpdir; make_folder(outdir_fitness_calculations)
    inputs_fn_fitness = []

    for I, (proc_images_folder, plate_batch, plate) in enumerate(inputs_fn_coords): inputs_fn_fitness.append((I+1, len(inputs_fn_coords), proc_images_folder, "%s/%s_plate%i"%(outdir_fitness_calculations, plate_batch, plate), plate_batch, plate, plate_batch_to_images[plate_batch], cp.deepcopy(df_plate_layout)))

    print_with_runtime("Analyzing images in parallel on %i threads..."%multiproc.cpu_count())
    run_function_in_parallel(inputs_fn_fitness, get_df_integrated_fitness_measurements_one_plate_batch_and_plate)

    # integrate the results of the fitness
    print_with_runtime("Integrating fitness datasets...")

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
        df_growth_measurements_all_timepoints = df_growth_measurements_all_timepoints.append(df_growth_measurements)

        # keep the growth curves in the final output
        copy_file("%s/%s_plate%i/output_diffims_greenlab_lc/output_plots.pdf"%(outdir_fitness_calculations, plate_batch, plate), "%s/batch_%s-plate%i.pdf"%(growth_curves_dir, plate_batch, plate))


    # define the merging fields
    merge_fields = ["plate_batch", "plate", "row", "column"]

    # keep some fields and merge the df_growth_measurements_all_timepoints
    df_growth_measurements_all_timepoints = df_growth_measurements_all_timepoints.rename(columns={"Row":"row", "Column":"column"})
    df_growth_measurements_all_timepoints = df_growth_measurements_all_timepoints[merge_fields + ['X.Offset', 'Y.Offset', 'Area', 'Trimmed', 'Threshold', 'Intensity', 'Edge.Pixels', 'redMean', 'greenMean', 'blueMean', 'redMeanBack', 'greenMeanBack', 'blueMeanBack', 'Edge.Length', 'Tile.Dimensions.X', 'Tile.Dimensions.Y', 'x', 'y', 'Diameter', 'Date.Time', 'Inoc.Time', 'Timeseries.order', 'Expt.Time', 'Growth']]
    df_growth_measurements_all_timepoints = df_growth_measurements_all_timepoints.merge(df_plate_layout, how="left", left_on=merge_fields, right_on=merge_fields, validate="many_to_one").reset_index(drop=True)

    # keep some fields and merge the df_fitness_measurements
    df_fitness_measurements = df_fitness_measurements.rename(columns={"Row":"row", "Column":"column"})
    df_fitness_measurements_interesting_fields = merge_fields + ['spotID', 'Inoc.Time', 'XOffset', 'YOffset', 'K', 'r', 'g', 'v', 'objval', 'd0', 'nAUC', 'nSTP', 'nr', 'nr_t', 'maxslp', 'maxslp_t', 'Gene', 'MDP', 'MDR', 'MDRMDP', 'glog_maxslp', 'DT', 'AUC', 'rsquare', 'DT_h', 'DT_h_goodR2', 'inv_DT_h_goodR2']
    df_fitness_measurements = df_fitness_measurements[df_fitness_measurements_interesting_fields]
    df_fitness_measurements = df_fitness_measurements.merge(df_plate_layout, how="left", left_on=merge_fields, right_on=merge_fields, validate="one_to_one").reset_index(drop=True)

    # checks
    for k in df_fitness_measurements.keys(): check_no_nans_series(df_fitness_measurements[k])
    for k in set(df_growth_measurements_all_timepoints.keys()).difference({"redMean", "greenMean", "blueMean"}): check_no_nans_series(df_growth_measurements_all_timepoints[k])

    # save the dataframe with all the timepoonts
    save_df_as_tab(df_growth_measurements_all_timepoints, "%s/growth_measurements_all_timepoints.tab"%outdir)

    ########################################################################

    #### INTEGRATE THE PLATE SETS TO MEASURE SUSCEPTIBILITY ####

    # run the AST calculations based on all plates
    print_with_runtime("Getting the susceptibility measurements. Adding %s as a pseudocount to calculate log2 concentrations. Considering spots with a  nAUC<%s to be not growing. Calculations are only made on strains with at least %s concentrations..."%(pseudocount_log2_concentration, min_nAUC_to_beConsideredGrowing, min_points_to_calculate_resistance_auc))

    # add fields to the fitness df that are necessary to run the AST calculations
    df_fitness_measurements["replicateID"] = "r" + df_fitness_measurements.row.apply(str) + "c" + df_fitness_measurements.column.apply(str)
    df_fitness_measurements["sampleID"] = df_fitness_measurements.strain + "_" + df_fitness_measurements.replicateID
    df_fitness_measurements["log2_concentration"] = np.log2(df_fitness_measurements.concentration + pseudocount_log2_concentration)
    df_fitness_measurements["is_growing"]  = df_fitness_measurements.nAUC>=min_nAUC_to_beConsideredGrowing # the nAUC to be considered growing

    # debugs
    for d in all_drugs:
        expected_nsamples = len(set(df_fitness_measurements[(df_fitness_measurements.drug==d)].sampleID))
        if sum(df_fitness_measurements.concentration==0.0)!=expected_nsamples: raise ValueError("There should be %i wells with concentration==0 for drug==%s. Note that this script expects the strains in each spot to be the same in all analyzed plates of the same drug."%(expected_nsamples, d))

    # init variables
    df_susceptibility = pd.DataFrame()
    fitness_estimates  = ["K", "r", "nr", "maxslp", "MDP", "MDR", "MDRMDP", "DT", "AUC", "DT_h", "nAUC", "DT_h_goodR2"]

    # get the fitness df with relative values (for each drug, the fitness relative to the concentration==0), and save these measurements
    df_fitness_measurements = get_fitness_df_with_relativeFitnessEstimates(df_fitness_measurements, fitness_estimates)

    # save the fitness df
    save_df_as_tab(df_fitness_measurements, "%s/fitness_measurements.tab"%outdir)

    # get the susceptibility df for each sampleID
    susceptibility_df = get_susceptibility_df(df_fitness_measurements, fitness_estimates, pseudocount_log2_concentration, min_points_to_calculate_resistance_auc, "%s/susceptibility_measurements.tab"%outdir)

    # generate a reduced, simple, susceptibility_df
    simple_susceptibility_df = susceptibility_df[(susceptibility_df.fitness_estimate=="nAUC_rel")].groupby(["drug", "strain"]).apply(get_row_simple_susceptibility_df_one_strain_and_drug).reset_index(drop=True)

    save_df_as_tab(simple_susceptibility_df, "%s/susceptibility_measurements_simple.tab"%outdir)
    simple_susceptibility_df.to_excel("%s/susceptibility_measurements_simple.xlsx"%outdir, index=False)

    ############################################################

    ######### MAKE PLOTS ##########

    # growth at different drugs
    plot_growth_at_different_drugs(susceptibility_df, df_fitness_measurements, "%s/drug_vs_fitness"%outdir, fitness_estimates, min_nAUC_to_beConsideredGrowing)

    ###############################
    
    ###### CLEAN #####

    # clean, unless specified otherwise
    if keep_tmp_files is False: delete_folder(tmpdir)

    #################


 
# check that the pygame can be executed
fun.print_with_runtime("Checking that pygame (a GUI library used here) works...")
pygame_std = "/output/pygame_std.txt"
fun.run_cmd("%s/pygame_example_script.py > %s 2>&1"%(ScriptsDir, pygame_std), env="colonyzer_env")
fun.remove_file(pygame_std)



# configure for each os (for GUI)
if opt.os=="linux":

    docker_cmd = 'xhost +local:docker && %s'%docker_cmd
    docker_cmd += ' -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix'

elif opt.os=="mac":

    local_IP = str(subprocess.check_output("ifconfig en0 | grep 'inet '", shell=True)).split("inet")[1].split()[0]
    docker_cmd = 'xhost +%s && %s'%(local_IP, docker_cmd)
    docker_cmd += ' -e DISPLAY=%s:0'%local_IP

elif opt.os=="windows":

    docker_cmd += " -e DISPLAY=host.docker.internal:0.0"
