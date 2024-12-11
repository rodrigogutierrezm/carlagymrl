import carla
import math
import time
from envs.src.carlaEnvConcat import CarlaEnv as Env

class AutopilotAgent:
    def __init__(self):
        # Initialize the CARLA client
        self.client = carla.Client('localhost', 2000)
        self.client.set_timeout(10.0)
        self.client.load_world('Town03')

        try:
            # Retrieve the world and setup settings
            self.world = self.client.get_world()
            self._setup_synchronous_mode()

            # Load and spawn the Audi A2
            self.vehicle = self._spawn_vehicle('vehicle.audi.a2')

            # Initialize traffic manager
            self.tm = self.client.get_trafficmanager(8000)  # Default port 8000
            self.tm_port = self.tm.get_port()

            # Disable autopilot initially
            self.vehicle.set_autopilot(False, self.tm_port)

            # Setup the environment
            self.env = Env()
        except Exception as e:
            print(f"An error occurred during initialization: {e}")
            raise

    def _setup_synchronous_mode(self):
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 1.0 / 20.0
        self.world.apply_settings(settings)

    def _spawn_vehicle(self, blueprint_name):
        blueprint_library = self.world.get_blueprint_library()
        vehicle_bp = blueprint_library.find(blueprint_name)

        spawn_points = self.world.get_map().get_spawn_points()
        if not spawn_points:
            raise RuntimeError("No spawn points available in the current map.")

        spawn_point = spawn_points[0]  # Use the first spawn point
        return self.world.spawn_actor(vehicle_bp, spawn_point)
    
    def reset(self):
        self.env.reset()
        self.world.tick()
        for i in range(200):
            self.update_spectator_view()
            self.env.step(0)  # Perform environment step
            self.world.tick()
            time.sleep(0.05)  # Ensure smooth execution

    def enable_autopilot(self):
        # Set predefined route for autopilot (straight path)
        route = ["Straight"] * 5
        self.tm.set_route(self.vehicle, route)
        self.tm.vehicle_percentage_speed_difference(self.vehicle, -80)
        self.vehicle.set_autopilot(True)

    def update_spectator_view(self):
        # Update the spectator view to follow the vehicle
        transform = self.vehicle.get_transform()
        location = transform.location
        yaw = transform.rotation.yaw

        dist_camera = 15
        x_offset = math.cos(math.radians(yaw) + math.pi) * dist_camera
        y_offset = math.sin(math.radians(yaw) + math.pi) * dist_camera

        spectator_transform = carla.Transform(
            carla.Location(x=location.x + x_offset, y=location.y + y_offset, z=10),
            carla.Rotation(yaw=yaw, pitch=-15)
        )
        self.world.get_spectator().set_transform(spectator_transform)

    def run(self):
        try:
            # Reset environment and enable autopilot
            self.reset()
            self.enable_autopilot() # HERE: Your code can be initialized.
            
            while True:
                self.update_spectator_view()
                self.env.step(0)  # HERE: You can send the control commands.
                self.world.tick()
                time.sleep(0.05)  # Ensure smooth execution

        except KeyboardInterrupt:
            print("Simulation interrupted by user.")
        except Exception as e:
            print(f"An error occurred during execution: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        # Destroy the vehicle and reset world settings
        if self.vehicle:
            self.vehicle.destroy()
        settings = self.world.get_settings()
        settings.synchronous_mode = False
        settings.fixed_delta_seconds = None
        self.world.apply_settings(settings)

if __name__ == '__main__':
    try:
        agent = AutopilotAgent()
        agent.run()  # Run the simulation for 100000 ticks
    except Exception as e:
        print(f"Failed to initialize AutopilotAgent: {e}")
