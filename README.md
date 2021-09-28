# optionchain_visualization

Run this script on EOD after 6 p.m. so all data gets updated on nse website
Optionchain data of previous working day can't be accessed on next working day so do run it every working day

It stores the data downloaded in the folder named

"Today's date"+-data folder

Eg - 2021-04-02-data

For future reference you can save data or delete the folder with "-data" 

And visualized png in stored in output folder, within stock specific folder
The png is named as

29-Apr-2021-oi-2021-04-02.png

Where 29-Apr-2021 is expiry date.

And 2021-04-02 is data of formation of png file for reference

# Pip  modules 

```sh

pip3 install -r requirments.txt

```
