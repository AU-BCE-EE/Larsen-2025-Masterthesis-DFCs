### Importing Libraries ###
library(ALFAM2) # calling the library, same as a package-call in Python
#? alfam2 # documentation of the alfam2 function

### Change to DFC-specific function-parameters ####
pars_df <- read.csv(file.choose())# the csv-file is in the same folder as the script, the name is Pars_AUDFC
#head(pars_df)# prints the head of the df
#str(pars_df) # shows structure of df

pars_AUDFC <- setNames(pars_df$pp, pars_df$X)# collum header with names is empty, function defaluts to X
#row-wise mathcing of the paratmer-name in the 1st collum with the numercial value in the 2nd 
#print(pars_AUDFC)

### single scenarios ###
# un-acidified
#datU <- data.frame(ctime = 160, TAN.app = 62, app.mthd = 'bc',
#man.dm = 7.42, man.ph = 6.91, air.temp = 8.6, rain.cum = 0, app.rate.ni = 29)
#predU <- alfam2(datU, app.name = 'TAN.app', time.name = 'ctime', pars = pars_AUDFC)
#print(predU)

# H2SO4
#datH <- data.frame(ctime = 160, TAN.app = 62, app.mthd = 'bc',
#man.dm = 7.24, man.ph = 6.25, air.temp = 8.6, rain.cum = 0, app.rate.ni = 29)
#predH <- alfam2(datH, app.name = 'TAN.app', time.name = 'ctime', pars = pars_AUDFC)
#print(predH)

### Multiple scenarious, single call ###
# un-acidified, H2SO4, AA
datM <- data.frame(
scenario = 1:3,
ctime = 160, 
TAN.app = c(63, 63, 61), 
app.mthd = 'bc', 
air.temp = 8.6, 
rain.cum = 0, 
app.rate.ni = 29,
man.dm = c(7.42, 7.25, 7.23), 
man.ph = c(6.91, 6.25, 6.26)
)

#predM <- alfam2(datM, app.name = 'TAN.app', time.name = 'ctime', pars = pars_AUDFC, group = "scenario")
#print(predM)

### Adding hourly temperature-data ###
T_df <- read.csv(file.choose())# the csv-file is in the same folder as the script, the name is Pars_AUDFC
#head(T_df)# prints the head of the df, check whether the import is correct
#str(T_df) # shows structure of df, check wheter the import is correct

datT <- data.frame(
scenario = 1:3,
ctime = T_df$delta_t, 
air.temp = T_df$megrtp, 
app.mthd = 'bc',  
rain.cum = 0, 
app.rate.ni = 29,
TAN.app = c(63, 63, 61),
man.dm = c(7.42, 7.25, 7.23), 
man.ph = c(6.91, 6.25, 6.26)
)

predT <- alfam2(datT, app.name = 'TAN.app', time.name = 'ctime', pars = pars_AUDFC, group = "scenario")
print(predT)

plot(j ~ ctime, data = predT, type = 'S', col = 'red', 
     xlab = 'Time (h)', ylab = 'Average flux (kg/ha-h)')
points(jinst ~ ctime, data = predT, col = 'blue')

### importing predictor-variables, hourly basis ###
# Slurry chracteristics & weather data

### Documentation and clearing variables ###
packageVersion("ALFAM2") # call of the version, for documentation
args(alfam2) # which argumments where used for modeeling getting these results

### Other ###
# rm(list = ls())# clears already defined varibles in the console 
