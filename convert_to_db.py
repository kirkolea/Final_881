import os
import pandas as pd
import sqlite3

DB_NAME = "wearable_data.db"
DATA_DIR = "Wearable_Dataset"

COLUMN_MAP = {
    'acc': ['x', 'y', 'z'],
    'bvp': ['value'],
    'eda': ['value'],
    'hr': ['bpm'],
    'temp': ['celsius'],
    'ibi': ['time', 'interval']
}

def transferToSQL():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        
    conn = sqlite3.connect(DB_NAME)
    
    path = os.path.join(DATA_DIR, 'subject-info.csv')
    if os.path.exists(path):
        pd.read_csv(path).to_sql('subjects', conn, index=False)
        print("Loaded subject-info.csv")

    activities = ['AEROBIC', 'ANAEROBIC', 'STRESS']
    
    for activity in activities:
        activityPath = os.path.join(DATA_DIR, activity)
        
        for subject in os.listdir(activityPath):
            subj_path = os.path.join(activityPath, subject)
            
            for csv_file in os.listdir(subj_path):
                if csv_file.endswith('.csv') and csv_file != 'tags.csv':
                    metric_name = csv_file.replace('.csv', '').lower()
                    file_path = os.path.join(subj_path, csv_file)
                    
                    cols = COLUMN_MAP.get(metric_name)
                    
                    df = pd.read_csv(file_path, skiprows=2, names=cols)
                    
                    df['subject_id'] = subject
                    df['activity'] = activity
                    
                    df.to_sql(metric_name, conn, if_exists='append', index=False)
            

    conn.close()

if __name__ == "__main__":
    transferToSQL()