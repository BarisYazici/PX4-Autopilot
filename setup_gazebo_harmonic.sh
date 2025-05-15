#!/bin/bash
# ==================================================================
# Gazebo Harmonic Setup Script for PX4 SITL Simulation
# ==================================================================
# This script sets up the necessary environment variables for PX4
# to detect and use Gazebo Harmonic (version 8) for simulation.
# ==================================================================

# Set the Gazebo distro to Harmonic
export GZ_DISTRO=harmonic
export GZ_VERSION=harmonic

# Set the Gazebo resource paths for version 8
export GZ_SIM_RESOURCE_PATH=/usr/share/gz/gz-sim8:/usr/share/gz/gz-sim-8:$GZ_SIM_RESOURCE_PATH
export GZ_SIM_SYSTEM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gz-sim-8/plugins:/usr/lib/x86_64-linux-gnu/gz-sim8/plugins:$GZ_SIM_SYSTEM_PLUGIN_PATH

# Set additional required paths for CMake to find dependencies
export CMAKE_PREFIX_PATH=/usr/lib/x86_64-linux-gnu/cmake/gz-transport13:$CMAKE_PREFIX_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
export PKG_CONFIG_PATH=/usr/lib/x86_64-linux-gnu/pkgconfig:$PKG_CONFIG_PATH

# Path to PX4 GZ plugins and resources
export PX4_GZ_MODELS=$PWD/Tools/simulation/gz/models
export PX4_GZ_WORLDS=$PWD/Tools/simulation/gz/worlds
export PX4_GZ_PLUGINS=$PWD/build/px4_sitl_default/src/modules/simulation/gz_plugins
export PX4_GZ_SERVER_CONFIG=$PWD/src/modules/simulation/gz_bridge/server.config

# Check if build directory exists, if not create it
if [ ! -d "build" ]; then
    mkdir -p build
fi

# Clean CMake cache to force re-detection of Gazebo dependencies
if [ -f "build/px4_sitl_default/CMakeCache.txt" ]; then
    rm build/px4_sitl_default/CMakeCache.txt
fi

echo "==================================================================="
echo "Gazebo Harmonic environment set up successfully."
echo ""
echo "You can run simulation using commands like:"
echo "  make px4_sitl_default gz_x500"
echo "  make px4_sitl_default gz_x500_depth"
echo "  make px4_sitl_default 4023_gz_phobos"
echo ""
echo "For headless simulation (no GUI):"
echo "  HEADLESS=1 make px4_sitl_default gz_x500"
echo "==================================================================="
