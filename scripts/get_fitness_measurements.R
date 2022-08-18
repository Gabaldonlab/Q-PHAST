#!/usr/bin/env Rscript

# This script is used to generate qfa plots given a directory where you have the qfa data. It should be run in main_env

# load packages
library(qfa)

# define functions

get_rsquare_fromRow = function(row, df, model="logreg"){
  
  # Takes a row of the fit df and the data_colonyzer df. It returns the rsquare between the real data and the generated from the model specified
  
  # define the position
  row_row = gsub(" ", "", row["Row"])
  row_column = gsub(" ", "", row["Column"])
  
  # get the raw data of the corresponding row and column 
  df = df[(df$Row==row_row) & (df$Column==row_column) & (df$Barcode==row["Barcode"]),]
  df = df[order(df$Expt.Time),]
  if (nrow(df)==0) { print(row); throw("is wrong")}
  
  # get data
  x = df$Expt.Time
  y = df$Growth
  
  # get the predicted data
  if (model=="logreg") { 
    
    # this is refered in https://mran.microsoft.com/snapshot/2014-09-08_1746/web/packages/qfa/vignettes/qfa.pdf
    
    # get parms
    K = as.numeric(row["K"]) # carrying capacity (maxiumum Y) --> implies that the lower asymptote is 0 and the shape is 1
    r = as.numeric(row["r"]) # rate (growth rate)
    g = as.numeric(row["g"]) # initial growth
    
    # get predicted values
    y_pred = K / (1 + (-1 + (K/g))*exp(-r*x))
  }
  
  # return the r2
  return(cor(y, y_pred, method="pearson")^2)
  
}

numerical_r_log2=function(obsdat,span=0.3,nBrute=1000,cDiffDelta=0.0001,mlab=""){
  
  # Generate numerical (model-free) estimate for nr_t intrinsic growth rate. This is a modi
  tims=obsdat$Expt.Time
  gdat=obsdat$Growth
  tmax=max(tims)
  
  # Smooth data, find slope as function of time and nr_t slope
  lgdat=log2(gdat)
  ltims=tims[!is.na(lgdat)]
  lgdat=lgdat[!is.na(lgdat)]
  la=NA
  
  # debug returning 
  try(a<-loapproxfun(tims,gdat,span=span),silent=TRUE)
  try(la<-loapproxfun(ltims,lgdat,span=span),silent=TRUE)
  problem=list(nr=0,nr_t=NA,mslp=0,mslp_t=NA)
  if(!exists("a")) return(problem)
  if(!is.function(a)) return(problem)
  if(!is.function(la)) return(problem)
  
  # calculate
  centralDiff=function(f,delta) return(function(x) (f(x+delta/2.0)-f(x-delta/2.0))/delta)
  lslp=centralDiff(la,cDiffDelta)
  slp=centralDiff(a,cDiffDelta)
  # Brute force optimization
  stimes=seq(min(ltims),max(ltims),length.out=nBrute)
  vals=a(stimes)
  slps=slp(stimes)
  lvals=la(stimes)
  lslps=lslp(stimes)
  # Discard points too close to t=0 to avoid artificially high slopes
  opt=which.max(slps)
  lopt=which.max(lslps)
  res=list(nr=lslps[lopt],nr_t=stimes[lopt],mslp=slps[opt],mslp_t=stimes[opt])
  maxslope=res$nr
  
  return(res)
}


get_minDoublingTime = function(row, df, max_dt){
  
  # Takes a row of the fit df and the data_colonyzer df. It returns the minimum doubling time in hours
  
  # define the position
  row_row = gsub(" ", "", row["Row"])
  row_column = gsub(" ", "", row["Column"])
  
  # get the raw data of the corresponding row and column 
  df = df[(df$Row==row_row) & (df$Column==row_column) & (df$Barcode==row["Barcode"]),]
  df = df[order(df$Expt.Time),]
  if (nrow(df)==0) { print(row); throw("is wrong")}

  # get the numerical_r estimates
  nr_df = numerical_r_log2(df) # This has nr, which is a numerical estimate of where the slope of a log2 transformed data is highest. This is the inverse of the maxiumum instantaneous DT
  
  # get the doubling time and debug
  dt_h = ((1/nr_df$nr)*24)
  if (dt_h>max_dt){dt_h = max_dt}
  
  return(dt_h)
}

# define paths
input_dir = commandArgs(trailingOnly = TRUE)[1]
#input_dir = "/home/mschikora/samba/imageAnalysis_fitness/test/output/output_greenlab_lc"

dat_file = paste(input_dir, "all_images_data.dat", sep="/")
expt_file = paste(input_dir, "ExptDescription.txt", sep="/")
lib_file = paste(input_dir, "LibraryDescriptions.txt", sep="/")
orf_to_gene = paste(input_dir, "ORF2GENE.txt", sep="/")
output_plots = paste(input_dir, "output_plots.pdf", sep="/")

# read colonyzer
data_colonyzer = colonyzer.read(files=c(dat_file), experiment=expt_file, libraries=lib_file, ORF2gene=orf_to_gene, screenID="")

# define what you have as growth. This is a surrogate of cell density, scaled to have all positive values

#data_colonyzer$Growth=data_colonyzer$Area

# get growth
data_colonyzer$Growth = scale(data_colonyzer$Trimmed/(data_colonyzer$Tile.Dimensions.X*data_colonyzer$Tile.Dimensions.Y*255))
#data_colonyzer$Growth = data_colonyzer$Trimmed/(data_colonyzer$Tile.Dimensions.X*data_colonyzer$Tile.Dimensions.Y*255)

# scale so that the minimum value is >0
data_colonyzer$Growth = data_colonyzer$Growth + abs(min(data_colonyzer$Growth)) + 0.1

# normalize so that the maximum is 1
data_colonyzer$Growth = data_colonyzer$Growth/max(data_colonyzer$Growth)

# define the inocguess, which is the initial value for growth, which can be the median of all the growth parameters in the first timepoint
inocguess = median(data_colonyzer[data_colonyzer$Timeseries.order==1,]$Growth)

# define the threshold in Growth under which you will say that it is noise
threshold = min(data_colonyzer$Growth)-0.1

# perform logistic regression
fit = qfa.fit(data_colonyzer,inocguess=inocguess,ORF2gene=orf_to_gene,fixG=FALSE,detectThresh=threshold, AUCLim=4,STP=4,glog=FALSE, globalOpt=FALSE, nrate=TRUE, checkSlow=TRUE)
fit = makeFitness(fit)

# add the rsquared of the fit
fit$rsquare = apply(fit, 1, function(r) get_rsquare_fromRow(r, data_colonyzer))

# add the maximum predicted doubling time
max_dt = max(fit$DT)
fit$DT_h = apply(fit, 1, function(r) get_minDoublingTime(r, data_colonyzer, max_dt))

# make the plots
qfa.plot(output_plots,fit,data_colonyzer,maxt=2)

# write the dfs
write.table(data_colonyzer, paste(input_dir, "processed_all_data.tbl", sep="/"),sep="\t",quote=FALSE,row.names=FALSE,col.names=TRUE)
write.table(fit,paste(input_dir, "logRegression_fits.tbl", sep="/"),sep="\t",quote=FALSE,row.names=FALSE,col.names=TRUE)


