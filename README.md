# Predicting_bike_distribution


03 / 08 / 2021

* KNN having bikes_changes_past45 makes it less accurate - probably because datapoints that are neighbours insofar as they are similar in their changes in the past 45 minutes are not necessarly similar in the future fullness change of their respective stations

02 / 08 / 2021

* reason accuracy was so high is because of the following:

X[0:MAX_TIME, 139:247]= fullness_in10
X[0:MAX_TIME, 247:355]= fullness_in30
X[0:MAX_TIME, 355:463]= fullness_in60

which should have been

X[0:MAX_TIME, 139:247]= bikes_changes_past5
X[0:MAX_TIME, 247:355]= bikes_changes_past15
X[0:MAX_TIME, 355:463]= bikes_changes_past45

01 / 08 / 2021

* Retrospectively, avoiding pandas probably made my life harder
* Big brain moment: going to represent the time of day as an x and y value, where a 24hr day is a circle. This way 15:00 and 16:00 are as similar to each other as 23:00 and 00:00

31 / 07 / 2021

* 1st model seems solid. Going to try a KNRegressor for the 2nd. Neighbours for a given time to predict will be the bike_fullness of that same station at that same prediction time at previous dates when the day_of_week was the same. Closer (and greater weighted) neighbours will be those where the bike_occupancy of the given station is more similar at the current time.
* Yep, so there is more to a knn when x and y aren't 1 dimensional. Trying to mentally conceive how a nearest neighbour is calculated when there are multiple features in X.

30 / 07 / 2021

* ~= 0.99938 accuracy 😳 Something must be wrong

29 / 07 / 2021

* Data from 27 / 1 / 2020 onwards is solid
* hindsight is 20,20; data processing feeling more streamlined. just got to exclude gaps in data now
* the edge cases of the block_xminchange arrays still have issues, but will sort those after the model is fit
* going to take a gamble and instead of rooting out what poor data is between 27 / 1 and 1 / 4 I am going to change the DUD_VALUE to 0 and train the model

28 / 07 / 2021

* Start-edge bikes_changes_pastx issue looking better
    bikes_changes_pastx completely ironed out in processor effective way
* Looks like it could just be exclusing poor days of data that is left in the feature data generation

27 / 07 / 2021

* There are so many kinks to iron out in the data and how I am processing it - it's starting to feel like I am writing code into a blackhole and that the ways I am structuring the data are arbitrary and redundant
An example of such a kink that I have just ironed out is changing
self.day_of_week= (STARTING_DAY + int(epoch_time / DATAPOINTS_PER_DAY ) % len(DAYS_OF_WEEK))
to
self.day_of_week= (STARTING_DAY + int(epoch_time / (DATAPOINTS_PER_DAY - 1)) % len(DAYS_OF_WEEK))
Although perhaps I have learned something here and not just applied a patchwork solution insofar as I imagine if there is a length of an array, I should universaly divide by the length of the array - 1
* .ipynb often unviewable. Perhaps I should export a .py before every commit
* Checklist at this point seems to be:
Fix problem with start-edge bikes_changes_pastx
Find way to exclude days with insufficent data
Fix hour_of_day

26 / 07 / 2021

* Some values in bikes_changes_past45 are greater than 100 - something must be wrong
* 3d confusion matrix could be used to gauge results: e.g. negative change in bikes, no change, and positive. Perhaps a better way to visualise though

25 / 07 / 2021

* 5, 15, and 45 minutes seem to be more appropriate time spans to look at previous bike station fullness changes in
* I want to change OPEN_HOURS to 18 but the data processing system ain't ready yet

24 / 07 / 2021

* For purposes of MLPreg approach, DataDay information is now as sparse arrays. This is causing graphs to look funny though
* I suspect long logs from print statements causing trouble for j notebook and github
* I need to make a change to the code in the .ipynb file so that the logs from the cells change
* There are many holes in 'fullness' due to gaps in the data. Since features for a given time are dependent on there being data before it, I will only generate sets of training features where there has been data in all stations for the past hour and where there is data in all stations for the coming hour

23 / 07 / 2021

* Might try an MLPRegressor approach, with input nodes being:
the 7 days of the week +
the 18 active hours of the day +
the fullness of the 117 stations +
changes in capacity for the 117 stations in the past 10, 30, and 60 minutes,
where the 7 are either 1 or 0 (it is that day or it's not),
the 18 are from 0 to 1 (eg if it's half 6 when 6 and 7 are 0.5)
and the 351 (117 * 3) are from 0 to N

22 / 07 / 2021

* There's a bug when you set INPUT_ROWS_LIMIT a good bit over 1,000,000
* Feature brainstorm: Getting rainfall data; lat & long where bikes leave, and then assuming they'll turn up at a distance in some time; increase / decrease in bikes at a station rather than bikes at a station; overall ratio of bikes that are out of stations vs bikes that are in stations
* yep, there are certain days that are just missing but that shouldn't matter
* TODO: in graphing cell, empty days that are having a colour allocated to them mean there are colours being wasted

21 / 07 / 2021

* TODO: Sort station_var values by epoch_time
* Not popping missing stations from arrays anymore because that leads to station ids not being usable as indices for these arrays

20 / 07 / 2021

* Assuming for now I should train on data for all bike stations but test on select ones
* Removing INPUT_ROWS_LIMIT can crash jupyter notebook
* Some days in the 1st Jan to 24th Feb 2020 range the dataset is supposed to cover are simply absent. The order of rows is unclear, often with various patches of records covering a few hours of a stations status.
* Only reading in these station_id= []; date= []; time= []; available_bikes= []; because non-variable info can be associated to a single object
* Going to ignore "STATUS" because none of the stations are anything but "Open" in the dataset. Going to ignore "AVAILABLE BIKE STANDS" because this is probably redundant for my ends when I have "AVAILABLE BIKES"
* Apparently there is no station where id = 1