# Gazebo Harmonic Simulation Setup Guide for PX4

This guide explains how to set up and run Gazebo Harmonic (version 8) simulations with PX4 Autopilot, focusing on the Phobos drone model.

## Prerequisites

- PX4 Autopilot source code
- Gazebo Harmonic installed
- Basic understanding of PX4 and Gazebo

## Setup Steps

### 1. Ensure the Airframe Configuration

The Phobos drone uses the airframe configuration file located at:
```
ROMFS/px4fmu_common/init.d-posix/airframes/4023_gz_phobos
```

Make sure this file exists and is correctly configured for your Phobos drone model.

### 2. Ensure the Model is Available

The Phobos model should be available in the following location:
```
Tools/simulation/gz/models/phobos/
```

### 3. Update the CMakeLists.txt

Ensure the airframe configuration file is listed in the ROMFS CMakeLists.txt:
```
ROMFS/px4fmu_common/init.d-posix/airframes/CMakeLists.txt
```

Add the following line to the list of files in the `px4_add_romfs_files` section:
```
4023_gz_phobos
```

### 4. Source the Gazebo Harmonic Setup Script

Before building and running simulations, source the Gazebo Harmonic setup script:
```bash
source ./setup_gazebo_harmonic.sh
```

This script sets up the necessary environment variables for PX4 to detect and use Gazebo Harmonic.

## Building and Running

### Build and Launch the Simulation

Use the following command to build and launch the simulation:
```bash
make clean && make px4_sitl_default gz_phobos
```

The `gz_phobos` target tells PX4 to use the Phobos model with Gazebo Harmonic.

### Headless Mode (No GUI)

If you want to run the simulation without the GUI (useful for CI or performance reasons):
```bash
HEADLESS=1 make px4_sitl_default gz_phobos
```

## Controlling the Drone

Once the simulation is running, you can control the drone using:

1. **QGroundControl**: Connect to the drone using QGroundControl
2. **MAVSDK**: Use MAVSDK to programmatically control the drone
3. **Command Line**: Use the PX4 shell (pxh>) to issue commands

### Common PX4 Shell Commands

```
commander takeoff    # Takeoff the drone
commander land       # Land the drone
commander arm        # Arm the motors
commander disarm     # Disarm the motors
param set SYS_AUTOSTART 4023  # Set the autostart to Phobos model
```

## Example Flight Patterns

### Running the Go and Stop Example

To run the simple "Go and Stop" example which demonstrates basic drone control:

1. Start the Gazebo Harmonic simulation:
```bash
make px4_sitl_default gz_phobos
```

2. In a separate terminal, run the Go and Stop example script:
```bash
python3 go_and_stop.py
```

This script will:
- Take off the drone to a predefined altitude
- Move forward for a specified distance
- Hover in position
- Return to the starting position
- Land safely

### Running the Figure 8 Pattern Example

To run the Figure 8 trajectory example:

1. Start the Gazebo Harmonic simulation:
```bash
make px4_sitl_default gz_phobos
```

2. In a separate terminal, run the Figure 8 example script:
```bash
python3 figure8_example.py
```

This script will:
- Take off the drone to a specified altitude
- Perform a figure 8 pattern using offboard control
- Log position data during the flight
- Return to the starting position and land

You can adjust parameters such as the size of the figure 8 and flight speed by modifying the script.

## Troubleshooting

### Model Not Found

If you encounter an error like "Unknown model", ensure:
1. The airframe file is correctly listed in CMakeLists.txt
2. The model exists in the gz/models directory
3. You've correctly sourced the setup_gazebo_harmonic.sh script

### CMake Errors

If you encounter CMake errors:
```bash
make clean
rm -rf build/px4_sitl_default/CMakeCache.txt
```

Then try building again.

### Simulation Crashes

If the simulation crashes:
1. Check the terminal output for error messages
2. Ensure your computer meets the system requirements for Gazebo Harmonic
3. Try running with HEADLESS=1 if you're having GUI issues

## Advanced Configurations

You can modify the Phobos model or create new models:

1. Copy an existing model folder in `Tools/simulation/gz/models/`
2. Modify the model.sdf file to change the drone's physical properties
3. Add or modify sensors by editing the appropriate SDF files
4. Create a new airframe configuration in `ROMFS/px4fmu_common/init.d-posix/airframes/`
5. Add the new airframe file to CMakeLists.txt

## Additional Resources

- [PX4 Gazebo Simulation Documentation](https://docs.px4.io/main/en/simulation/gazebo.html)
- [Gazebo Harmonic Documentation](https://gazebosim.org/docs/harmonic)
