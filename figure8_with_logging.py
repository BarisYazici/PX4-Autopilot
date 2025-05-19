#!/usr/bin/env python3

import asyncio
import math
import csv
import time
import os
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw

# Parameters for figure 8
ALTITUDE = -2.0  # Negative because NED coordinate system (2 meters down from home)
RADIUS = 5.0  # Radius of each circle in meters
NUM_POINTS = 60  # Number of points per circle, more points = smoother path
HOVER_TIME = 0.2  # Time to hover at each point (seconds)

# Initialize data log lists
timestamps = []
positions_n = []
positions_e = []
positions_d = []
velocities_n = []
velocities_e = []
velocities_d = []
attitudes_roll = []
attitudes_pitch = []
attitudes_yaw = []
motor_rpms = []

# Generate points for a figure 8 pattern in the NED frame
def generate_figure8_points():
    points = []

    # First circle (left side of the 8)
    for i in range(NUM_POINTS):
        angle = 2 * math.pi * i / NUM_POINTS
        x = -RADIUS * math.cos(angle)  # Negative to go to the left
        y = RADIUS * math.sin(angle)
        points.append(PositionNedYaw(x, y, ALTITUDE, 0.0))

    # Second circle (right side of the 8)
    for i in range(NUM_POINTS):
        angle = 2 * math.pi * i / NUM_POINTS
        x = RADIUS * math.cos(angle)  # Positive to go to the right
        y = -RADIUS * math.sin(angle)  # Negative to create the 8 pattern
        points.append(PositionNedYaw(x, y, ALTITUDE, 0.0))

    return points

# Save the logged data to a CSV file
def save_to_csv():
    data_dir = "flight_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    filename = f"{data_dir}/figure8_flight_{int(time.time())}.csv"

    # Ensure all lists have the same length by padding with zeros
    max_length = max(len(timestamps), len(positions_n), len(positions_e), len(positions_d),
                     len(velocities_n), len(velocities_e), len(velocities_d),
                     len(attitudes_roll), len(attitudes_pitch), len(attitudes_yaw),
                     len(motor_rpms))

    print(f"Data points collected: {max_length}")

    # Pad lists with zeros if needed
    timestamps.extend([0] * (max_length - len(timestamps)))
    positions_n.extend([0] * (max_length - len(positions_n)))
    positions_e.extend([0] * (max_length - len(positions_e)))
    positions_d.extend([0] * (max_length - len(positions_d)))
    velocities_n.extend([0] * (max_length - len(velocities_n)))
    velocities_e.extend([0] * (max_length - len(velocities_e)))
    velocities_d.extend([0] * (max_length - len(velocities_d)))
    attitudes_roll.extend([0] * (max_length - len(attitudes_roll)))
    attitudes_pitch.extend([0] * (max_length - len(attitudes_pitch)))
    attitudes_yaw.extend([0] * (max_length - len(attitudes_yaw)))
    motor_rpms.extend([0] * (max_length - len(motor_rpms)))

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Timestamp',
            'Position_N', 'Position_E', 'Position_D',
            'Velocity_N', 'Velocity_E', 'Velocity_D',
            'Attitude_Roll', 'Attitude_Pitch', 'Attitude_Yaw',
            'Motor_RPMs'
        ])

        for i in range(max_length):
            try:
                writer.writerow([
                    timestamps[i],
                    positions_n[i], positions_e[i], positions_d[i],
                    velocities_n[i], velocities_e[i], velocities_d[i],
                    attitudes_roll[i], attitudes_pitch[i], attitudes_yaw[i],
                    motor_rpms[i]
                ])
            except IndexError as e:
                print(f"Error while writing row {i}: {e}")
                # Skip this row if there's an index error
                continue

    print(f"Flight data saved to {filename}")

# Log drone telemetry data
async def log_telemetry(drone):
    # Start the telemetry monitoring tasks
    position_task = asyncio.create_task(monitor_position(drone))
    velocity_task = asyncio.create_task(monitor_velocity(drone))
    attitude_task = asyncio.create_task(monitor_attitude(drone))
    rpm_task = asyncio.create_task(monitor_actuator_output_status(drone))

    # Return a function to stop the logging
    def stop_logging():
        position_task.cancel()
        velocity_task.cancel()
        attitude_task.cancel()
        rpm_task.cancel()

    return stop_logging

# Monitor position updates
async def monitor_position(drone):
    try:
        async for position in drone.telemetry.position():
            current_time = time.time()
            timestamps.append(current_time)
            positions_n.append(position.relative_altitude_m if hasattr(position, 'relative_altitude_m') else 0.0)
            positions_e.append(position.latitude_deg if hasattr(position, 'latitude_deg') else 0.0)
            positions_d.append(position.longitude_deg if hasattr(position, 'longitude_deg') else 0.0)
            await asyncio.sleep(0.1)  # Update at 10Hz
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in position monitoring: {e}")

# Monitor velocity updates
async def monitor_velocity(drone):
    try:
        async for velocity in drone.telemetry.velocity_ned():
            velocities_n.append(velocity.north_m_s if hasattr(velocity, 'north_m_s') else 0.0)
            velocities_e.append(velocity.east_m_s if hasattr(velocity, 'east_m_s') else 0.0)
            velocities_d.append(velocity.down_m_s if hasattr(velocity, 'down_m_s') else 0.0)
            await asyncio.sleep(0.1)  # Update at 10Hz
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in velocity monitoring: {e}")

# Monitor attitude updates
async def monitor_attitude(drone):
    try:
        async for attitude in drone.telemetry.attitude_euler():
            attitudes_roll.append(attitude.roll_deg if hasattr(attitude, 'roll_deg') else 0.0)
            attitudes_pitch.append(attitude.pitch_deg if hasattr(attitude, 'pitch_deg') else 0.0)
            attitudes_yaw.append(attitude.yaw_deg if hasattr(attitude, 'yaw_deg') else 0.0)
            await asyncio.sleep(0.1)  # Update at 10Hz
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in attitude monitoring: {e}")

# Monitor actuator output status for motor RPMs
async def monitor_actuator_output_status(drone):
    try:
        async for actuator_output_status in drone.telemetry.actuator_output_status():
            # Save the average of all motor RPMs (or save individual motors if preferred)
            if hasattr(actuator_output_status, 'actuator') and len(actuator_output_status.actuator) > 0:
                avg_rpm = sum(actuator_output_status.actuator) / len(actuator_output_status.actuator)
                motor_rpms.append(avg_rpm)
            else:
                motor_rpms.append(0.0)
            await asyncio.sleep(0.1)  # Update at 10Hz
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error monitoring actuator output: {e}")
        # If the drone doesn't support this telemetry, append zeros
        motor_rpms.append(0.0)

# Main function
async def run():
    # Connect to the drone
    drone = System()
    await drone.connect(system_address="udp://:14550")  # Simulator address

    # Wait for the drone to connect
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break

    # Set up the safety check
    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate is ok")
            break

    # Check if the drone is ready to arm
    print("Waiting for drone to be ready to arm...")
    async for health in drone.telemetry.health():
        if (health.is_home_position_ok and
            health.is_armable):
            print("Drone is ready to arm!")
            break
        print("Drone not ready to arm, waiting...")
        print(f"Health: {health}")
        await asyncio.sleep(1)

    # Start logging telemetry data
    print("Starting telemetry logging...")
    stop_logging = await log_telemetry(drone)

    try:
        # Arm the drone
        print("Arming the drone...")
        try:
            await drone.action.arm()
        except Exception as e:
            print(f"Arming failed: {e}")
            # Try to force arming if normal arming failed
            print("Attempting to arm with force...")
            try:
                await drone.action.arm()
            except Exception as e:
                print(f"Force arming also failed: {e}")
                stop_logging()
                save_to_csv()
                return

        # Start offboard mode
        print("Starting offboard mode...")
        try:
            await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
            await drone.offboard.start()
        except OffboardError as error:
            print(f"Starting offboard mode failed with error: {error}")
            print("Disarming")
            await drone.action.disarm()
            stop_logging()
            save_to_csv()
            return

        # Take off to 2 meters
        print("Taking off to 2 meters...")
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, ALTITUDE, 0.0))
        await asyncio.sleep(5)  # Give time to reach altitude

        # Generate the figure 8 path
        figure8_points = generate_figure8_points()

        # Execute the figure 8 pattern
        print("Starting figure 8 pattern...")
        try:
            for point in figure8_points:
                await drone.offboard.set_position_ned(point)
                await asyncio.sleep(HOVER_TIME)
        except Exception as e:
            print(f"Error during figure 8 pattern: {e}")

        # Return to launch position
        print("Returning to launch position...")
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, ALTITUDE, 0.0))
        await asyncio.sleep(5)  # Give time to return

        # Land
        print("Landing...")
        await drone.action.land()

        # Wait until landed and disarm
        await asyncio.sleep(10)
        print("Disarming...")
        await drone.action.disarm()

    except Exception as e:
        print(f"Flight error: {e}")
    finally:
        # Stop logging and save data in any case
        print("Stopping telemetry logging...")
        stop_logging()

        # Save the collected data
        print("Saving flight data...")
        save_to_csv()

# Run the main function
if __name__ == "__main__":
    asyncio.run(run())
