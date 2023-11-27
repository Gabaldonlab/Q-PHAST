## General aim of Q-PHAST

The Q-PHAST pipeline generates fitness and susceptibility measurements for various strains grown in 96-well agar plates, based on images taken at different timepoints. Fitness measurements reflect how much a sample grows in a given drug concentration (i.e. the total growth after N hours of strain X in [drug Y]==0.1). Conversely, susceptibility measurements reflect fitness differences across drug concentrations (i.e. Minimum Inhibitory Concentration for drug Y of strain X). 

## Running image analysis pipeline

To illustrate the running we will use an example experiment in which we measured antifungal susceptibility and fitness in anidulafungin in 24 strains and 12 drug concentrations (one of them is 0). The images and plate layout file are [here](https://github.com/Gabaldonlab/Q-PHAST/tree/main/testing/testing_subsets/AST_48h_subset/input). You may follow these steps to get the fitness/susceptibility calculations (this would work for the docker image `mikischikora/q-phast:v1`):

- Optional: If you want to ignore some spots in the susceptibility and fitness measurements (i.e. because you see contamination) you can 'red-flag' them by adding them to the 'Bad Spots' table from `plate_layout.xlsx`. In this example we remove two spots. Any spots marked as 'bad spot' will not be considered in the fitness and susceptibility measurements. Note that, beyond this manual setting of bad spots, the pipeline will also automatically detect bad spots as those that have outlier fitness values as compared to the other techincal replicates of a given strain.

- Initialize the 'docker daemon' to start using docker. You can do this by either running `sudo systemctl start docker` from the terminal (LINUX) or executing 'Docker Desktop' (WINDOWS/MAC).

- Run the interactive app `main.py`. You have to follow these steps:
  
  - Open a terminal that has `python`, `tk`, `pandas` and `pillow` packages installed. If you installed these with Anaconda Navigator, you can open such a terminal by 1) running Anaconda Navigator, 2) going to 'Environments', 3) right-clicking on the used environment and 4) clicking on 'Launch terminal'.

  - Execute the `main.py` from the terminal. Type `python <path to main.py>` (i.e. `python /home/mschikora/Downloads/Q-PHAST/main.py`) and hit `Enter`. To get `<path to main.py>` you may open the `Q-PHAST` folder in your Files app and drag the file `main.py` to the terminal.

- Once you execute the interactive app, you'll be asked to provide the input/output files and parameters necessary to run the pipeline. You'll have to provide them in the following windows that pop-up sequentially:

  - The first two windows require you setting the OS and the docker image.

  - The 3d window requires the 'mandatory' inputs: input folder (with the plate layout and images formatted as in the [example](https://github.com/Gabaldonlab/Q-PHAST/tree/main/testing/testing_subsets/AST_48h_subset/input)) and output folder (where all results will be saved).

  - The 4th window asks whether you want manual verification of coordinates and bad spots. If you click on 'Yes' (recommended), the pipeline will require for manual verification of 1) the spot coordinates in all plates and 2) automatically-inferred bad spots (described above). If you click on 'No' there will be no manual verification, meaning that some of the results may be biased.

  - The 5th window is useful to tune the optional parameters of the pipeline. These are relevant because they can affect the fitness measurements, and it might be interesting to tune them in some experiments (Se section 'Important Notes' below for more details). Once you click on 'Run', the pipeline will start, and the running log will be printed in the terminal.


## Important notes

- You can run `main.py` in a non-interactive mode, providing all input/ouput files and parameters as command-line arguments of the script. Run `main.py -h` for more details.

- The optional arguments may be necessary to tune in some situations. Below are examples of why this is the case:

  - 'Hours of experiment' refers to the hours in which the fitness measurements are made. By default it is set to 24 hours, but it may be changed in some situations. For instance, if the total time of the experiment is below or above 24h it could be relevant to change this parameter. In addition, in some experiments the time to reach a stationary growth phase is highly variable across conditions, and it may be suitable to perform fitness measurements in a time were all strains are growing exponentially (i.e. after 10 or 15 hours, instead of 24).

  -  'min nAUC growing' indicates the minimum nAUC (a commonly-used fitness estimate, see [Q-PHAST outputs](https://github.com/Gabaldonlab/Q-PHAST/blob/main/wiki/output.md))


  - 'Enhance image contrast' can be either True or False. By default we recommend enhancing image contrast, as in some experimental settings the contrast might be insufficient to capture slow-growing spots. However, changing contrast may affect the fitness calculations in some cases, so it could be relevant to also analyze the images without contrast enhancing.
















 is set to 24 by default, but it can be adjusted 





  - Click on the appropiate Operating System, docker image, the output folder (where all files will be saved).

  - Provide the plate layout file (`plate_layout.xlsx`) and the images folder (`images`). Click on 'Run' to save this information and continue to the next step.

  - Optional: The last interactive window is necessary to tune the parameters of the susceptibility measurements. This is the meaning of the parameters:

    - Keep temporary files: Set to 'Yes' if you want to save all the temporary files. This is only recommended for debugging.

    - pseudocount concentration: This is a float that is added to concentrations to get rAUC measurements where the X axis is log2(concentration). We set a default of 0.1, which may be tuned depending on the concentration range.

    - min nAUC growing: This is a float that indicates the minimum nAUC required to consider that a spot is growing. This is added in the 'is_growing' field. Note that, for the simplified susceptibility measurements (saved into the `susceptibility_measurements_simple.tab` file ), only replicates where the concentration==0 is growing will be considered.

    - min concentrations rAUC: This is an integer that indicates the minimum number of concentrations required to calculate rAUC. Note that, when using the 'bad_spot' field, you may get some concentration-vs-growth curves with few points (resulting in poor rAUC calculations). This parameter allows you to set a minimum number of concentrations to get robust rAUC calculations. rAUC will not be calculated on replicates with less points.

  - Once you have set the parameters you can click on 'Run' to analyze the images. Follow the log printed in the terminal to understand what is happening. At some point the pipeline asks the user to define the coordinates of the top-left and lower-right spots. To do so you have to click on them, and then hit 'Enter'. The folder `output_Q-PHAST` will contain all the calculations.





















Similarly, the 'min nAUC growing' might be tuned to change the criteria used to define non-growing spots.




  This is relevant because some fitness estimates (i.e. total growth after N hours) are made after the specified hours


   This is a relevant parameter because the fitness values can be affected by this parameter. 


 the command line. 


  'non-growers'

   were the

  or you see growth saturation long before 24h it may be interesting to reduce the 'Hours of experiment'. 




   []



  Conversely, 'min nAUC growing' is relevant to identify samples that are not growing. 'Enhance contrast' is relevant because it can affect.



- In this example we only used a subset of 5 images (to ease testing), which would be insufficient to get accurate measurements.

- You can also run the `main.py` in a non-interactive manner. To do so you should provide all the arguments (output folder, docker image ...) through the command line. Type `python3 main.py -h` (LINUX/MAC) to understand how to use this script. Note that, if you provide any argument it runs in a non-interactive manner.

- If you break the execution of `main.py` at any point you can re-run it (with the same inputs / parameters) without repeating any steps. Note that the first thing printed to the terminal is the full `main.py` command being used (below the text 'Executing the following command:'). You can copy this command and re-execute it to avoid repeating any steps. Note that this will only work if the inputs (plate layout and images) and parameters are exactly the same.

- The plate layout excel has some constraints:

    - The strain and drug names should be text (non-numeric). For example 'strain-1' is valid, but '100' is not.

    - There can only be one plate with concentration==0 to be used as a reference for susceptibility analyses. If there are no concentration==0 plates the pipeline will only perform fitness calculations.

- In some LINUX systems we saw that the `main.py` execution failed due to permission issues. One solution is to run `sudo python3 main.py`.

- There have to be always 96 strains in the plate layout. If you want to define empty spots you can set the strains as 'H2O'.








If ther 'concentration==0' spot is marked as 'bad_spot' all the others should also be marked as bad spots, or there will be an error in the susceptibility measures.
