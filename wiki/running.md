# Running image analysis pipeline

To illustrate the running we will use an example experiment in which we measured antifungal susceptibility to anidulafungin (ANI) in 24 strains and 12 drug concentrations (one of them is 0). The images and plate layout file are [here](https://github.com/Gabaldonlab/qCAST/tree/main/testing/testing_subset). You may follow these steps to get the fitness/susceptibility calculations (this would work for the docker image `mikischikora/qcast:v0.1`):

- Optional: If you want to ignore some spots in the susceptibility measurements (i.e. because you see contamination) you can 'red-flag' them by adding them to the 'Bad Spots' table from `plate_layout.xlsx`. In this example we remove four spots. Any spots marked as 'bad spots' will not be considered in the susceptibility measurements. If ther 'concentration==0' spot is marked as 'bad_spot' all the others should also be marked as bad spots, or there will be an error in the susceptibility measures.

- Initialize the 'docker daemon' to start using docker. You can do this by either running `sudo systemctl start docker` from the terminal (LINUX) or executing 'Docker Desktop' (WINDOWS/MAC).

- Run the interactive app contained in `main.py`. You have to follow these steps:

    - Access the `qCAST` folder (which contains `main.py`) from the terminal.

        - In MAC, right-click on the folder and select 'Services>New Terminal in folder'.

        - In LINUX, right-click on the folder and select 'Actions>Open terminal here'.

        - In WINDOWS, obtain the Location of `qCAST` (right-click on the folder and check 'Properties'), open the Command Prompt app (terminal) and execute `cd <Location>` (for example `cd C:\Users\mschikora\Desktop\qCAST`).

    - Run the interactive app by executing in the terminal `python3 main.py` (LINUX/MAC) or `py main.py` (WINDOWS). Note that this script depends on the libraries 'tkinter' and 'Pillow' (usually installed with python). If some of them are not installed the script will gently guide you through the installation process.

- Once you execute the interactive app follow these steps:

    - Click on the appropiate Operating System, docker image, the output folder (where all files will be saved).

    - Provide the plate layout file (`plate_layout.xlsx`) and the images folder (`images`). Click on 'Run' to save this information and continue to the next step.

    - Optional: The last interactive window is necessary to tune the parameters of the susceptibility measurements. This is the meaning of the parameters:

      - Keep temporary files: Set to 'Yes' if you want to save all the temporary files. This is only recommended for debugging.

      - pseudocount concentration: This is a float that is added to concentrations to get rAUC measurements where the X axis is log2(concentration). We set a default of 0.1, which may be tuned depending on the concentration range.

      - min nAUC growing: This is a float that indicates the minimum nAUC required to consider that a spot is growing. This is added in the 'is_growing' field. Note that, for the simplified susceptibility measurements (saved into the `susceptibility_measurements_simple.tab` file ), only replicates where the concentration==0 is growing will be considered.

      - min concentrations rAUC: This is an integer that indicates the minimum number of concentrations required to calculate rAUC. Note that, when using the 'bad_spot' field, you may get some concentration-vs-growth curves with few points (resulting in poor rAUC calculations). This parameter allows you to set a minimum number of concentrations to get robust rAUC calculations. rAUC will not be calculated on replicates with less points.

    - Once you have set the parameters you can click on 'Run' to analyze the images. Follow the log printed in the terminal to understand what is happening. At some point the pipeline asks the user to define the coordinates of the top-left and lower-right spots. To do so you have to click on them, and then hit 'Enter'. The folder `output_qCAST` will contain all the calculations.

## Extra comments

- Note that in this example we only used a subset of 5 images (to ease testing), which would be insufficient to get accurate measurements.

- You can also run the `main.py` in a non-interactive manner. To do so you should provide all the arguments (output folder, docker image ...) through the command line. Type `python3 main.py -h` (LINUX/MAC) to understand how to use this script. Note that, if you provide any argument it runs in a non-interactive manner.
