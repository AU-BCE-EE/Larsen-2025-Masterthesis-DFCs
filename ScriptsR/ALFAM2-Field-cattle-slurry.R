### Importing Libraries ###
library(ALFAM2) # calling the library, same as a package-call in Python
#?alfam2 # documentation of the alfam2 function

### Change to DFC-specific function-parameters ####
pars_df <- read.csv(file.choose())# the csv-file is in the same folder as the script, the name is Pars_AUDFC
#head(pars_df)# prints the head of the df
#str(pars_df) # shows structure of df

pars_AUDFC <- setNames(pars_df$pp, pars_df$X)# collum header with names is empty, function defaluts to X
#row-wise mathcing of the paratmer-name in the 1st collum with the numercial value in the 2nd 
#print(pars_AUDFC)

### Importing hourly temperature-data ###
T_df <- read.csv(file.choose())# the csv-file is in the same folder as the script, the name is Pars_AUDFC
#head(T_df)# prints the head of the df, check whether the import is correct
#str(T_df) # shows structure of df, check wheter the import is correct

### Simulating, plot-level ###
# implementing time-delay aka temperature difference
T_df$time <- as.POSIXct(T_df$DATE_TIME)# convert time-data into an R time-object
T_df$time_shifted <- T_df$time - 10 * 60 # slight shift of the temperature-time
# alligns 1st temperature-point with temperature-start
#print(T_df$time_shifted)

# interpolate temperature func
get_temp <- function(wanted_time) {
  approx(
x = as.numeric(T_df$time_shifted),
y = T_df$megrtp,
xout = as.numeric(wanted_time),
rule = 2
  )$y
}

# as.numeric(T_df$time_shifted): shifted timestamps for known temperature-data, as a value instead of a date-time object
# T_df$time_shifted: shifted time-line: knwon temperature data 
# as.numeric(wanted_time): the timestamp for which to aproximate a temperature
# $y: ensures the function only returns the y-value, instead of a vector of T and related t
# rule = 2 : if interpolating outside of bounds (at the final points), simply apply the nearest known value

### table of slurry-data for each treatment & time-delay for specific plots ###
plot_scens <- data.frame(
  scenario = 1:9,
  
  treatment = c("AA", "H2SO4", "RAW",
                "H2SO4", "RAW", "AA",
                "RAW", "AA", "H2SO4"),
  
  shift = c(0.00, 0.27, 0.53,
            0.67, 0.80, 0.93,
            1.07, 1.33, 1.47),
  
  TAN.app = c(62, 62.5, 63,
              62.5, 63, 63,
              63, 62, 62.5),
  
  man.dm = c(7.23, 7.25, 7.42,
             7.25, 7.42, 7.23,
             7.42, 7.23, 7.25),
  
  man.ph = c(6.26, 6.25 ,6.91,
             6.25, 6.91, 6.26,
             6.91, 6.26, 6.25)
)
  
### Combine slurry, shift and temperature-data to create a full dataset of each hour ###
n_time <- nrow(T_df) # grap amount of rows to create based on avalable time data

dat_all <- do.call(rbind, lapply(1:nrow(plot_scens), function(i) {
# create a looping mechanism for each scenario i: lapply(1:nrow(plot_scens)
# constuct a datatable for each
# combine all created datatables: do.call(rbind, ...)
# create each table based on variables defined bellow

  
  shift <- plot_scens$shift[i] # grab the shift of each plot-scen
   
  time_vec <- T_df$time_shifted + shift * 3600 # [h] to [s] - create the plot-specific time-axis based the complete plot-specific time axis and the plotspecific shift
  
  temp_vec <- get_temp(time_vec) # interpolate plot-specific temperature using the pre-built function
  
  data.frame(
    scenario = plot_scens$scenario[i], # extract constants for scenario i
    treatment = plot_scens$treatment[i],
    
    ctime = T_df$delta_t,
    air.temp = temp_vec,
    
    TAN.app = plot_scens$TAN.app[i],
    man.dm  = plot_scens$man.dm[i],
    man.ph  = plot_scens$man.ph[i],
    
    app.mthd = "ts",
    rain.cum = 0,
    app.rate.ni = 29
  )
}))

#subset(dat_all, scenario == 5)[1:10,]

# apply the alfam2-function on all data #

pred_all <- alfam2(
  dat_all,
  app.name = "TAN.app",
  time.name = "ctime",
  pars = pars_AUDFC,
  group = "scenario"
)

### Quick tests of restult ###

# final accumulated relative emissions of each scenario/plot #
final_rel <- tapply(pred_all$er, pred_all$scenario, tail, 1)

final_rel * 100

final_df <- data.frame(
  scenario = names(final_rel),
  rel_emission_pct = final_rel * 100
)

print(final_df)

# Check of inputs for each scenario #
input_check <- dat_all[!duplicated(dat_all$scenario),
                      c("scenario","treatment","TAN.app","man.dm","man.ph")]

#print(input_check)

# Check the shifted temperature #
#subset(dat_all, ctime == 0)[, c("scenario","air.temp")]


### Prepare reuslts for csv-file ###
# combine input df and result df
result_df <- cbind(dat_all, pred_all[, c("j", "er")])

# aditionaly add the time-shift of each scenario/plot
result_df <- merge(result_df, plot_scens[, c("scenario","shift")], by = "scenario")

head(result_df)# check the headers of combined df

### Export results as csv-file ###
folder <- "C:/Users/mikae/Desktop/Github - speciale/Larsen-2025-Masterthesis-DFCs/output/ALFAM2/Alfam2-model-results"
#write.csv(result_df, file.path(folder, "2026-05-05-alfam2_Cattle-ts.csv"), row.names = FALSE)

### Documentation and clearing variables ###
#packageVersion("ALFAM2") # call of the version, for documentation
#args(alfam2) # which argumments where used for modeeling getting these results

### Other ###
# rm(list = ls())# clears already defined varibles in the console 
