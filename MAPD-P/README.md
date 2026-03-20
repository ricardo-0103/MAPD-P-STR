# Multi-Agent Pickup and Delivery with Task Probability Distribution (MAPD-P)

<p align="justify">
This repo contains implementations of various algorithms used to solve the problem of Multi-Agent Pickup and Delivery based on Token Passing and using a task probability distribution.
The implementation of base token passing is based on this implementation: https://github.com/Lodz97/Multi-Agent_Pickup_and_Delivery.
</p>

### Root folder

This is the main directory where everything starts.

- _**demo.py**_: This is the main entry point. It orchestrates the entire process: it loads the map, generates random tasks based on a probability distribution, initializes the agents, runs the Token Passing simulation until all tasks are finished, and finally prints the performance metrics to your terminal.

- _**config.json**_: A simple configuration file that tells demo.py exactly which folder (input_path) and which map file (input_name) to load for the simulation.

- _**README.md**_: The basic documentation explaining that this repository implements MAPD based on Token Passing with a task probability distribution.

### Environments/ & Benchmarks/ Folders (The Maps)

These folders contain the physical layouts where the simulation takes place.

- _**input_warehouse_big_random.yaml (and other .yaml files)**_: These define the grid environment. They list the dimensions of the warehouse, the exact (x, y) coordinates of all obstacles, where tasks can start (start_locations), where tasks must be delivered (goal_locations), and where the agents start.

- _**Benchmarks/**_: Usually contains standard text-based ASCII maps from academic pathfinding databases (like the den308d.map file).

### Utils/ Folder (The Helpers)

Contains standalone helper scripts that you run before the main simulation to prepare your data.

- _**map_converter.py**_: This takes raw ASCII maps from the Benchmarks folder, randomly sprinkles start/goal locations and agents across the free space, and converts them into .yaml files in the Environments folder so demo.py can read them.

- _**print_envs.py**_: This takes the .yaml file required inside the Environments folder and make an image showing the position of the agents, the obstacles, and the tasks.

### Simulation/ Folder (The Brains)

This is where the actual logic of the MAPD algorithms lives. demo.py calls these scripts to do the heavy lifting.

- _**simulation_new_recovery.py**_: Think of this as the "physics engine" or the "clock". It keeps track of time moving forward, updates the agents' positions at each timestep, checks if tasks have appeared according to the probability distribution, and logs everything to save to the output file later.

- _**TP_with_recovery.py**_: This implements the Token Passing algorithm. In Token Passing, a virtual "token" containing the list of all available tasks and the paths of all agents is passed from agent to agent. When an agent gets the token, it claims a task and calculates its route. This script also contains the modified logic to exploit task probability distributions to improve efficiency.

- _**markov_chains.py**_: This file likely handles the math behind the task probability distributions mentioned in the paper, predicting where tasks are most likely to appear next.

### Simulation/CBS/ Subfolder (The Navigators)

While TP_with_recovery.py decides which agent takes which task, the scripts in the CBS folder figure out how the agent physically drives there without crashing into walls or other robots.

- _**a_star.py**_: A standard low-level pathfinding algorithm. It calculates the shortest path from point A to point B on a grid.

- _**cbs.py**_: Stands for Conflict-Based Search. When a_star.py calculates routes for multiple robots, they might cross paths at the same time (a collision). CBS detects these conflicts and forces the a_star.py algorithm to recalculate a slightly longer route for one of the robots to avoid the crash.
