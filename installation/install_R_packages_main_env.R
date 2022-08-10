#!/usr/bin/env Rscript

# install non-conda R packages in the main_env
install.packages("https://cran.r-project.org/src/contrib/Archive/optparse/optparse_1.6.6.tar.gz", repos=NULL, type="source") # version 1.6.6 
install.packages("https://download.r-forge.r-project.org/src/contrib/qfa_0.0-45.tar.gz", repos=NULL, type="source") # version 0.0-45