## Fitness and susceptibility measurements

Q-PHAST calculates different fitness and susceptibility measurements. First, our pipeline uses the time-vs-growth curve to infer fitness for each sample in each drug concentration (each spot in the experiment). Note that for one strain we may have multple samples (technical replicates). There are two types of fitness estimates:

  - Model-based fitness estimates: estimated by fitting a [generalised logistic model](http://en.wikipedia.org/wiki/Generalised_logistic_function#Generalised_logistic_differential_equation) to the time-vs-growth curve. The model parameters give us different fitness estimates. These estimates can be useful if we have some spots that did not reach stationary phase (to predict maximum growth, for example) or we have mixed samples with different growth times. These don't work well if we have slow-growing spots or non-logistic curves (which may happen because there is cell death after reaching stationary phase). `K`, `r`, `g`, `v`, `MDR`, `MDP`, `DT`, `AUC`, `MDRMDP`, `rsquare` (see below) are related to such model fitting.

  - Non parametric (or numeric) fitness estimates: these are calculated directly from the data, without assuming any underlying growth model. We generally use these (`nAUC` and `DT_h`) if we have experiments with the same growth times. `nAUC`, `nr`, `nr_t`, `maxslp`, `maxslp_t`, `DT_h`, `nSTP` and `DT_h_goodR2` (see below) are non-parametric measurements.

These are the relevant fitness estimates (check the [qfa manual](http://qfa.r-forge.r-project.org/docs/qfa-manual.pdf) for more information):

- `K`, `r`, `g` and `v` are the parameters of a generalised logistic model that is fit to the data. `K` (maximum predicted growth) and `r` (predicted growth rate) are fitness estimates that may be used.

- `MDR` (Maximum Doubling Rate), `MDP` (Maximum Doubling Potential), `DT` (Doubling Time estimated from the model fit at t=0), `AUC` (Area Under the growth-vs-fitness fit Curve) and `MDRMDP` (Addinall et al. style fitness) are several fitness estimates calculated from the model fit.

- `rsquare` is the [coefficient of determination](https://en.wikipedia.org/wiki/Coefficient_of_determination) between the model fit and the data. You can use it to determine which curves have a good model fit (i.e. rsquare > 0.95).

- `nr` is a numerical estimate of intrinsic growth rate. It is estimated by fitting smoothing function to log of data, calculating numerical slope estimate across range of data and selecting the maximum estimate (should occur during exponential phase). `nr_t` is the time at which `nr` occurs, so that is an estimator of the lag phase time.

- `maxslp` is a numerical estimate of maximum slope of growth curve, and `maxslp_t` is the time at which this maximum slope of observations occurs. `maxslp_t` is a way to calculate the lag phase.

- `nAUC` is the numerical Area Under Curve. This is a model-free fitness estimate, directly calculated from the data, measuring the AUC of the time-vs-growth curve between t=0 and t=hours_experiment (24h by default). This is our preferred fitness esimate.

- `nSTP` is the numerical Single-Timepoint growth estimate, calculated at t=hours_experiment (24h by default). 

- `DT_h` is a numerical estimate for the maximum doubling time, in hours. `DT_h_goodR2` is the same value but only for those spots with a good model fit (rsquare>0.95). For poorly fit curves the `DT_h_goodR2` is set to 25.0 (very high). This `DT_h_goodR2` can be used to have as non-growing the samples with weird curves.

Once all fitness estimates are measured, Q-PHAST calculates the relative fitness (i.e. `nAUC_rel`, `r_rel` or `nSTP_rel`) for each spot by dividing the raw fitness by the fitness at concentration==0. This is only performed if a plate with concentration==0 is provided. These relative fitness measurements are essential to perform the susceptibility analysis. 

Finally, for drugs with at least two non-0 concentrations, Q-PHAST measures the following susceptibility estimates (considering either `K_rel`, `r_rel`, `nr_rel`, `maxslp_rel`, `MDP_rel`, `MDR_rel`, `MDRMDP_rel`, `AUC_rel`, `nAUC_rel` or `nSTP_rel`):

- `MIC`: The Minimum Inhibitory Concentration 

- `rAUC`:

- `SMG`:

## Q-PHAST outputs

This pipeline generates the following files / folders under the output directory:

### Integrated susceptibility measurements

Three excel files generated including integrated, per-strain fitness and susceptibiity measurements: 

- `fitness_measurements_simple.xlsx`: This contains the raw fitness values



WORKING HERE!!!!!!!!!




It only considers valid replicates (there are enough data points and concentartion==0 is growing). Each row corresponds to one drug and strain. These are the columns:

- `median_MIC50` is the median MIC50 across replicates.

- `mode_MIC50` is the mode MIC50 across replicates.

- `range_MIC50`is the range of observed MIC50 across replicates.

- `replicates_MIC50` is the number of replicates used for MIC calculations.

- `median_rAUC` is the median rAUC across replicates.

- `mode_rAUC` is the mode rAUC across replicates.

- `range_rAUC`is the range of observed rAUC across replicates.

- `replicates_rAUC` is the number of replicates used for rAUC calculations.







## susceptibility_measurements.tab

A file with the susceptibility measurements for each strain. These are the columns:

- `drug`, `strain`, `row` and `column` indicate the assayed strain (and position) and drug.

- `replicateID` indicates the replicate as `r<row>c<column>`, which is useful to access one same sample across different plates. Derived from this there is the `sampleID` field, which includes `<strain>_<replicateID>`.

- `fitness_estimate` indicates, for each row, which is the fitness estimate in which the MIC and rAUC values (see below) were calcualted. This table includes several ABSOLUTE estimates (`K`, `r`, `nr`, `maxslp`, `MDP`, `MDR`, `MDRMDP`, `DT`, `AUC`, `DT_h`, `nAUC` and `DT_h_goodR2`) and their corresponding RELATIVE estimates (`K_rel`, `r_rel`, `nr_rel`, `maxslp_rel`, `MDP_rel`, `MDR_rel`, `MDRMDP_rel`, `DT_rel`, `AUC_rel`, `DT_h_rel`, `nAUC_rel` and `DT_h_goodR2_rel`)

- `MIC_*` is, for a given fitness_estimate, the minimum concentration at which you have an inhibition of at least 0.25, 0.5, 0.75 or 0.90 as compared to the concentration==0. Note that this is only meaningful (in terms of drug susceptibility) for RELATIVE fitness estimates (those that are called like `*_rel`), where the fitness values are normalised to the `concentration`==0.

- `rAUC_concentration` is the Area Under the concentration vs fitness Curve, divided by a 'maximum AUC' (where fitness==1 across all concentrations). Again, this is mostly meaningful for for RELATIVE fitness estimates (those that are called like `*_rel`), where the fitness values are normalised to the `concentration`==0. For those, it should be a value between 0 and 1.

- `rAUC_log2_concentration` is similar to `rAUC_concentration`, but with the `log2_concentration` instead of `concentration`. As drug concentrations follow mostly a logarithmic range it can happen that the highest concentrations dominate the `rAUC_concentration` values. `rAUC_log2_concentration` gives more importance to all the concentartion range, and it is the one that we used in the C. glabrata paper of antifungal drug resistance.

- `fitness_conc0` is the fitness at  `concentration`==0. It is only meaningful for ABSOLUTE fitness estimates (those that are NOT called like `*_rel`).

- `conc0_is_growing` indicates whether this sample is growing (it has an nAUC>=0.5) at concentration==0. If this is false you should not consider this susceptibility estimate.

## susceptibility_measurements_simple.xlsx

This is a table with integrated (and simplified) susceptibility calculations. It only considers valid replicates (there are enough data points and concentartion==0 is growing). Each row corresponds to one drug and strain. These are the columns:

- `median_MIC50` is the median MIC50 across replicates.

- `mode_MIC50` is the mode MIC50 across replicates.

- `range_MIC50`is the range of observed MIC50 across replicates.

- `replicates_MIC50` is the number of replicates used for MIC calculations.

- `median_rAUC` is the median rAUC across replicates.

- `mode_rAUC` is the mode rAUC across replicates.

- `range_rAUC`is the range of observed rAUC across replicates.

- `replicates_rAUC` is the number of replicates used for rAUC calculations.





### relative_fitness_measurements_simple.xlsx

### susceptibility_measurements_simple.xlsx

### summary_plots

### Extened outputs 

## Important notes





The module generates the following files and folders under the output directory:

## growth_curves

This is a folder containing plots of the time-vs-growth curves for each spot. It can be useful check that the experiment went well.

## growth_measurements_all_timepoints.tab

This is a table with the growth calculations for each spot in all timepoints. It has the following columns:

- `plate_batch`, `plate`, `row` and `column` indicate the spot.

- `strain`, `drug`, `concentration` and `bad_spot` indicate the metadata provided in the plate layout table.

- `Growth` has the inferred cell density.

- `Inoc.Time` is the innoculation time in YYYY-MM-DD_HH-MM-SS

- `Date.Time` is the timepoint in YYYY-MM-DD_HH-MM-SS, and `Expt.Time` in days.

- `Timeseries.order`is the categorical timepoint.

- `XOffset`and	`YOffset` are the coordinates of the spot.

- The remaining fields (i.e. `Area` or `redMean`) are related to the growth inference, interesting for developing purposes.

## fitness_measurements.tab

A table with the fitness estimates for each spot. It has the following columns:

- `plate_batch`, `plate`, `row`, `column`, `spotID` indicate the spot.

- `strain`, `drug`, `concentration` and `bad_spot` indicate the metadata provided in the plate layout table.

- `replicateID` indicates the replicate as `r<row>c<column>`, which is useful to access one same sample across different plates. Derived from this there is the `sampleID` field, which includes `<strain>_<replicateID>`.


- `K_rel`,	`r_rel`, `nr_rel`,	`maxslp_rel`,	`MDP_rel`,	`MDR_rel`	`MDRMDP_rel`,	`DT_rel`,	`AUC_rel`,	`DT_h_rel`,	`nAUC_rel`,	`DT_h_goodR2_rel` are the relative fitness estimates. We calculate them by dividing the fitness estimate in a given spot by the value at concentration==0. This is essential to get susceptibility measurements.



- `is_growing` is a boolean that indicates whether the spot is growing, which is necessary for the calculation of rAUC. Spots are considered to be growing if `nAUC` is above `min_nAUC_to_beConsideredGrowing` (default to 0.5, but it can be personalized with --min_nAUC_to_beConsideredGrowing 0.5, for example).


## drug_vs_fitness

A folder with plots showing the relationship between the drug concentration and fitness. There is one plot for each drug and fitness estimate.
