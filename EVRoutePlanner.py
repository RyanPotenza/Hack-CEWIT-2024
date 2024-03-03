from typing import List, Dict, Any, Tuple
from geopy.distance import geodesic

from GoogleClients import GoogleMapsClient, GooglePlacesClient
from PathInterpolator import PathInterpolator
from EmissionsCalculator import EmissionsCalculator

import torch
import torch.nn as nn

import random

from torch.utils.data import DataLoader, TensorDataset
from gym import spaces
import gym

import torch.optim as optim
class EVRouteGymEnv(gym.Env):
    def __init__(self, ev_route_planner):
        super(EVRouteGymEnv, self).__init__()
        self.ev_route_planner = ev_route_planner
        self.action_space = spaces.Discrete(2)  # 0 = continue, 1 = charge
        self.observation_space = spaces.Box(low=0, high=float('inf'), shape=(2,), dtype=float)
        self.current_node_index = 0
        self.remaining_range = ev_route_planner.vehicle_range

    def reset(self):
        self.nodes = self.ev_route_planner.calculate_route('regular')
        print(self.nodes)
        self.current_node_index = 0
        self.remaining_range = self.ev_route_planner.vehicle_range
        return self._get_obs()

    def step(self, action):
        done = False
        reward = 0

        if self.current_node_index >= len(self.nodes): # Check if the episode is over
            done = True
            return self._get_obs(), reward, done, 'branched' in self.nodes[self.current_node_index-1]
        


        if action == 1:  # Charge
            if 'nearest_ev_station_distance' in self.nodes[self.current_node_index] and \
               self.remaining_range >= self.nodes[self.current_node_index]['nearest_ev_station_distance']:
                # Assuming charging restores the EV's range to its maximum capacity
                self.remaining_range = self.ev_route_planner.vehicle_range
                # Move to charging station if not at the current node's location
                self.remaining_range -= self.nodes[self.current_node_index].get('nearest_ev_station_distance', 0)
            else:
                # If charging is not possible due to range issues, heavily penalize the action
                reward = self._calculate_reward(action, False)
        elif action == 0:  # Continue
            if self.current_node_index < len(self.nodes) - 1:
                self.remaining_range -= self.nodes[self.current_node_index + 1]['dist']
                # self.current_node_index += 1
                reward = self._calculate_reward(action, True)
            else:
                done = True
                reward = self._calculate_reward(action, True)

        # Check if the EV can no longer move due to insufficient range, ending the episode
        if self.remaining_range < 0:
            done = True
            reward = self._calculate_reward(action, False)

        if not done:
            self.current_node_index += 1

        return self._get_obs(), reward, done, 'branched' in self.nodes[self.current_node_index-1]


    def _get_obs(self):
        # branched = 'branched' in self.nodes[self.current_node_index]
        if self.current_node_index < len(self.nodes):
            node = self.nodes[self.current_node_index]

            return [self.remaining_range, 'nearest_ev_station_distance' in node and node['nearest_ev_station_distance'] or 7777777]
        else:
            return [0, 0]

    def _can_charge(self):
        # Implement logic to check if the current node has a charging station and is within range
        current_node = self.nodes[self.current_node_index]
        return 'nearest_ev_station' in current_node and self.remaining_range >= current_node['nearest_ev_station_distance']

    def _calculate_reward(self, action, successful):
        # Reward logic considering the action's success and its implications
        if action == 1:  # Charge
            if successful:
                # Negative reward for charging to reflect time spent, but less penalty if it was necessary
                return -5  # Example penalty value, adjust based on needs
            else:
                # Heavy penalty if charging was attempted but is not possible
                return -100  # Example penalty value, adjust based on needs
        elif action == 0:  # Continue
            if successful:
                # Positive reward for successfully moving to the next node without unnecessary charging
                return 10  # Example reward value, adjust based on needs
            else:
                # Penalize running out of range
                return -100  # Example penalty value, adjust based on needs


    
class EVDecisionNetwork(nn.Module):
    def __init__(self):
        super(EVDecisionNetwork, self).__init__()
        self.fc1 = nn.Linear(2, 64)  # 2 input features: remaining range and nearest station range
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 2)  # 2 output classes: 0 = don't branch, 1 = branch

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)  # Output raw scores for each class
        return x
    
def traindata(env):
    training_data = []
    for episode in range(5):
        state = env.reset()
        for step in range(10):
            action = random.choice([0, 1])  # Randomly choose to continue or charge
            next_state, reward, done, branched = env.step(action)

            # Record the state, action, and whether the action resulted in branching
            training_data.append((state, action, int(branched)))

            state = next_state
            if done:
                break
    # Extract inputs and labels
    inputs = torch.tensor([data[0] for data in training_data]).float()  # Convert to float for NN processing
    labels = torch.tensor([data[1] for data in training_data]).long()  # Convert to long because these are categorical labels

    # Create a TensorDataset and DataLoader
    train_dataset = TensorDataset(inputs, labels)
    train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True)

    return training_data,train_loader

def train(model,train_loader):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    # Step 3: Training Loop
    num_epochs = 1000  # Number of epochs to train for

    for epoch in range(num_epochs):
        for inputs, labels in train_loader:
            # Zero the parameter gradients
            optimizer.zero_grad()
        
            # Forward pass
            outputs = model(inputs)
        
            # Compute loss
            loss = criterion(outputs, labels)
        
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
    
        # Optionally print the loss every x epochs
        if epoch % 1 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

    print("Training complete.")


class EVRoutePlanner:
    def __init__(self, api_key: str, start: Tuple[float, float], end: Tuple[float, float], vehicle_range, vehicle_efficiency):
        """
        Initializes the EVRoutePlanner with start, end locations, and the EV's range.

        :param api_key: API key for accessing Google Maps and Places APIs.
        :param start: Start location as a tuple (latitude, longitude).
        :param end: End location as a tuple (latitude, longitude).
        :param vehicle_range: The EV's range on a full charge in meters.
        """
        self.vehicle_efficiency = vehicle_efficiency
        self.vehicle_range = vehicle_range*1E3

        self.maps_client = GoogleMapsClient(api_key)
        self.places_client = GooglePlacesClient(api_key)
        self.paths_interpolator = PathInterpolator(api_key,30000)
        self.emissions_calculator = EmissionsCalculator(vehicle_efficiency)
        self.start = start
        self.end = end
        self.route = []
        self.total_distance = 0

        self.gym_env = EVRouteGymEnv(self)
        self.model = EVDecisionNetwork()

        self.emissions_kg_co2 = 0

        self.charging_stations = []

        self.all_stations = []

    def calculate_route(self,type='regular') -> List[dict]:
        """
        Calculates the route, including necessary charging stops based on the EV's range.

        :return: A list of route segments, including charging stops.
        """

        if type == "ai":
            training_data,train_loader = traindata(self.gym_env)

            train(self.model,train_loader)

            current_location = self.start
            keepGoing = True
            while keepGoing:
                # try:
                # route_segment = self.maps_client.get_route(current_location, self.end)
                path = self.paths_interpolator.get_points_at_intervals(current_location, self.end)

                nodes = self.path_to_nodes(path)

                # self.end = (nodes[-1]['lat'], nodes[-1]['lng'])
                for i, node in enumerate(nodes):
                    if self.model(torch.tensor([self.vehicle_range, 'nearest_ev_station_distance' in node and node['nearest_ev_station_distance'] or 7777777]).float()).argmax().item() == 1:
                        charging_station_route = node['nearest_ev_route_segment']

                        # We must add the route nodes to the route list
                        newNodes = []
                        for step in charging_station_route['steps']:
                            newNodes.append({
                                'lat': step['start_location']['lat'],
                                'lng': step['start_location']['lng'],
                                'dist': step['distance']['value']
                            })
                            # self.total_distance += step['distance']['value']
                        #make the last node a 'branched'
                        newNodes[0]['branched'] = True
                        print("setting to branch")
                        self.route.extend(newNodes)

                        # Calculate the amount of CO2 emissions 
                        self.emissions_kg_co2 += self.emissions_calculator.calculate_emissions(self.total_distance, node)   
                        print("Total Distance: ", self.total_distance)
                        print("Added emissions: ", self.emissions_kg_co2)

                        # Reset the distance 
                        self.total_distance = 0

                        # Add the charging station to the charging stations list
                        self.charging_stations.append({
                            'lat': charging_station_route['end_location']['lat'],
                            'lng': charging_station_route['end_location']['lng']
                        })

                        # Recalculate route from charging station to end
                        current_location = (charging_station_route['steps'][-1]['end_location']['lat'], charging_station_route['steps'][-1]['end_location']['lng'])
                        break
                    else:
                        self.route.append(node)
                        self.total_distance += node['dist']
                        if i == len(nodes) - 1:
                            # Add emissions for the last segment
                            self.emissions_kg_co2 += self.emissions_calculator.calculate_emissions(self.total_distance, node)
                            # current_location = self.end
                            keepGoing = False
                # except Exception as e:
                #     print(f"Error calculating route: {e}")
                #     break
            return self.route




        else:
            current_location = self.start
            keepGoing = True
            while keepGoing:
                # try:
                # route_segment = self.maps_client.get_route(current_location, self.end)
                path = self.paths_interpolator.get_points_at_intervals(current_location, self.end)

                nodes = self.path_to_nodes(path)

                # self.end = (nodes[-1]['lat'], nodes[-1]['lng'])
                for i, node in enumerate(nodes):
                    print(f"Processing node {i + 1} of {len(nodes)}")
                    if self._requires_charge(node, nodes, i):
                        print("needs charge")
                        charging_station_route = node['nearest_ev_route_segment']

                        # We must add the route nodes to the route list
                        newNodes = []
                        for step in charging_station_route['steps']:
                            newNodes.append({
                                'lat': step['start_location']['lat'],
                                'lng': step['start_location']['lng'],
                                'dist': step['distance']['value']
                            })
                            # self.total_distance += step['distance']['value']
                        #make the last node a 'branched'
                        newNodes[0]['branched'] = True
                        print("setting to branch")
                        self.route.extend(newNodes)

                        # Calculate the amount of CO2 emissions 
                        self.emissions_kg_co2 += self.emissions_calculator.calculate_emissions(self.total_distance, node)   
                        print("Total Distance: ", self.total_distance)
                        print("Added emissions: ", self.emissions_kg_co2)

                        # Reset the distance 
                        self.total_distance = 0

                        # Add the charging station to the charging stations list
                        self.charging_stations.append({
                            'lat': charging_station_route['end_location']['lat'],
                            'lng': charging_station_route['end_location']['lng']
                        })

                        # Recalculate route from charging station to end
                        current_location = (charging_station_route['steps'][-1]['end_location']['lat'], charging_station_route['steps'][-1]['end_location']['lng'])
                        break
                    else:
                        self.route.append(node)
                        self.total_distance += node['dist']
                        if i == len(nodes) - 1:
                            # Add emissions for the last segment
                            self.emissions_kg_co2 += self.emissions_calculator.calculate_emissions(self.total_distance, node)
                            # current_location = self.end
                            keepGoing = False
                # except Exception as e:
                #     print(f"Error calculating route: {e}")
                #     break
            return self.route
        
        
    
    def _requires_charge(self, current_node, nodes, current_node_i) -> bool:
        """
        Determines if charging is required based on the EV's current range,
        the distance to the next node, and the distance from the next node to the nearest charging station.

        :param current_node: The current node in the route.
        :param nodes: List of all nodes
        :param current_node_i: The index of the current node in the list of nodes
        :return: True if charging is required before reaching the next node, False otherwise.
        """

        if not nodes:
            return False
        if 'nearest_ev_station_distance' in current_node:
            currentDist = self.total_distance
            while current_node_i < len(nodes):
                currentDist += nodes[current_node_i]['dist']
                if 'nearest_ev_station_distance' in nodes[current_node_i]:
                    currentDist += nodes[current_node_i]['nearest_ev_station_distance']
                    # print(f"Nearest station distance: {nodes[current_node_i]['nearest_ev_station_distance']}")
                    print(f"Current distance: {currentDist}")
                    return currentDist > self.vehicle_range
                current_node_i += 1
            return False

    def path_to_nodes(self, path) -> List[dict]:
        """
        Converts a route segment to a list of nodes, where each node represents a step in the route
        with its start location (latitude and longitude) and distance.

        :param route_segment: Segment of the route as returned by the Google Maps API.
        :return: A list of nodes, each containing latitude, longitude, and distance.
        """
        nodes = []
        # Iterate through each step in the route segment
        for step in path:
            dist = 0
            if not (step == path[-1]):
                # Calculate the distance between the current and next step
                dist = geodesic(step, path[path.index(step) + 1]).meters
                # print(dist)

            node = {
                'lat': step[0],
                'lng': step[1],
                'dist': dist
            }
            # Calculate the distance to the nearest EV charging station
            nearest_station = self.places_client.find_nearby_charging_stations((node['lat'], node['lng']))[0]#['geometry']['location']

            if nearest_station:
                nearest_station_route = self.maps_client.get_route((node['lat'], node['lng']), (nearest_station['geometry']['location']['lat'], nearest_station['geometry']['location']['lng']))['legs'][0]
                nearest_station_distance = nearest_station_route['distance']['value']

                node['nearest_ev_station'] = nearest_station
                node['nearest_ev_station_distance'] = nearest_station_distance
                node['nearest_ev_route_segment'] = nearest_station_route


            nodes.append(node)
        return nodes
    
    