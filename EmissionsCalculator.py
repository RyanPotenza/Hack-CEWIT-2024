import pandas as pd
from math import sin, cos, sqrt, atan2, radians

power_plants = pd.read_csv("global_power_plant_database.csv", header=0)
co2_emissions = {
    'Hydro': 4,
    'Solar': 45,
    'Gas': 450,
    'Other': 0,  # This is a placeholder, as "Other" is not specific
    'Oil': 890,
    'Wind': 11,
    'Nuclear': 12,
    'Coal': 1001,
    'Waste': 670,  # This is an estimate; actual emissions can vary
    'Biomass': 230,
    'Wave and Tidal': 17,  # This is an estimate; actual emissions can vary
    'Petcoke': 1025,  # This is an estimate; actual emissions can vary
    'Geothermal': 38,
    'Storage': 0,  # This depends on the source of the stored energy
    'Cogeneration': 0  # This is a placeholder, as emissions depend on the fuel used
} # kg CO2 per MWh

class EmissionsCalculator:
    def __init__(self, vehicle_type='Model 3'):
        self.vehicle_type = vehicle_type
        # Define the energy consumption in Wh/km for different vehicle types
        self.energy_consumption = {
            'Model 3': 139,  # Tesla Model 3: 139 Wh/km
            # Add other vehicle types here if needed
        }

    def haversine(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = 6371000 * c  # Radius of earth in meters
        return distance

    def is_within_distance(self, lat1, lon1, lat2, lon2, dist):
        """
        Check if a point at lat2, lon2 is within dist meters from lat1, lon1
        """
        distance = self.haversine(lat1, lon1, lat2, lon2)
        return distance <= dist

    def get_power_plant_emission(self, lat, lon, power_plants, co2_emissions):
        """
        Returns kgCO2 / m based on the location and nearby power plants
        """
        # Get power plants in a 20km radius
        power_plants_near = power_plants[power_plants.apply(lambda row: self.is_within_distance(lat, lon, row['latitude'], row['longitude'], 20000), axis=1)]

        # Get the fraction of each type of power plant based on primary_fuel and capacity_mw
        power_plant_type_fraction = power_plants_near.groupby('primary_fuel').sum()['capacity_mw'] / power_plants_near['capacity_mw'].sum()
        power_plant_type_emissions = (power_plant_type_fraction * pd.Series(co2_emissions)).sum()  # kg CO2 per MWh

        # Convert energy consumption to Wh/m and calculate emissions
        energy_consumption_wh_per_m = self.energy_consumption[self.vehicle_type] / 1000
        return power_plant_type_emissions * energy_consumption_wh_per_m * 1e-6  # kg CO2 / m
    
    def calculate_emissions(self, total_charge, loc):
        """
        Calculate the CO2 emissions for a given location
        """
        return self.get_power_plant_emission(loc['lat'], loc['lng'], power_plants, co2_emissions) * total_charge
