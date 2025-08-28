# template-data
A template for a GitHub repository for sharing data. 
Use the sections below to document your repo.
Summarize your data here, e.g.,:

Data on a cat breath experiment carried out in 2036.
Three house cats were fed three different meals in a randomized order and the foulness of their breath was assessed by a panel of three volunteers (humans).

# Maintainer
Your name here.
Contact information here: <https://au.dk/YOUR_ID_HERE@bce>.

# References
Add any papers or other references here.
Include links like this: `[display text](https://www.theurl.com)` or just `<https://www.theurl.com>`.
Omit the backtick quotes of course: [display text](https://www.theurl.com) or just <https://www.theurl.com>.

# Description of directories and files
## `data`
Directory contains data files as comma-separated text files.
Use CSV files if at all possible.

* `cats.csv` age and weight of the experimental subjects
* `breath.csv` breath scores from the experiment

## `others`
If you include other directories, describe them like this.

# Variables
Variables should be described here or in a separate file.
It may be necessary to have separate lists for the different data files.

* `cat_key` unique integer key for each experimental subject
* `breath_score` "breath foulness" index as median of three panelists
* ...

# License
You do not need a license section in the README.md file (you can remove this section) but you should look through the available GitHub licenses and pick a suitable one to include in a LICENSE file in your repo.
CC-BY-4.0 is a good choice for data (some details here: <https://choosealicense.com/licenses/cc-by-4.0/> and <https://choosealicense.com/non-software/>).
