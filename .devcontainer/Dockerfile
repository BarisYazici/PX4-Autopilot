# Start from the PX4 base image as specified in devcontainer.json
FROM px4io/px4-dev-simulation-jammy:latest

# Install sudo and necessary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    wget \
    lsb-release \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add Gazebo repositories and install Gazebo Harmonic
RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    gz-harmonic \
    && rm -rf /var/lib/apt/lists/*

# Add user to sudo group
RUN adduser user sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Make sure user can access GPU
RUN usermod -aG video,render user

# Switch back to user
USER user
WORKDIR /workspaces/PX4-Autopilot

# Create script to set up environment variables
RUN mkdir -p ~/.bashrc.d && \
    echo '#!/bin/bash\n\n# Gazebo environment setup\nexport PATH="/usr/bin:$PATH"\n\n# Gazebo environment variables\nexport GZ_VERSION=harmonic\nexport GZ_SIM_SYSTEM_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/gz-sim-7/plugins:/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)/gz-sim-7/plugins"\nexport GZ_SIM_RESOURCE_PATH="/usr/share/gz/gz-sim7:/usr/share/gz/gz-sim-7"\nexport GAZEBO_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/gazebo-11/plugins:${GAZEBO_PLUGIN_PATH}"\nexport LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu/gazebo-11/plugins:${LD_LIBRARY_PATH}"\n' > ~/.bashrc.d/gazebo.sh && \
    chmod +x ~/.bashrc.d/gazebo.sh

# Add to bashrc if not already there
RUN grep -q "bashrc.d" ~/.bashrc || echo '\n# Source gazebo environment variables\nif [ -d ~/.bashrc.d ]; then\n  for file in ~/.bashrc.d/*.sh; do\n    if [ -r "$file" ]; then\n      source "$file"\n    fi\n  done\nfi' >> ~/.bashrc
