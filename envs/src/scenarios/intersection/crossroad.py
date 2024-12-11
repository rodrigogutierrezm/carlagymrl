#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

"""
Created on Mon Jul 17 2023
@author: Rodrigo Gutiérrez Moreno
"""

import carla

import time
from random import choice, randint
import math

class crossroadEnv():

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

        settings = self.world.get_settings()
        settings.synchronous_mode = True
        self.world.apply_settings(settings)

        # Destroy actors --------------------------------------------------------------------------
        actors = self.world.get_actors().filter('vehicle.*.*')
        for _, actor in enumerate(actors):
            if actor.type_id != 'vehicle.audi.a2':
                actor.destroy()

        # Set spectator ---------------------------------------------------------------------------
        spawn_point = self.map.get_waypoint_xodr(28,-2,70)
        world_transform = carla.Transform(carla.Location(x=spawn_point.transform.location.x, y=spawn_point.transform.location.y-20, z=70),
                                          carla.Rotation(yaw=0, pitch = -90))
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
        self.vehicles = [2, 2, 2, 6, 2, 6]
        
    def get_ego_vehicle(self):
        return self.ego_vehicle

    def reset_scenario(self):            
        self.ego_vehicle.apply_control(carla.VehicleControl(throttle=0, steer=0, brake=1))
        while(math.sqrt(pow(self.ego_vehicle.get_velocity().x,2) + pow(self.ego_vehicle.get_velocity().y,2)) > 0):
            self.world.tick()
        self.ego_vehicle.set_transform(self.ego_vehicle_transform)

        self.time_reset = time.time()
        self.collision = False
        self.steps = 0
        time.sleep(0.1)

    def step_scenario(self):
        self.steps += 1
        self.scenario()
        self.world.tick()
        done, info = self.get_info()
        time.sleep(0.01)

        return done, info

    def get_info(self):
        done = True
        waypoint = self.map.get_waypoint(self.ego_vehicle.get_location(),project_to_road=True, 
                   lane_type=(carla.LaneType.Driving | carla.LaneType.Sidewalk))
                
        if waypoint.road_id == 879:
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
        waypoint_left_1 = self.map.get_waypoint_xodr(19, 1, 20)
        transform_left_1 = carla.Transform(carla.Location(x=waypoint_left_1.transform.location.x, y=waypoint_left_1.transform.location.y, z=5), carla.Rotation(yaw=waypoint_left_1.transform.rotation.yaw))

        waypoint_right_1 = self.map.get_waypoint_xodr(18, -1, 22)
        transform_right_1 = carla.Transform(carla.Location(x=waypoint_right_1.transform.location.x, y=waypoint_right_1.transform.location.y, z=5), carla.Rotation(yaw=waypoint_right_1.transform.rotation.yaw))

        transforms = [transform_left_1, transform_right_1]

        return transforms

    def scenario(self):
        actors = self.world.get_actors().filter('vehicle.*.*')

        if (time.time() - self.time_reset) > self.vehicles[self.vehicles_index]:
            if self.vehicles_index < (len(self.vehicles)-1):
                self.vehicles_index += 1
            else: 
                self.vehicles_index = 0

            self.time_reset = time.time()
            # route = [choice(self.routes)]
            # transform = choice(self.transforms)
            for i in range(len(self.transforms)):
                transform = self.transforms[i]

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
                if (waypoint.road_id == 18 and waypoint.lane_id > 0) or \
                   (waypoint.road_id == 19 and waypoint.lane_id < 0):
                   actor.destroy()
            
