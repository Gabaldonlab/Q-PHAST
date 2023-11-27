## General aim of Q-PHAST

The Q-PHAST pipeline generates fitness and susceptibility measurements for various strains grown in 96-well agar plates, based on images taken at different timepoints. These are some important definitions:

- Fitness measurements reflect how much a sample grows in a given drug concentration (i.e. the total growth after N hours of strain X in [drug Y]==0.1). 

- Relative fitness measurements reflect the fitness of a given sample (i.e. strain X) in a given drug concentration normalized by the fitness in the fitness in the absence of the drug (i.e. [drug Y]==0). 

- Susceptibility measurements reflect relative fitness differences across drug concentrations (i.e. Minimum Inhibitory Concentration for drug Y of strain X). 

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

- After a few seconds, the pipeline will show you the last timepoint of each plate and you'll need to manually select the plate boundaries by clicking on the upper-left and lower-right spots of the plate. This is essential for the fitness calculations.

- Once all spot coordinates are set, the pipeline will ask you to validate that they are correct. It will run Colonyzer (a software to infer growth from agar plates) on the last timepoint of each plate and show you the inferred growth intensity in a 96-well grid of spots. You'll need to validate the coordinates by clicking on 'Y'. If you see something strange (i.e. the coordinates are not correct ot there is no growth detected) you may click 'N' to be able to select the coordinates again. This manual validation is essential to ensure that the fitness measurements are correct. Once you validate all corrdinates, the pipeline will calculate fitness for each spot.

- After the fitness calculation, the pipeline will often print a WARNING message, starting with 'We found N (not defined) potential bad spots...'. Basically, Q-PHAST flags as 'bad spots' those that are outliers within the fitness distribution of different replicates of a given strain. If the number of bad spots (N) is very high it means that there was something wrong with the experiment and/or the analysis, and you might need to run it again. Thus, it is important that you check that N is not very high as compared to the total number of spots.

- Short after the WARNING message, the pipeline will ask you to manually verify the automatically-inferred bad spots. For each bad spot, it will show you a composition of different images showing the growth across time of the spot as compared to replicates of the same strain. You have to either agree that a given spot is bad (clicking on 'B') or disagree (clicking on 'G'). This step is essential to ensure that you are only measuring fitness and susceptibility for high-quality spots. After this, the pipeline will run until the end.

Once your run finishes, you can interpret the ouptut following [these instructions](https://github.com/Gabaldonlab/Q-PHAST/blob/main/wiki/output.md).

## Important notes

- You can run `main.py` in a non-interactive mode, providing all input/ouput files and parameters as command-line arguments of the script. Run `main.py -h` for more details.

- The optional arguments may be necessary to tune in some situations. Below are examples of why this is the case:

  - 'Hours of experiment' refers to the hours in which the fitness measurements are made. By default it is set to 24 hours, but it may be changed in some situations. For instance, if the total time of the experiment is below or above 24h it could be relevant to change this parameter. In addition, in some experiments the time to reach a stationary growth phase is highly variable across conditions, and it may be suitable to perform fitness measurements in a time were all strains are growing exponentially (i.e. after 10 or 15 hours, instead of 24).

  - 'min nAUC growing' indicates the minimum nAUC (a commonly-used fitness estimate, see [Q-PHAST outputs](https://github.com/Gabaldonlab/Q-PHAST/blob/main/wiki/output.md)) above which a spot is considered to be growing. This is relevant because in relative fitness and susceptibility measurements we ignore spots where the corresponding no drug spot (concentration==0) is not growing.

  - 'Enhance image contrast' can be either True or False. By default we recommend enhancing image contrast, as in some experimental settings the contrast might be insufficient to capture slow-growing spots. However, changing contrast may affect the fitness calculations in some cases, so it could be relevant to also analyze the images without contrast enhancing if you see unexpcted biases.

- The pipeline follows these steps:

  - Step 1/5: Image processing.
  - Step 2/5: Coordinate selection, which requires manual curation.
  - Step 3/5: Fitness calculations per spot. 
  - Step 4/5: Manual curation of automatically-inferred bad spots.
  - Step 5/5: Integration of the results and generation of outputs.

- Q-PHAST is an interactive pipeline, and you'll need to provide your input in steps 2 and 4. On occasion, it is likely that you'll mis-click the coordinates (setp 2), or that you'll accidentally close the windows defining bad spots (step 4), which will launch an error. Similarly, you may close you computer or the running terminal by accident. If this happens, you don't need to re-run the pipeline from zero. Q-PHAST is designed in a way that you can quickly re-run the pipeline with the exact same inputs and parameters without the need to repeat any analysis steps. One of the first messages that appear in the running log states 'Executing the following command (you may use it to reproduce the analysis):'. You can copy this command and run it from the terminal to re-run the pipeline without repeating steps. Note that this will only work if you do not change any of the arguments (inputs, outputs and parameters), to prevent issues of reproducible runs.

- In this example we only used a subset of 5 images (to ease testing), which would be insufficient to get accurate measurements. For real experiments you need a much higher resolution of timepoints.

- If you break the execution of `main.py` at any point you can re-run it (with the same inputs / parameters) without repeating any steps. Note that the first thing printed to the terminal is the full `main.py` command being used (below the text 'Executing the following command:'). You can copy this command and re-execute it to avoid repeating any steps. Note that this will only work if the inputs (plate layout and images) and parameters are exactly the same.

- In the plate layout excel, there can only be one plate with concentration==0 to be used as a reference for susceptibility analyses. If there are no concentration==0 plates the pipeline will only perform fitness calculations, as relative fitness and susceptibility measurements require a concentration==0.

- In some LINUX systems we saw that the `main.py` execution failed due to permission issues in the output folders. One solution is to run `sudo python main.py`.

- There have to be always 96 strains in the plate layout. If you want to define empty spots you can set the strains as 'H2O'.