#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

"""
Created on Mon Jul 17 2023
@author: Rodrigo Gutiérrez Moreno
"""

import time, math

class Reward():

    def __init__(self, ego_vehicle = None):
        self.success = 0
        self.collision = 0
        self.ego_vehicle = ego_vehicle

    def reset_reward(self):
        self.time_reset = time.time()

    def get_reward(self, info):      
        if info['episode'] == 'Finished: suceed.':
            self.success = 1
        elif info['episode'] == 'Finished: collided.':
            self.collision = 1
        
        rv = math.sqrt(pow(self.ego_vehicle.get_velocity().x,2) + pow(self.ego_vehicle.get_velocity().y,2))

        reward = self.success - self.collision
                 
        return reward