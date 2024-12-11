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
import transforms3d



class Observations():

    def __init__(self, obs_mode = "low_dimensional", ego_vehicle = None):
        self.obs_mode = obs_mode

        self.client = carla.Client("localhost", 2000)
        self.client.set_timeout(2.0)
        self.world = self.client.get_world()
        self.map = self.world.get_map()
        self.ego_vehicle = ego_vehicle

    def get_observation_space(self):
        observation_space = spaces.Box(0,1,shape=(12,))
        return observation_space

    def reset_observations(self):
        pass

    def get_observations(self):  
        d_ll=d_cl=d_rl=d_lf=d_cf=d_rf = 1
        v_ll=v_cl=v_rl=v_lf=v_cf=v_rf = 1
        max_range = 40
        v_max = 10
        obs = np.array([1] * 12)

        wp = self.map.get_waypoint(self.ego_vehicle.get_location())
        ego_lane_id = abs(wp.lane_id)

        actors = self.world.get_actors().filter('vehicle.*.*')

        for actor in actors:
            d = math.sqrt(pow((self.ego_vehicle.get_location().x - actor.get_location().x),2) + \
                          pow((self.ego_vehicle.get_location().y - actor.get_location().y),2))
            
            if d < max_range and d > 2:
                wp = self.map.get_waypoint(actor.get_location())

                actor_lane_id = abs(wp.lane_id)
                actor_loc = np.array([actor.get_location().x - self.ego_vehicle.get_location().x,
                                        actor.get_location().y - self.ego_vehicle.get_location().y,
                                        actor.get_location().z - self.ego_vehicle.get_location().z])
                roll = math.radians(actor.get_transform().rotation.roll)
                pitch = math.radians(actor.get_transform().rotation.pitch)
                yaw = math.radians(actor.get_transform().rotation.yaw)
                R = transforms3d.euler.euler2mat(roll,pitch,yaw).T
                actor_relative = np.dot(R,actor_loc)                               

                if actor_relative[0] > 0:      # Ahead
                    if actor_lane_id == ego_lane_id - 1 and d_ll > d / max_range:
                        d_ll = round(d / max_range, 2)
                        v_ll = round(math.sqrt(pow(actor.get_velocity().x,2) + pow(actor.get_velocity().y,2)) / v_max, 2)
                    elif actor_lane_id == ego_lane_id + 1 and d_rl > d / max_range:
                        d_rl = round(d / max_range, 2)
                        v_rl = round(math.sqrt(pow(actor.get_velocity().x,2) + pow(actor.get_velocity().y,2)) / v_max, 2)
                    elif ego_lane_id == actor_lane_id and d_cl > d / max_range:
                        d_cl = round(d / max_range, 2)
                        v_cl = round(math.sqrt(pow(actor.get_velocity().x,2) + pow(actor.get_velocity().y,2)) / v_max, 2)

                if actor_relative[0] < 0:      # Behind
                    if actor_lane_id == ego_lane_id - 1 and d_lf > d / max_range:
                        d_lf = round(d / max_range, 2)
                        v_lf = round(math.sqrt(pow(actor.get_velocity().x,2) + pow(actor.get_velocity().y,2)) / v_max, 2)
                    elif actor_lane_id == ego_lane_id + 1 and d_rf > d / max_range:
                        d_rf = round(d / max_range, 2)
                        v_rf = round(math.sqrt(pow(actor.get_velocity().x,2) + pow(actor.get_velocity().y,2)) / v_max, 2)
                    elif ego_lane_id == actor_lane_id and d_cf > d / max_range:
                        d_cf = round(d / max_range, 2)
                        v_cf = round(math.sqrt(pow(actor.get_velocity().x,2) + pow(actor.get_velocity().y,2)) / v_max, 2)

        obs = np.array([d_ll, v_ll, d_cl, v_cl, d_rl, v_rl, d_lf, v_lf, d_cf, v_cf, d_rf, v_rf])

        return obs
