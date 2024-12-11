#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

"""
Created on Mon Jul 17 2023
@author: Rodrigo Gutiérrez Moreno
"""

import carla

import time
from random import choice, randint
import os, subprocess

class campusEnv():

    def __init__(self, render_mode):
        # Carla config ----------------------------------------------------------------------------
        self.client = carla.Client("localhost", 2000)
        self.client.set_timeout(2.0)
        self.world = self.client.get_world()
        self.map = self.world.get_map()

        # Weather settings ------------------------------------------------------------------------
        weather = carla.WeatherParameters(sun_altitude_angle=90.0)
        self.world.set_weather(weather)

        # Render mode -----------------------------------------------------------------------------
        if render_mode == False:
            settings = self.world.get_settings()
            settings.no_rendering_mode = True
            self.world.apply_settings(settings)

        # Destroy actors --------------------------------------------------------------------------
        actors = self.world.get_actors().filter('vehicle.*.*')
        for _, actor in enumerate(actors):
            if actor.type_id != 'vehicle.audi.a2':
                actor.destroy()

        # Set spectator ---------------------------------------------------------------------------
        spawn_point = self.map.get_waypoint_xodr(56,1,5)
        spectator = self.map.get_waypoint_xodr(56,1,0)
        world_transform = carla.Transform(carla.Location(x=spectator.transform.location.x+12, y=spectator.transform.location.y-5, z=3),
                                          carla.Rotation(yaw=-165, pitch = -5))
        # world_transform = carla.Transform(carla.Location(x=-267.582245, y=-374.686707, z=26.182993), carla.Rotation(pitch=-88.994965, yaw=-126.246040, roll=0.000584))
        self.world.get_spectator().set_transform(world_transform)

        # Spawn ego vehicle -----------------------------------------------------------------------------
        self.blueprint_library = self.world.get_blueprint_library()
        self.ego_vehicle_transform = carla.Transform(carla.Location(x=spawn_point.transform.location.x, y=spawn_point.transform.location.y, z=1), 
                                                    carla.Rotation(yaw=spawn_point.transform.rotation.yaw))
        actors = self.world.get_actors().filter('vehicle.*.*')
        if actors:
            for actor in actors:
                if actor.type_id == 'vehicle.audi.a2':
                    self.ego_vehicle = actor
                    print('\033[1;93m'+'Ego-vehicle found.' +'\033[0;m')
                    break
        else: 
            ego_vehicle_bp = self.blueprint_library.find('vehicle.audi.a2')
            self.ego_vehicle = self.world.spawn_actor(ego_vehicle_bp, self.ego_vehicle_transform)
            print('\033[1;93m'+'Ego-vehicle spawned.' +'\033[0;m')
        
        self.collision_sensor = self.world.spawn_actor(self.blueprint_library.find('sensor.other.collision'),
                                        carla.Transform(), attach_to=self.ego_vehicle)
        self.collision_sensor.listen(lambda event: self.function_handler(event))
        self.collision = False

        # Scenario variables
        self.transforms = self.define_transforms()
        # self.routes = ["Right", "Straight", "Left"]

        # Traffic Manager 
        self.tm = self.client.get_trafficmanager(8000)
        self.tm_port = self.tm.get_port()
        self.tm.global_percentage_speed_difference(10)

        self.steps = 0

        self.vehicles_index = 0
        self.vehicles = [2, 2, 2, 2, 2, 2]

        self.path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../../../"))
        self.path_published = True
        
    def get_ego_vehicle(self):
        return self.ego_vehicle

    def reset_scenario(self):            
        self.ego_vehicle.apply_control(carla.VehicleControl(throttle=0, steer=0, brake=1))
        # while(math.sqrt(pow(self.ego_vehicle.get_velocity().x,2) + pow(self.ego_vehicle.get_velocity().y,2)) > 0):
            # self.world.tick()
        self.ego_vehicle.set_transform(self.ego_vehicle_transform)

        self.time_reset = time.time()
        self.collision = False
        self.steps = 0
        # time.sleep(0.1)

    def step_scenario(self):
        self.steps += 1
        self.scenario()
        # self.world.tick()
        done, info = self.get_info()
        # time.sleep(0.01)

        return done, info

    def get_info(self):
        done = True
        waypoint = self.map.get_waypoint(self.ego_vehicle.get_location(),project_to_road=True, 
                   lane_type=(carla.LaneType.Driving | carla.LaneType.Sidewalk))
                
        if waypoint.road_id == 5:
            episode = 'Finished: succeed.'
        elif self.collision:
            episode = 'Finished: collided.'
        elif (time.time() - self.time_reset) > 1000:
            episode = 'Finished: timeout.'
        else:
            episode = 'Running.'
            done = False

        info = {'time' : time.time() - self.time_reset, 'episode' : episode, 'step' : self.steps}

        return done, info 
    
    def function_handler(self, event):
        event.other_actor.destroy()
        self.collision = True

    def define_transforms(self):
        waypoint_1 = self.map.get_waypoint_xodr(81,-2,60)
        waypoint_2 = self.map.get_waypoint_xodr(81,-1,90)
        transform_1 = carla.Transform(carla.Location(x=waypoint_1.transform.location.x, y=waypoint_1.transform.location.y, z=1), carla.Rotation(yaw=waypoint_1.transform.rotation.yaw))
        transform_2 = carla.Transform(carla.Location(x=waypoint_2.transform.location.x, y=waypoint_2.transform.location.y, z=1), carla.Rotation(yaw=waypoint_2.transform.rotation.yaw))
        transforms = [transform_1]

        return transforms

    def scenario(self):

        actors = self.world.get_actors().filter('vehicle.*.*')
        if len(actors) > 9 and self.path_published:
            self.path_published = False
            os.system("cd " + self.path + "&& ./route.sh &")

        if (time.time() - self.time_reset) > self.vehicles[self.vehicles_index]:
            if self.vehicles_index < (len(self.vehicles)-1):
                self.vehicles_index += 1
            else: 
                self.vehicles_index = 0
                
            self.time_reset = time.time()
            transform = choice(self.transforms)
            vehicle_bp = self.blueprint_library.find('vehicle.tesla.model3')
            adversary = self.world.try_spawn_actor(vehicle_bp, transform)
            if adversary:
                adversary.set_autopilot(True,self.tm_port)
                self.tm.ignore_lights_percentage(adversary,100)
                self.tm.distance_to_leading_vehicle(adversary,randint(2,3))
                self.tm.auto_lane_change(adversary, False)
                self.tm.vehicle_percentage_speed_difference(adversary,randint(30,31))
                self.tm.set_route(adversary, ["Straight"])

        for _, actor in enumerate(actors):
            if actor.id != self.ego_vehicle.id:
                actor.set_autopilot(True,self.tm_port)
                waypoint = self.map.get_waypoint(actor.get_location(),project_to_road=True, lane_type=(carla.LaneType.Driving | carla.LaneType.Sidewalk))
                if (waypoint.road_id == 3 and waypoint.s > 39) or \
                   (waypoint.road_id == 3 and waypoint.s > 39)or \
                   (waypoint.road_id == 56 and waypoint.lane_id == -1 and waypoint.s > 10):
                   actor.destroy()
            
