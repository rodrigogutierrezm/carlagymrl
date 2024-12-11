#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

"""
Created on Mon Jul 17 2023
@author: Rodrigo Gutiérrez Moreno
"""

from gym import spaces

import carla

class Actions():

    def __init__(self, ego_vehicle = None):
        self.client = carla.Client("localhost", 2000)
        self.client.set_timeout(2.0)
        self.world = self.client.get_world()
        self.ego_vehicle = ego_vehicle

    def get_actions_space(self, n_actions = 2):
        action_space = spaces.Discrete(n_actions)
        
        return action_space

    def set_actions(self, action):        
        if action == 1:
            self.ego_vehicle.apply_control(carla.VehicleControl(throttle=0.6, steer=0, brake=0))
        elif action == 0:
            self.ego_vehicle.apply_control(carla.VehicleControl(throttle=0, steer=0, brake=1))