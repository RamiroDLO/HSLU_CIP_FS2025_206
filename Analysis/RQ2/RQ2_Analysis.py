import pandas as pd
import os
path_autoscout = "project_scraping_CIP_analysis_car_commodity_price/Data/Final Data/autoscout_cleaned.csv"
path_yahoo = "project_scraping_CIP_analysis_car_commodity_price/Data/Final Data/yahoo_spot_cleaned.csv"


df1 = pd.read_csv(path_autoscout)
df2 = pd.read_csv(path_yahoo)

print(df1, "\n" ,  df2)