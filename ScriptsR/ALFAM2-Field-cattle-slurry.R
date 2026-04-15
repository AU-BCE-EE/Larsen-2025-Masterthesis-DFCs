### Import ALFAM2 library ###
library(ALFAM2) # calling the library, same as a package in PYT
#?alfam2 # open the function help file

### Importing data ###
# weather data
# specific alfam2 parameters, fitted only to DFC's

### single scenario tests of function, only final ###
# data for unacidified slurry
# default parameters
dat1_none <- data.frame(ctime = 160, TAN.app = 62,app.mthd = 'bc', 
man.dm = 7.42, man.ph = 6.91, air.temp = 8.1)

pred1_none <- alfam2(dat1_none, app.name = 'TAN.app', time.name = 'ctime')
print(pred1_none)

# data for slurry acidified with AA
dat1_A = dat1_none <- data.frame(ctime = 160, TAN.app = 62,app.mthd = 'bc',
man.dm = 7.23,man.ph = 6.26, air.temp = 8.1)

pred1_A <- alfam2(dat1_A, app.name = 'TAN.app', time.name = 'ctime')
print(pred1_A)

# data for slurry acidified with H2SO4
dat1_H = dat1_none <- data.frame(ctime = 160, TAN.app = 62,app.mthd = 'bc',
man.dm = 7.23,man.ph = 6.25, air.temp = 8.1)

pred1_H <- alfam2(dat1_H, app.name = 'TAN.app', time.name = 'ctime')
print(pred1_H)


### setting function variables ####


### Final documentation ###
packageVersion("ALFAM2") # call of the version, for documentation
args(alfam2) # which argumments where used for modeeling getting these results