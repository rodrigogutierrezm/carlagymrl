#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

"""
Created on Mon Jul 17 2023
@author: Rodrigo Gutiérrez Moreno
"""

from gym import spaces
import numpy as np
import carla
# from carla_birdeye_view import BirdViewProducer, BirdViewCropType, PixelDimensions
import copy
import math



class Observations():

    def __init__(self, obs_mode = "low_dimensional", ego_vehicle = None):
        self.obs_mode = obs_mode

        self.client = carla.Client("localhost", 2000)
        self.client.set_timeout(2.0)
        self.world = self.client.get_world()
        self.map = self.world.get_map()
        self.ego_vehicle = ego_vehicle

        self.n_features = 4

    def get_observation_space(self):
        observation_space = spaces.Box(0,1,shape=(2*self.n_features,))
        return observation_space

    def reset_observations(self):
        pass

    def get_observations(self):  
        obs = np.array([1] * 2 * self.n_features)

        d_max = 50
        v_max = 8.5
        d = 0
        d_up = []
        v_up = []
        d_down = []
        v_down = []

        vehicles = self.world.get_actors().filter('vehicle.*.*')
        for vehicle in vehicles:
            if vehicle.id != self.ego_vehicle.id:
                waypoint = self.map.get_waypoint(vehicle.get_location(),project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Sidewalk))
                # if waypoint.road_id == 1661:
                #     d = round(((8 - waypoint.s) / d_max),2)
                #     if d >= 0 and d <= 1:
                #         d_down.append(abs(d))
                #         v_down.append(round(((math.sqrt(pow(vehicle.get_velocity().x,2) + pow(vehicle.get_velocity().y,2))) / v_max),2))
                if waypoint.road_id == 1655:
                    d = round(((18 - waypoint.s) / d_max),2)
                    if d >= 0 and d <= 1:
                        d_down.append(abs(d))
                        v_down.append(round(((math.sqrt(pow(vehicle.get_velocity().x,2) + pow(vehicle.get_velocity().y,2))) / v_max),2))     
                elif waypoint.road_id == 1566:
                    d = round(((waypoint.s + 18) / d_max),2)
                    if d >= 0 and d <= 1:
                        d_down.append(abs(d))
                        v_down.append(round(((math.sqrt(pow(vehicle.get_velocity().x,2) + pow(vehicle.get_velocity().y,2))) / v_max),2))     

        for _ in range(4):
            d_up.append(1)
            d_down.append(1)
            v_up.append(1)
            v_down.append(1)

        v_up = [x for _, x in sorted(zip(d_up, v_up))]
        d_up = np.sort(d_up)
        v_down = [x for _, x in sorted(zip(d_down, v_down))]
        d_down = np.sort(d_down)

        # obs = np.array([d_down[0],v_down[0],d_down[1],v_down[1]])
        obs = np.array([1,1,1,1,d_down[0],v_down[0],d_down[1],v_down[1]])

        return obs
