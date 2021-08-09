#!/usr/bin/env python
# coding: utf-8

# In[59]:


# IMPORTS & DEFINITIONS

import csv, sys
import datetime
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np; np.set_printoptions(threshold=sys.maxsize)
from sklearn.neural_network import MLPRegressor
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsRegressor
import math
from sklearn.model_selection import cross_val_score
from sklearn import linear_model
from sklearn.metrics import r2_score
from sklearn.preprocessing import PolynomialFeatures

DUD_VALUE= 0 # change from 0 to something like 123 for debugging
EMPTY_DATA_DAY_VAL= 123456789
TOTAL_ROWS= 9999999999
INPUT_ROWS_LIMIT= TOTAL_ROWS # 500000
FILENAME= 'dublinbikes_2020_Q1.csv'
MAX_STATION_ID= 117
SECS_IN_5MIN= 300
DATAPOINT_EVERYX_MIN= 5
DATAPOINTS_PER_DAY= 288
DAYS_OF_WEEK= ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] # yes, I consider Monday to be the '0'/start of the week
STARTING_DATE= 0 # aka Monday. Because the 27th of Jan 2020 is a Monday
MISSING_STATIONS= [117, 116, 70, 60, 46, 35, 20, 14, 1, 0]
NUM_STATIONS= MAX_STATION_ID - len(MISSING_STATIONS)
SUBSTANDARD_DAYS= [] # [50, 49]
TOTAL_DAYS= 66 # from 27 / 1 / 2020 to (and including) 1 / 4 / 2020
HOURS= 24
EPOCH= datetime.datetime(2020, 1, 27, 0, 0)
TOTAL_TIME_DATAPOINTS= int((datetime.datetime(2020,4,2,0,0) - EPOCH).total_seconds() / SECS_IN_5MIN)
K= 5
STEP_SIZE= 0.02185 # just the magic number that leads to 288 values being generated
R= 0.5
MAX_HINDSIGHT= 60 # minutes

class DataDay: # ideally this would be nested in the Station class
    def __init__(self, index):
        self.index= index
        self.substandard_day= False
        if index in SUBSTANDARD_DAYS:
            self.substandard_day= True
        self.times_populated= 0
        self.day_of_week= ((STARTING_DATE + index) % len(DAYS_OF_WEEK))
        
        self.daily_epoch_time= np.full(DATAPOINTS_PER_DAY, EMPTY_DATA_DAY_VAL, dtype=np.int)
        self.epoch_time= np.full(DATAPOINTS_PER_DAY, EMPTY_DATA_DAY_VAL, dtype=np.int)
        self.bikes= np.full(DATAPOINTS_PER_DAY, EMPTY_DATA_DAY_VAL, dtype=np.int)
        self.percent_bikes= np.full(DATAPOINTS_PER_DAY, float(EMPTY_DATA_DAY_VAL), dtype=np.float)

    def populate(self, daily_epoch_time, epoch_time, bikes, percent_bikes):
        if self.substandard_day == False:
            self.daily_epoch_time[daily_epoch_time]= daily_epoch_time
            self.epoch_time[daily_epoch_time]= epoch_time
            self.bikes[daily_epoch_time]= bikes
            self.percent_bikes[daily_epoch_time]= percent_bikes
            self.times_populated+= 1

class Station:
    def __init__(self, index):
        self.index= index
        self.name= DUD_VALUE
        self.bike_capacity= DUD_VALUE
        self.address= DUD_VALUE
        self.latitude= DUD_VALUE
        self.longitude= DUD_VALUE
        self.data_days= [DataDay(i) for i in range(0, TOTAL_DAYS)]
    
    def populate_consts(self, name, bike_capacity, address, latitude, longitude):
        self.name= name
        self.bike_capacity= bike_capacity
        self.address= address
        self.latitude= latitude
        self.longitude= longitude

def get_station_id(name):
    try:
        index= [x.name for x in stations].index(name)
    except ValueError:
        index= -1
    return index


# In[2]:


# DATA STRUCTURING

total_capacity= 0 # not in use currently
index= []; daily_epoch_time= []; epoch_time= []; percent_bikes= [];
stations= [Station(i) for i in range(0, MAX_STATION_ID + 1)] # + 1 so as to include MAX_STATION_ID in the range. Even though there is no station 0 or 1, I include them so that station indices are also array indices
indices_to_populate= list(range(0, MAX_STATION_ID + 1))
for index in MISSING_STATIONS:
    indices_to_populate.remove(index)

with open(FILENAME, newline='') as f:
    reader = csv.reader(f); next(reader) # skip data header
    current_index= 0
    try:
        while len(indices_to_populate) != 0:
            row= next(reader)
            if int(row[0]) == current_index: # this clause is just for performance
                continue
            current_index= int(row[0])
            if current_index in indices_to_populate:
                stations[current_index].populate_consts(row[3], row[4], row[8], row[9], row[10])
                indices_to_populate.remove(current_index)
                total_capacity+= int(row[4])
        
        f.seek(0)
        reader= csv.reader(f); row= next(reader) # skip data header
        for row_i, row in enumerate(reader):
            if row_i >= INPUT_ROWS_LIMIT:
                break
            if int((datetime.datetime(int(row[1][0:4]), int(row[1][5:7]), int(row[1][8:10]), int(row[1][11: 13]), int(row[1][14: 16])) - EPOCH).total_seconds()) < 0:
                continue
            try:
                epoch_time= int((datetime.datetime(int(row[1][0:4]), int(row[1][5:7]), int(row[1][8:10]), int(row[1][11: 13]), int(row[1][14: 16])) - EPOCH).total_seconds() / SECS_IN_5MIN)
                stations[int(row[0])].data_days[int(epoch_time / DATAPOINTS_PER_DAY)].populate(                     int((datetime.datetime(int(row[1][0:4]), int(row[1][5:7]), int(row[1][8:10]), int(row[1][11: 13]), int(row[1][14: 16])) - datetime.datetime(int(row[1][0:4]), int(row[1][5:7]), int(row[1][8:10]), 0, 0)).total_seconds() / (SECS_IN_5MIN)),                     epoch_time,                     int(row[6]),                     float("{:.3f}".format(float(row[6]) / float(row[4]))))
            except IndexError as e:
                print("\nTRIED: ", epoch_time, ' / ', DATAPOINTS_PER_DAY, ' = ', int(epoch_time / DATAPOINTS_PER_DAY))
                print(row[1])
    except csv.Error as e:
        sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))


# In[3]:



            
for station_i, station in enumerate(stations):
    last_bikes= 0
    last_percent_bikes= 0
    for day_i, data_day in enumerate(station.data_days):
        for val_i, val in enumerate(data_day.bikes):
            if val == EMPTY_DATA_DAY_VAL:
                stations[station_i].data_days[day_i].populate(val_i, day_i * DATAPOINTS_PER_DAY + val_i, last_bikes, last_percent_bikes)
            else:
                last_bikes= data_day.bikes[val_i]
                last_percent_bikes= data_day.percent_bikes[val_i]


# In[ ]:


# FEATURE DATA PREPERATION

fullness= np.full((TOTAL_TIME_DATAPOINTS, MAX_STATION_ID - len(MISSING_STATIONS)), DUD_VALUE, dtype=np.int)
fullness_in10= np.full((TOTAL_TIME_DATAPOINTS, MAX_STATION_ID - len(MISSING_STATIONS)), DUD_VALUE, dtype=np.int)
fullness_in30= np.full((TOTAL_TIME_DATAPOINTS, MAX_STATION_ID - len(MISSING_STATIONS)), DUD_VALUE, dtype=np.int)
fullness_in60= np.full((TOTAL_TIME_DATAPOINTS, MAX_STATION_ID - len(MISSING_STATIONS)), DUD_VALUE, dtype=np.int)
fullness_percent= np.full((TOTAL_TIME_DATAPOINTS, MAX_STATION_ID - len(MISSING_STATIONS)), DUD_VALUE, dtype=np.float)
bikes_changes_pastx= np.full((TOTAL_TIME_DATAPOINTS, MAX_STATION_ID - len(MISSING_STATIONS), int(MAX_HINDSIGHT / DATAPOINT_EVERYX_MIN)), DUD_VALUE, dtype=np.int)
day_of_week= np.full((TOTAL_TIME_DATAPOINTS, len(DAYS_OF_WEEK)), DUD_VALUE, dtype=np.int)
hour_of_day= np.full((TOTAL_TIME_DATAPOINTS, HOURS), DUD_VALUE, dtype=np.float)

station_index_decrement= 1 # this is a varying offset for the indexing of stations that accounts for missing stations that are being ignored
for epoch_day_i in range(TOTAL_DAYS):
    #print("########### epoch_day_i: ", epoch_day_i)
    x_offset= epoch_day_i * DATAPOINTS_PER_DAY
    y_offset= 0
    
    block= np.zeros((DATAPOINTS_PER_DAY, HOURS), dtype=np.float)
    daily_epoch_time= list(range(DATAPOINTS_PER_DAY))
    for time_i in daily_epoch_time:
        hour= float("{:.3f}".format(time_i / 12)) # divide by 12 because there are 12 datapoints in an hour
        block[time_i][(int(hour) + 1) % HOURS]= hour % 1
        block[time_i][int(hour)]= 1 - (hour % 1)
    hour_of_day[x_offset:x_offset + block.shape[0], y_offset:y_offset + block.shape[1]]= block
    
    day= stations[2].data_days[epoch_day_i].day_of_week
    block= np.zeros((DATAPOINTS_PER_DAY, len(DAYS_OF_WEEK)), dtype=np.int)
    for block_i, sub_arr in enumerate(block):
        block[block_i][day]= 1
    day_of_week[x_offset:x_offset + block.shape[0], y_offset:y_offset + block.shape[1]]= block
    
    for station in stations:
        #print("###### station.index: ", station.index)
        if station.index == 1:
            station_index_decrement= 1
        if station.index in MISSING_STATIONS:
            station_index_decrement+= 1
            continue
        y_offset= station.index - station_index_decrement
        
        block= station.data_days[epoch_day_i].percent_bikes
        block= np.reshape(block, (DATAPOINTS_PER_DAY, 1))
        fullness_percent[x_offset:x_offset + block.shape[0], y_offset:y_offset + block.shape[1]]= block
        
        block= station.data_days[epoch_day_i].bikes
        block= np.reshape(block, (DATAPOINTS_PER_DAY, 1))
        fullness[x_offset:x_offset + block.shape[0], y_offset:y_offset + block.shape[1]]= block
        
        bikes= station.data_days[epoch_day_i].bikes
        block= np.reshape(bikes[2:], (bikes.shape[0] - 2, 1))
        fullness_in10[x_offset:x_offset + block.shape[0], y_offset:y_offset + block.shape[1]]= block
        block= np.reshape(bikes[6:], (bikes.shape[0] - 6, 1))
        fullness_in30[x_offset:x_offset + block.shape[0], y_offset:y_offset + block.shape[1]]= block
        block= np.reshape(bikes[12:], (bikes.shape[0] - 12, 1))
        fullness_in60[x_offset:x_offset + block.shape[0], y_offset:y_offset + block.shape[1]]= block
        
        block= np.reshape(station.data_days[epoch_day_i].bikes, (DATAPOINTS_PER_DAY, 1))
        if epoch_day_i - 1 == -1:
            prev_block= np.zeros((DATAPOINTS_PER_DAY, 1), dtype=np.int)
        else:
            prev_block= np.reshape(station.data_days[epoch_day_i - 1].bikes, (DATAPOINTS_PER_DAY, 1))
        block_xminchange= np.zeros((DATAPOINTS_PER_DAY, int(MAX_HINDSIGHT / DATAPOINT_EVERYX_MIN)), dtype=np.int)
        fullness_xago= np.zeros((DATAPOINTS_PER_DAY, int(MAX_HINDSIGHT / DATAPOINT_EVERYX_MIN)), dtype=np.int)
        for col_i in range(fullness_xago.shape[1]):
            i= col_i + 1
            fullness_xago[i:DATAPOINTS_PER_DAY, col_i:col_i + 1]= block[0:DATAPOINTS_PER_DAY - i, 0:1]
            fullness_xago[0:i, col_i:col_i + 1]= prev_block[DATAPOINTS_PER_DAY - i:DATAPOINTS_PER_DAY, 0:1]
        for col_i in range(fullness_xago.shape[1]):
            block_xminchange[0:DATAPOINTS_PER_DAY, col_i:col_i + 1]= np.subtract(block, fullness_xago[0:DATAPOINTS_PER_DAY, col_i:col_i + 1])
        
        bikes_changes_pastx[x_offset:x_offset + block_xminchange.shape[0], y_offset:y_offset + 1, 0:block_xminchange.shape[1]]= np.reshape(block_xminchange, (DATAPOINTS_PER_DAY, 1, block_xminchange.shape[1]))


# In[80]:


# APPROACH DEFINITIONS

def run_baseline(station_name):
    index= get_station_id(station_name)
    X= np.full((TOTAL_TIME_DATAPOINTS, 1), 0, dtype=np.int)
    y= np.full(TOTAL_TIME_DATAPOINTS, 0, dtype=np.int)
    X[0:TOTAL_TIME_DATAPOINTS, 0:1]= fullness[0:TOTAL_TIME_DATAPOINTS, index:index + 1]
    y[0:TOTAL_TIME_DATAPOINTS]= np.arange(0, TOTAL_TIME_DATAPOINTS, dtype=np.int)
    
    polynomial_features= PolynomialFeatures(degree= 3)
    poly_X= polynomial_features.fit_transform(X, y)
    X_train, X_test, y_train, y_test= train_test_split(poly_X, y, test_size= 0.2, shuffle= False)
    regr= linear_model.LinearRegression().fit(X_train, y_train)
    
    y_pred= regr.predict(X_test)
    print("R**2 accuracy: ", r2_score(y_test, y_pred) * 100, " %")
    
def run_approach1(station_name):
    index= get_station_id(station_name)
    
    y= np.full((TOTAL_TIME_DATAPOINTS, 3), 0, dtype=np.int) # change the 3 to a 6 to do both stations at once on the generalised-training form of an approach
    y[0:TOTAL_TIME_DATAPOINTS, 0:1]= np.reshape(fullness_in10[:,index], (TOTAL_TIME_DATAPOINTS, 1))
    y[0:TOTAL_TIME_DATAPOINTS, 1:2]= np.reshape(fullness_in30[:,index], (TOTAL_TIME_DATAPOINTS, 1))
    y[0:TOTAL_TIME_DATAPOINTS, 2:3]= np.reshape(fullness_in60[:,index], (TOTAL_TIME_DATAPOINTS, 1))

    X= np.full((TOTAL_TIME_DATAPOINTS, hour_of_day.shape[1] + day_of_week.shape[1] + 3                 + 0 * NUM_STATIONS                ), 0, dtype=np.float)
    X[0:TOTAL_TIME_DATAPOINTS, 0:7]= day_of_week
    X[0:TOTAL_TIME_DATAPOINTS, 7:31]= hour_of_day
    X[0:TOTAL_TIME_DATAPOINTS, 31:32]= fullness_percent[0:TOTAL_TIME_DATAPOINTS, index:index + 1]
    X[0:TOTAL_TIME_DATAPOINTS, 32:33]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, index:index + 1, 0:1]), (TOTAL_TIME_DATAPOINTS, 1)) # past5
    X[0:TOTAL_TIME_DATAPOINTS, 33:34]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, index:index + 1, 1:2]), (TOTAL_TIME_DATAPOINTS, 1)) # past10
    #X[0:TOTAL_TIME_DATAPOINTS, 34:35]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, index:index+1, 2:3]), (TOTAL_TIME_DATAPOINTS, 1)) # past15
    #X[0:TOTAL_TIME_DATAPOINTS, 35:36]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, index:index+1, 3:4]), (TOTAL_TIME_DATAPOINTS, 1)) # past20
    #X[0:TOTAL_TIME_DATAPOINTS, 36:37]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, index:index+1, 4:5]), (TOTAL_TIME_DATAPOINTS, 1)) # past25
    # X[0:TOTAL_TIME_DATAPOINTS, 139:247]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, 0:NUM_STATIONS, 0:1]), (TOTAL_TIME_DATAPOINTS, 1)) # past5
    # X[0:TOTAL_TIME_DATAPOINTS, 247:355]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, 0:NUM_STATIONS, 2:3]), (TOTAL_TIME_DATAPOINTS, 1)) # past15
    # X[0:TOTAL_TIME_DATAPOINTS, 355:463]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, 0:NUM_STATIONS, 8:9]), (TOTAL_TIME_DATAPOINTS, 1)) # past45

    kf= KFold(n_splits= K)
    kf.get_n_splits(X)
    score_sum= 0.0
    i= 1
    for train_index, test_index in kf.split(X):
        X_train, X_test= X[train_index], X[test_index]
        y_train, y_test= y[train_index], y[test_index]
        regr= MLPRegressor(random_state= 1, max_iter= 1000, alpha=0.001).fit(X_train, y_train)
        y_pred= regr.predict(X_test)
        score_sum+= regr.score(X_test, y_test)
        print("R**2 accuracy of data split", i, ": ", regr.score(X_test, y_test) * 100, " %")
        i+= 1
    print("\nAVERAGE R**2 evaluation: ", (score_sum / K) * 100, " %")
    
def run_approach2(station_name):
    index= get_station_id(station_name)
    
    y= np.full((TOTAL_TIME_DATAPOINTS, 3), 0, dtype=np.int) # change the 3 to a 6 to do both stations at once on the generalised-training form of an approach
    y[0:TOTAL_TIME_DATAPOINTS, 0:1]= np.reshape(fullness_in10[:,index], (TOTAL_TIME_DATAPOINTS, 1))
    y[0:TOTAL_TIME_DATAPOINTS, 1:2]= np.reshape(fullness_in30[:,index], (TOTAL_TIME_DATAPOINTS, 1))
    y[0:TOTAL_TIME_DATAPOINTS, 2:3]= np.reshape(fullness_in60[:,index], (TOTAL_TIME_DATAPOINTS, 1))
    
    X= np.full((TOTAL_TIME_DATAPOINTS, 2 + 2             #* bikes_changes_pastx.shape[1] \ # This line is uncommented when training on all stations
           ), -1, dtype=np.float)
    
    positions= []; t= 0
    while t < 2 * math.pi:
        positions.append((1 - (R * math.cos(t) + R), R * math.sin(t) + R))
        t+= STEP_SIZE
    pos_i= 0
    for time_i in range(TOTAL_TIME_DATAPOINTS):
        X[time_i, 0]= positions[pos_i][0]
        X[time_i, 1]= positions[pos_i][1]
        pos_i= (pos_i + 1) % len(positions)
    
    X[0:TOTAL_TIME_DATAPOINTS, 2:3]= fullness_percent[0:TOTAL_TIME_DATAPOINTS, index:index+1]
    X[0:TOTAL_TIME_DATAPOINTS, 3:4]= np.reshape((bikes_changes_pastx[0:TOTAL_TIME_DATAPOINTS, index:index+1, 0:1]), (TOTAL_TIME_DATAPOINTS, 1)) # past5
    # X[0:TOTAL_TIME_DATAPOINTS, 2:110]= bikes_changes_past5
    # X[0:TOTAL_TIME_DATAPOINTS, 110:218]= bikes_changes_past15
    
    neigh= KNeighborsRegressor(n_neighbors= 30, weights='distance')
    cv_scores= cross_val_score(neigh, X, y, cv=5)
    print(cv_scores) # print each cv score (accuracy) and average them
    print('cv_scores mean:{}'.format(np.mean(cv_scores)))


# In[79]:


# DRIVER

run_baseline("PORTOBELLO ROAD")
print("--------------------")
#run_baseline("CUSTOM HOUSE QUAY")


# In[ ]:




