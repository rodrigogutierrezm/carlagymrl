#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

"""
Created on Mon Jul 17 2023
@author: Rodrigo Gutiérrez Moreno
"""
import sys, os

def select_scenario(scenario=None):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
    if scenario == "highway":
        from scenarios.highway.highway import highwayEnv as scenarioEnv
        from utils.observationshighway import Observations
    elif scenario == "roundabout":
        from scenarios.intersection.roundabout import roundaboutEnv as scenarioEnv
        from utils.observationsroundabout import Observations
    elif scenario == "merge":
        from scenarios.intersection.merge import mergeEnv as scenarioEnv
        from utils.observationsmerge import Observations
    elif scenario == "crossroad":
        from scenarios.intersection.crossroad import crossroadEnv as scenarioEnv
        from utils.observationscrossroad import Observations
    elif scenario == "campus":
        from scenarios.intersection.campus import campusEnv as scenarioEnv
        from utils.observationscampus import Observations
    elif scenario == "concatenated":
        from scenarios.benchmark.benchmark import benchmarkEnv as scenarioEnv
        from utils.observationscrossroad import Observations

    return scenarioEnv, Observations
