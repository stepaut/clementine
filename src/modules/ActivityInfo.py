import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import ACTIVITIES_FILE, GROUPS_FILE

class ActivityInfo:
    def __init__(self):
        self.adf = pd.read_csv(ACTIVITIES_FILE)
        self.gdf = pd.read_csv(GROUPS_FILE)
        self.activitiesHash = self.adf['Activity'].to_dict()
        self.parseHash = {}

    def get_activity_color(self, activity_name: str, use_group_color: bool = False) -> str:
        try:
            activity = self._parse_activity(activity_name)
            if activity not in self.activitiesHash:
                return 'lightgray'

            activity_row = self.adf[self.adf['Activity'] == activity].values[0]

            if not use_group_color or activity_row['Group'] == "":
                return activity_row['Color']

            group_row = self.gdf[self.gdf['Group'] == activity_row['Group']].values[0]
            
            return group_row['Color']

        except Exception as e:
            print(f"Error getting activity color for {activity_name}: {e}")
            return 'lightgray'
    
    def _parse_activity(self, activity_name: str) -> str:
        if activity_name in self.parseHash:
            return self.parseHash[activity_name]

        activity_name = activity_name.replace("_", "").replace(" ", "").lower().strip()

        if ':' not in activity_name:
            self.parseHash[activity_name] = activity_name
            return activity_name

        arr = activity_name.split(':')
        activity = arr[-1].strip()
        self.parseHash[activity_name] = activity
        return self.parseHash[activity_name]




