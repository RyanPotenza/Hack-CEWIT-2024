import gym
from gym import spaces
from typing import Tuple, List, Dict
import numpy as np

from EVRoutePlanner import EVRoutePlanner

class EVChargingEnv(gym.Env):
    def __init__(self, api_key: str, start: Tuple[float, float], end: Tuple[float, float], vehicle_range: int):
        super(EVChargingEnv, self).__init__()
        
        # Initialize the EVRoutePlanner
        self.route_planner = EVRoutePlanner(api_key, start, end, vehicle_range)
        self.route_planner.calculate_route()
        self.current_node_index = 0
        self.current_node = self.route_planner.route[self.current_node_index]
        self.remaining_range = vehicle_range

        # Define action and observation space
        self.action_space = spaces.Discrete(2)  # 0: continue, 1: charge
        self.observation_space = spaces.Box(low=np.array([0, 0]), high=np.array([float('inf'), float('inf')]), dtype=np.float32)

    def reset(self):
        self.current_node_index = 0
        self.current_node = self.route_planner.route[self.current_node_index]
        self.remaining_range = self.route_planner.vehicle_range
        return self._get_obs()

    def step(self, action):
        done = False
        reward = 0

        if action == 1:  # Charge
            # Simulate charging
            self.remaining_range = self.route_planner.vehicle_range
            if 'nearest_ev_actual' in self.current_node:
                reward -= self.current_node['nearest_ev_actual'] / 1000

        # Move to the next node
        self.current_node_index += 1
        if self.current_node_index >= len(self.route_planner.route):
            done = True
        else:
            self.current_node = self.route_planner.route[self.current_node_index]
            self.remaining_range -= self.current_node['dist']

        if self.remaining_range < 0:
            done = True
            reward -= 100  # Penalize for running out of charge

        return self._get_obs(), reward, done, {}

    def _get_obs(self): # Get the observation
        return np.array([self.remaining_range, 'nearest_ev_actual' in self.current_node and self.current_node['nearest_ev_actual'] or 0])

    def render(self, mode='human'):
        pass  # Optional: Implement visualization