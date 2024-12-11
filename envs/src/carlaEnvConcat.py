#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

"""
Created on Mon Jul 17 2023
@author: Rodrigo Gutiérrez Moreno
"""

import os
import sys

# sys.path.append(git.Repo(__file__, search_parent_directories=True).working_tree_dir)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import gym

from src.scenarios.benchmark.benchmark import benchmarkEnv as scenarioEnv
from src.utils.observationscrossroad import Observations as observationscrossroad
from src.utils.observationsmerge import Observations as observationsmerge
from src.utils.observationsroundabout import Observations as observationsroundabout
from src.utils.observationshighway import Observations as observationshighway

from src.utils.actions import Actions
from src.utils.reward import Reward

class CarlaEnv(gym.Env):
    metadata = {"render_modes": ["features", "top_view", "camera"], "render_fps": 4}

    def __init__(self, render_mode=True, obs_mode="low-dimensional"):

        self.env = scenarioEnv(render_mode)
        ego_vehicle = self.env.get_ego_vehicle()

        self.observation_crossroad = observationscrossroad(obs_mode = obs_mode, ego_vehicle = ego_vehicle)
        self.observation_merge = observationsmerge(obs_mode = obs_mode, ego_vehicle = ego_vehicle)
        self.observation_roundabout = observationsroundabout(obs_mode = obs_mode, ego_vehicle = ego_vehicle)
        self.observation_space = self.observation_crossroad.get_observation_space()

        self.action_env = Actions(ego_vehicle = ego_vehicle) 
        self.action_space = self.action_env.get_actions_space()

        self.reward_env = Reward(ego_vehicle = ego_vehicle)
        self.reward_mean = 0

    def reset(self):

        self.env.reset_scenario()
        self.observation_roundabout.reset_observations()
        self.reward_env.reset_reward()

        observations = self.observation_roundabout.get_observations()

        self.reward_mean = 0
        
        return observations

    def step(self, action):
        done = 0

        if action == 0:
            observations = self.observation_roundabout.get_observations()  
        elif action == 1:
            observations = self.observation_crossroad.get_observations() 
        elif action == 2:
            observations = self.observation_merge.get_observations() 

        self.action_env.set_actions(action)
        done, info = self.env.step_scenario()  
        reward = self.reward_env.get_reward(info)    
        self.reward_mean += reward

        if done:
            info['reward_mean'] = self.reward_mean
            # print(info)
        
        info = {}

        return observations, reward, done, info

    
