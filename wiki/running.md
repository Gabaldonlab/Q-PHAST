# Running

To illustrate how you can run this method we will use an example experiment in which we measured antifungal susceptibility to anidulafungin (ANI) in 24 strains and 8 drug concentrations (one of them is 0). The images and input files can be found [here](https://github.com/Gabaldonlab/qCAST/tree/main/testing/testing_subset), and you may check them to understand how to design the input files. You may follow these steps to get the calculations (this would work in LINUX for the image `mikischikora/qcast:v0.1`):

## 1-Design the plate layout

Follow these steps before doing the experiment:

- Create an excel table with the 24 strains to be measured (called `strains.xlsx` in the example). This may contain empty wells (named 'H2O') or wells with a pool of strains that will grow in all assayed conditions (named 'Pool'). Make sure that there are no spaces in the strain names.

- Create an excel table with the drugs (column 'drug') and concentrations (column 'concentration') to be assayed (called `drugs.xlsx` in the example). The drugs table should also contain two extra columns:

    - The 'plate_batch' column should be a unique identifier for each batch of plates that will be run in a single scanner.

    - The 'plate' column should be a number between '1' and '4' indicating which plate in the batch has a given drug and concentration. The [experimental protocol]() shows how to set the 'plate' number.

- Open the terminal and move into the folder where you have the `main.py` script with `cd <type path here>` (for example `cd /home/mschikora/Desktop/qCAST` is the path in my computer). To know the path of your folder you can use the 'Properties' menu. Once you are in the desired folder you can launch our interactive app by typing `python3 main.py`. To get the plate layout you should follow these steps:

    - Click on the appropiate Operating System, docker image, the 'plate_layout' module and the output folder (where all files will be saved).

    - Provide the `strains.xlsx` and `drugs.xlsx` files. Click on 'Run module' to get the plate layout.

    - This generates a folder (`output_get_plate_layout`) that contains two useful excel tables: `plate_layout.xlsx` has a visual representation of how you should position the strains in each plate and `plate_layout_long.xlsx` is a long table that is required to further analyze the data.

## 2-Run the experiment

Run the experiment to obtain images for each plate setting the strains as in `output_get_plate_layout/plate_layout.xlsx` (see [experimental protocol]()). Save them into a folder (called `raw_images` in the example) containing one subfolder for each batch of plates (corresponding to the column 'plate_batch' from `drugs.xslx`). The filename of image should have a timestamp with a 'YYYYMMDD_HHMM' format (i.e. `20210814_0011.tif`, `_0_20210814_0011.tif` or `2021_08_14_00_11.tif`). Make sure that the plates are positioned well in the quadrants of the image.

## 3-Analyze the images

Follow these steps to get the antifungal susceptibility measurements:

- Optional: If you want to ignore some spots in the susceptibility measurements (i.e. because you see contamination) you can 'red-flag' them with the 'bad_spot' column from `output_get_plate_layout/plate_layout_long.xlsx`. By default, the 'bad_spot' column is set to 'F' (false) for all spots, but you can change the value to 'T' (true) for spots that you want to ignore. Any spots marked as 'bad spots' (with 'bad_spot'=='T') will not be considered in the susceptibility measurements. If ther 'concentration==0' spot is marked as 'bad_spot' all the others should also be marked as bad spots, or there will be an error.

- Get the antifungal susceptibility measurements by running the interactive app (with `python3 main.py`) and following these steps:

    - Click on the appropiate Operating System, docker image, the 'analyze_images' module and the output folder (where all files will be saved).

    - Provide the plate layout file (`output_get_plate_layout/plate_layout_long.xlsx`) and the raw images folder (`raw_images`). Click on 'Run module' to save this information and continue to the next step.

    - Optional: The last interactive window is necessary to tune the parameters of the susceptibility measurements. This is the meaning of the parameters:

      - Keep temporary files: Set to 'Yes' if you want to save all the temporary files. This is only recommended for debugging.

      - pseudocount concentration: This is a float that is added to concentrations to get rAUC measurements where the X axis is log2(concentration). We set a default of 0.1, which may be tuned depending on the concentration range.

      - min nAUC growing: This is a float that indicates the minimum nAUC required to consider that a spot is growing. This is added in the 'is_growing' field. Note that, for the simplified susceptibility measurements (saved into the `susceptibility_measurements_simple.tab` file ), only replicates where the concentration==0 is growing will be considered.
      
      - min concentrations rAUC: This is an integer that indicates the minimum number of concentrations required to calculate rAUC. Note that, when using the 'bad_spot' field, you may get some concentration-vs-growth curves with few points (resulting in poor rAUC calculations). This parameter allows you to set a minimum number of concentrations to get robust rAUC calculations. rAUC will not be calculated on replicates with less points.

    - Once you have set the parameters you can click on 'Run module' to analyze the images. Follow the log printed in the terminal to understand what is happening. The folder `output_analyze_images` will contain all the calculations.

## Extra comments

- Note that the syntax to execute the script `main.py` is slightly different for each OS. You should execute (in the terminal):

  - In LINUX and MAC: `python3 main.py`
  - In WINDOWS: `py main.py`

- If you are running on Windows you also need to run the XLauch application (with all default parameters) BEFORE running this pipeline.

- Note that in this example we only used a subset of 5 images (to ease testing), which would be insufficient to get accurate measurements.

- You can also run the `main.py` in a non-interactive manner. To do so you should provide all the arguments (output folder, docker image ...) through the command line. Type `python3 main.py -h` to understand how to use this script. Note that, if you provide any argument it runs in a non-interactive manner.

- The `main.py` requires the Tkinter python library, which is usually installed with python. If this is not true, you will get an import error when running the script. You can install Tkinter like [this](https://www.geeksforgeeks.org/how-to-install-tkinter-in-windows/) or [this](https://www.tutorialspoint.com/how-to-install-tkinter-in-python).
