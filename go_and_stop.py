#!/usr/bin/env python3

import asyncio
import sys
import time
from mavsdk import System
from mavsdk.offboard import OffboardError, PositionNedYaw
from mavsdk.action import ActionError

# Main function
async def run():
    # Connect to the drone
    drone = System()

    # Try different common connection URLs
    connection_urls = [
        "udp://:14550",       # Standard PX4 SITL
        "udp://127.0.0.1:14540",
        "udp://localhost:14540",
        "udp://:14550",       # QGroundControl default
        "udp://127.0.0.1:14550",
        "udp://127.0.0.1:18570",  # GCS port
        "tcp://:5760"         # SITL TCP connection
    ]

    connected = False
    for url in connection_urls:
        print(f"Trying to connect to {url}...")
        try:
            await drone.connect(system_address=url)
            print(f"Connected to {url}, waiting for heartbeat...")

            # Use a longer 10 second timeout for initial connection
            connection_timeout = 10
            connection_start_time = time.time()

            while time.time() - connection_start_time < connection_timeout:
                try:
                    async for state in drone.core.connection_state():
                        if state.is_connected:
                            print(f"✅ Drone connected via {url}!")
                            connected = True
                            break
                        print(f"Waiting for connection on {url}... (state={state})")
                        await asyncio.sleep(1)

                    if connected:
                        break
                except asyncio.TimeoutError:
                    print(f"Timeout in connection state check for {url}")

                if connected:
                    break

                await asyncio.sleep(1)

            if connected:
                break
            else:
                print(f"Could not establish stable connection via {url}, trying next...")

        except Exception as e:
            print(f"Error connecting to {url}: {e}")

    if not connected:
        print("Failed to connect to the drone. Please check if the simulation is running correctly.")
        print("Ensure PX4 is publishing MAVLink on one of the tested ports.")
        print("\nTroubleshooting tips:")
        print("1. Make sure the simulation is running with: make px4_sitl_default gz_phobos")
        print("2. Check the PX4 terminal output for MAVLink configuration issues")
        print("3. Ensure ports are correctly configured:")
        print("   - Check that MAVLink broadcasting is enabled (MAV_X_BROADCAST=1)")
        print("   - Ensure firewall isn't blocking UDP connections")
        print("4. Try modifying the script to use the port showing activity in the PX4 logs")
        return

    # Print flight mode before attempting anything
    print("Current flight mode:")
    try:
        async for flight_mode in drone.telemetry.flight_mode():
            print(f"Flight mode: {flight_mode}")
            break
    except Exception as e:
        print(f"Error getting flight mode: {e}")

    # Set PX4 parameters to make arming easier
    print("\nSetting PX4 parameters to bypass strict arming checks (for simulation)...")
    try:
        # Allow arming without GPS
        await drone.param.set_param_int("COM_ARM_WO_GPS", 1)
        print("Set COM_ARM_WO_GPS = 1")

        # Disable magnetometer checks
        await drone.param.set_param_int("COM_ARM_MAG_STR", 0)
        print("Set COM_ARM_MAG_STR = 0")

        # Disable prearm check
        await drone.param.set_param_int("COM_PREARM_MODE", 0)
        print("Set COM_PREARM_MODE = 0")

        # Make accelerometer checks less strict
        await drone.param.set_param_float("COM_ARM_IMU_ACC", 0.7)
        print("Set COM_ARM_IMU_ACC = 0.7")

        # Set system to report armable
        await drone.param.set_param_int("COM_ARM_CHK_ESCS", 0)
        print("Set COM_ARM_CHK_ESCS = 0")

        # Wait for parameters to take effect
        print("Waiting for parameters to take effect...")
        await asyncio.sleep(2)

    except Exception as e:
        print(f"Error setting parameters: {e}")
        # Continue anyway as some drones might not support parameter setting

    # Check health parameters
    print("Checking drone health status...")
    try:
        health_check_start = time.time()
        health_check_timeout = 30  # seconds
        health_ok = False

        while time.time() - health_check_start < health_check_timeout:
            async for health in drone.telemetry.health():
                print(f"\nHealth object: {health}")

                print("\nDrone Health Status:")

                # Only use attributes that are available in the Health object
                if hasattr(health, "is_global_position_ok"):
                    print(f"- Global Position:      {'✅' if health.is_global_position_ok else '❌'}")

                if hasattr(health, "is_local_position_ok"):
                    print(f"- Local Position:       {'✅' if health.is_local_position_ok else '❌'}")

                if hasattr(health, "is_home_position_ok"):
                    print(f"- Home Position:        {'✅' if health.is_home_position_ok else '❌'}")

                if hasattr(health, "is_accelerometer_calibration_ok"):
                    print(f"- Accelerometer:        {'✅' if health.is_accelerometer_calibration_ok else '❌'}")

                if hasattr(health, "is_gyro_calibration_ok"):
                    print(f"- Gyro:                 {'✅' if health.is_gyro_calibration_ok else '❌'}")

                if hasattr(health, "is_magnetometer_calibration_ok"):
                    print(f"- Magnetometer:         {'✅' if health.is_magnetometer_calibration_ok else '❌'}")

                if hasattr(health, "is_level_calibration_ok"):
                    print(f"- Level Calibration:    {'✅' if health.is_level_calibration_ok else '❌'}")

                if hasattr(health, "is_armable"):
                    print(f"- Armable:              {'✅' if health.is_armable else '❌'}")

                    if health.is_armable:
                        print("Drone is armable!")
                        health_ok = True
                        break
                    else:
                        print("\nDrone is NOT armable. Trying direct arm anyway...")
                else:
                    # If is_armable attribute doesn't exist, check other conditions
                    # Typically global position and home position are required
                    required_checks = []
                    if hasattr(health, "is_global_position_ok"):
                        required_checks.append(health.is_global_position_ok)
                    if hasattr(health, "is_home_position_ok"):
                        required_checks.append(health.is_home_position_ok)
                    if hasattr(health, "is_local_position_ok"):
                        required_checks.append(health.is_local_position_ok)

                    if required_checks and all(required_checks):
                        print("All available position checks passed, attempting to arm")
                        health_ok = True
                        break
                    else:
                        print("\nOne or more position checks failed. Trying direct arm anyway...")

                # We'll try arming anyway after displaying the checks
                print("\nTrying to arm despite health checks...")
                break

            # Try arming in different ways - since we've changed parameters, we might be able to arm now
            try:
                print("\nTrying standard arming...")
                await drone.action.arm()
                print("✅ ARMING SUCCESSFUL!")
                health_ok = True
                break
            except ActionError as e:
                print(f"Standard arming error: {e}")

                # Try force arming since parameter setting might not have worked
                try:
                    print("\nTrying force arming...")
                    await drone.action.arm(force=True)
                    print("✅ FORCE ARMING SUCCESSFUL!")
                    health_ok = True
                    break
                except Exception as e:
                    print(f"Force arming error: {e}")

            # Wait before trying again
            print("\nWaiting 3 seconds before trying again...")
            await asyncio.sleep(3)

        if not health_ok:
            print("\n⚠️ Could not arm the drone after multiple attempts")
            print("\nAdvanced PX4 parameter suggestions:")
            print("1. Set ARM_DISARM_REASON=1 (allows arming for HITL)")
            print("2. Set SYS_HITL=1 (enables HITL simulation mode)")
            print("3. Disable all arming checks with COM_ARM_ALL_CHECKS=0 (USE WITH CAUTION)")
            print("4. Try using QGroundControl to manually arm and diagnose issues")

            # Try one final approach - kill switch parameter for all arm checks
            try:
                print("\nLast resort: Disabling ALL arming checks...")
                await drone.param.set_param_int("COM_ARM_AUTH_REQ", 0)
                await drone.param.set_param_int("COM_ARM_ALL_CHECKS", 0)
                await asyncio.sleep(2)

                print("Trying to arm with all checks disabled...")
                await drone.action.arm(force=True)
                print("✅ ARMING SUCCESSFUL by disabling all checks!")
                health_ok = True
            except Exception as e:
                print(f"Final arming attempt failed: {e}")
                print("\nPlease check the PX4 logs for specific arming denials and try resolving those issues.")
                return

    except asyncio.CancelledError:
        print("Health check cancelled")
        return
    except Exception as e:
        print(f"Error checking health: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        return

    # Print drone status
    print("Fetching drone information...")
    try:
        async for flight_mode in drone.telemetry.flight_mode():
            print(f"Flight mode: {flight_mode}")
            break

        async for battery in drone.telemetry.battery():
            print(f"Battery: {battery.remaining_percent * 100:.1f}%")
            break

        async for position in drone.telemetry.position():
            print(f"Position: lat: {position.latitude_deg}, lon: {position.longitude_deg}, alt: {position.relative_altitude_m}")
            break
    except Exception as e:
        print(f"Error fetching drone info: {e}")

    # Start offboard mode
    print("Starting offboard mode...")
    try:
        # Set the initial setpoint before starting offboard mode
        print("Setting initial setpoint...")
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))

        # Try to start offboard mode
        print("Enabling offboard mode...")
        await drone.offboard.start()
    except OffboardError as error:
        print(f"Starting offboard mode failed with error: {error}")
        print("Disarming")
        await drone.action.disarm()
        return
    except Exception as e:
        print(f"Unexpected error starting offboard: {e}")
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
    try:
        await drone.action.land()
    except Exception as e:
        print(f"Error during landing: {e}")

    # Wait until landed and disarm
    await asyncio.sleep(10)
    print("Disarming...")
    await drone.action.disarm()

# Run the main function
if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Script interrupted, exiting.")
    except Exception as e:
        print(f"Unexpected error: {e}")
