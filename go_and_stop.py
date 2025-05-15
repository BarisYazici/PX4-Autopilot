#!/usr/bin/env python3

import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw

# Main function
async def run():
    # Connect to the drone
    drone = System()
    await drone.connect(system_address="udp://:14540")  # Simulator address

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

    # Arm the drone
    print("Arming the drone...")
    await drone.action.arm()

    # Start offboard mode
    print("Starting offboard mode...")
    try:
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error: {error}")
        print("Disarming")
        await drone.action.disarm()
        return

    # Take off to 2 meters
    print("Taking off to 2 meters...")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -2.0, 0.0))
    await asyncio.sleep(5)  # Give time to reach altitude

    # Move forward 5 meters
    print("Moving forward 5 meters...")
    await drone.offboard.set_position_ned(PositionNedYaw(5.0, 0.0, -2.0, 0.0))
    await asyncio.sleep(10)  # Give time to reach the position

    # Stop and hover
    print("Stopping and hovering...")
    await drone.offboard.set_position_ned(PositionNedYaw(5.0, 0.0, -2.0, 0.0))
    await asyncio.sleep(5)  # Hover for 5 seconds

    # Return to launch position
    print("Returning to launch position...")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -2.0, 0.0))
    await asyncio.sleep(10)  # Give time to return

    # Land
    print("Landing...")
    await drone.action.land()

    # Wait until landed and disarm
    await asyncio.sleep(10)
    print("Disarming...")
    await drone.action.disarm()

# Run the main function
if __name__ == "__main__":
    asyncio.run(run())
