# doctorbox-covid-notify
A script that automatically checks doctorbox if a covid test result is available.

## Setup: ##

conda install selenium
conda install pillow

## How to use ##

Run the file with python and give it 5 arguments in the correct order.
The arguments are: 
* an email adress, that will be used to notify you when a result is available.
* testID Your individuel Identifikation number. It has 9 or 10 digits, input it without dots. Just digits. Incase of barcode with more than 10 digits: the last 10 digits.
* (Birthdate) The day of birth
* (Birthdate) The month of birth
* (Birthdate) The year of birth

### Example: ###

You're are born of 24 of december in 1990
Your test ID is 1337424242 
and you want to receive emails on: max@mustermann.de

python check.py max@mustermann.de 1337424242 24 12 1990


The script will run just the one time. It includes no functionality to check on a schedule. I suggest running it on a cronjob on a linux machine.

Create a script called run-covid-check.py with the content

```bash
#!/bin/sh

<path to your python3> <path to the check.py file>
```

then edit the crontab with 

```bash
crontab -e
```

and insert 

```bash
*/10 * * * * <path to run-covid-check.py> >> <path to a log file> 2>&1
```

into the crob table to run the script every 10 minutes.