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

from src.utils.scenario import select_scenario
from src.utils.actions import Actions
from src.utils.reward import Reward

class CarlaEnv(gym.Env):
    metadata = {"render_modes": ["features", "top_view", "camera"], "render_fps": 4}

    def __init__(self, render_mode=True, obs_mode="low-dimensional", scenario="crossroad"):

        scenarioEnv, Observations = select_scenario(scenario)
        self.env = scenarioEnv(render_mode)
        ego_vehicle = self.env.get_ego_vehicle()

        self.observation_env = Observations(obs_mode = obs_mode, ego_vehicle = ego_vehicle)
        self.observation_space = self.observation_env.get_observation_space()

        self.action_env = Actions(ego_vehicle = ego_vehicle) 
        self.action_space = self.action_env.get_actions_space(n_actions=2)

        self.reward_env = Reward(ego_vehicle = ego_vehicle)
        self.reward_mean = 0

    def reset(self):

        self.env.reset_scenario()
        self.observation_env.reset_observations()
        self.reward_env.reset_reward()

        observations = self.observation_env.get_observations()

        self.reward_mean = 0
        
        return observations

    def step(self, action):
        done = 0

        if action == 1:
            while not done:
                self.action_env.set_actions(action)
                done, info = self.env.step_scenario()  
                reward = self.reward_env.get_reward(info)
                observations = self.observation_env.get_observations()  
                self.reward_mean += reward
        else:
            self.action_env.set_actions(action)
            done, info = self.env.step_scenario()  
            reward = self.reward_env.get_reward(info)
            observations = self.observation_env.get_observations()  
            self.reward_mean += reward

        if done:
            info['reward_mean'] = self.reward_mean
            # print(info)
        
        info = {}

        return observations, reward, done, info


    
