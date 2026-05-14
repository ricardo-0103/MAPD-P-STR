import argparse
import datetime
import json
import os
import random
import sys
from statistics import *

import numpy
import yaml

import RoothPath
from Simulation.TP_with_recovery import TokenPassingRecovery
from Simulation.simulation_new_recovery import SimulationNewRecovery

if __name__ == '__main__':

    # Set random seed for reproducibility
    random.seed(42)
    numpy.random.seed(42)
                      
    parser = argparse.ArgumentParser()
    parser.add_argument('-m1', help='Modify Path1', default=False, type=bool)
    parser.add_argument('-m2', help='Modify Path2', default=False, type=bool)
    # --- /// STR -------------------------
    parser.add_argument('-m1_STR', help='Use Spatio-Temporal Regret for Path1',         
                        default=False, type=bool)
    parser.add_argument('-m2_STR', help='Use Spatio-Temporal Regret for Path2', 
                        default=False, type=bool)
    # --- /// Noise -------------------------
    parser.add_argument('-noise', help='Noise level added to the task probability prediction', 
                        default=0.0, type=float)
    # -----------------------------------
    parser.add_argument('-preemption_distance', help='Maximum distance to be part of the preemption zone',
                        default=0, type=int)
    parser.add_argument('-preemption_duration', help='Preemption duration',
                        default=0, type=int)
    parser.add_argument('-a_star_max_iter', help='Maximum number of states explored by the low-level algorithm',
                        default=5000, type=int)
    parser.add_argument('-tasks', help='Number of tasks',
                        default=80, type=int)
    parser.add_argument('-task_frequency', help='Maximum number of states explored by the low-level algorithm',
                        default=0.2, type=float)
    args = parser.parse_args()

    # Automatically enable the base predictive logic if STR is requested
    if args.m1_STR:
        args.m1 = True
    if args.m2_STR:
        args.m2 = True
    # ----------------------

    number_of_tasks = args.tasks
    tasks_frequency = args.task_frequency
    print("Number of tasks:", number_of_tasks)
    print("Task frequency", tasks_frequency)

    # --- Global accumulators ---
    global_avg_service_times = []
    global_agents_costs = []
    global_runtime_costs = []
    global_makespans = []

    for i in range(20):
        with open(os.path.join(RoothPath.get_root(), 'config.json'), 'r') as json_file:
            config = json.load(json_file)
        args.param = os.path.join(RoothPath.get_root(), os.path.join(config['input_path'], config['input_name']))
        args.output = os.path.join(RoothPath.get_root(), 'output.yaml')

        # Read from input file
        with open(args.param, 'r') as param_file:
            try:
                param = yaml.load(param_file, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                print(exc)

        dimensions = param['map']['dimensions']
        dimensions = (dimensions[0], dimensions[1], 10000)
        task_distribution = numpy.zeros(dimensions)
        tasks = []
        total = 0
        time = 0
        while total < number_of_tasks:
            tasks_now = numpy.random.poisson(tasks_frequency)
            # print(tasks_now)
            locations = []
            if tasks_now > number_of_tasks - total:
                tasks_now = number_of_tasks - total
            while tasks_now > 0:
                tasks_now -= 1
                locations.append(random.choice(param['map']['start_locations']))
            for loc in param['map']['start_locations']:
                if loc in locations:
                    probability = 1.0
                    task_distribution[loc[0], loc[1], time] = probability
                    total += 1
                    tasks.append(
                        {'start_time': time, 'start': loc, 'goal': random.choice(param['map']['goal_locations']),
                         'task_name': 'task' + str(total)})
                else:
                    probability = 0.0
                    task_distribution[loc[0], loc[1], time] = probability
            time += 1

        numpy.set_printoptions(threshold=sys.maxsize)

        preemption_radius = 3
        preemption_duration = 3

        with open(args.param, 'r') as param_file:
            try:
                param = yaml.load(param_file, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                print(exc)

        dimensions = param['map']['dimensions']
        obstacles = param['map']['obstacles']
        non_task_endpoints = param['map']['non_task_endpoints']
        agents = param['agents']
        param['tasks'] = tasks

        # Simulate
        simulation = SimulationNewRecovery(tasks, agents, task_distribution)
        tp = TokenPassingRecovery(agents, dimensions, obstacles, non_task_endpoints, simulation,
                                  param['map']['start_locations'],
                                  a_star_max_iter=args.a_star_max_iter, path_1_modified=args.m1,
                                  path_2_modified=args.m2,
                                  # --- ///STR arguments ---------
                                  path_1_str=args.m1_STR,
                                  path_2_str=args.m2_STR,
                                  # --- ///Noise level arguments ---------
                                  noise_level=args.noise,
                                  # ---------------------------
                                  preemption_radius=args.preemption_distance,
                                  preemption_duration=args.preemption_duration)

        initialTime = datetime.datetime.now().timestamp()
        while tp.get_completed_tasks() != len(tasks):
            simulation.time_forward(tp)
        final = datetime.datetime.now().timestamp()
        runtime = final - initialTime
        agents_cost = simulation.agents_cost
        for agent in simulation.actual_paths.keys():
            for t in range(len(simulation.actual_paths[agent]) - 1):
                for agent2 in simulation.actual_paths.keys():
                    if agent2 != agent:
                        if simulation.actual_paths[agent][t] == simulation.actual_paths[agent2][t]:
                            print("Path collision agents" + str(agent) + " " + str(agent2) + str(
                                simulation.actual_paths[agent]) + str(
                                simulation.actual_paths[agent2]) + "at time " + str(
                                t))
                        if simulation.actual_paths[agent][t] == simulation.actual_paths[agent2][t + 1] and \
                                simulation.actual_paths[agent][t + 1] == simulation.actual_paths[agent2][t]:
                            print("Switch collision " + str(agent) + " " + str(agent2) + str(
                                simulation.actual_paths[agent]) + str(
                                simulation.actual_paths[agent2]) + "at time " + str(
                                t))

        costs = []
        replans = []
        service_times = []
        sim_times = []
        algo_times = []
        cost = 0
        for path in simulation.actual_paths.values():
            cost = cost + len(path)
        output = {'schedule': simulation.actual_paths, 'cost': cost,
                  'completed_tasks_times': tp.get_completed_tasks_times(),
                  }
        with open(args.output, 'w') as output_yaml:
            yaml.safe_dump(output, output_yaml)

            cost = 0
            for path in simulation.actual_paths.values():
                cost = cost + len(path)
            costs.append(cost)
            serv_time = 0
            for task, end_time in tp.get_token()['completed_tasks_times'].items():
                serv_time = (end_time - tp.get_token()['start_tasks_times'][task])
                service_times.append(serv_time)
            print("Service time of this run: ", serv_time)
        avg_cost = mean(costs)
        avg_service_time = mean(service_times)
        print("Average service time:", avg_service_time, ". Standard deviation: ", ". Agents cost: ", agents_cost,
              ". Runtime cost:", runtime, ". Makespan:", simulation.time)
        
        # --- Save metrics for the global average ---
        global_avg_service_times.append(avg_service_time)
        global_agents_costs.append(agents_cost)
        global_runtime_costs.append(runtime)
        global_makespans.append(simulation.time)

    # --- Print global averages ---
    print("\n" + "="*80)
    print("GLOBAL AVERAGES OVER 20 RUNS:")
    print("Average service time:", mean(global_avg_service_times), 
          ". Cost of the solution per task:", mean(global_agents_costs) / args.tasks, 
          ". Runtime cost:", mean(global_runtime_costs), 
          ". Makespan:", mean(global_makespans))
    print("="*80)

    # --- Save metrics to a text file, to keep track of results ---
    # Append the results and configuration to a text file
    metrics_filename = "metrics_test.txt"
    
    # Calculate final averages
    final_service_time = mean(global_avg_service_times)
    final_agents_cost_per_task = mean(global_agents_costs) / args.tasks  # Normalize by number of tasks
    final_runtime = mean(global_runtime_costs)
    final_makespan = mean(global_makespans)

    # Open the file in 'a' (append) mode so it doesn't overwrite previous runs
    with open(metrics_filename, 'a') as f:
        # Write the configuration used
        f.write(f"CONFIG: tasks={args.tasks}, freq={args.task_frequency}, m1={args.m1}, m2={args.m2}, m1_STR={args.m1_STR}, m2_STR={args.m2_STR}, noise={args.noise}, preemption_dist={args.preemption_distance}, preemption_dur={args.preemption_duration}\n")
        # Write the resulting metrics
        f.write(f"RESULTS: Avg Service Time: {final_service_time:.2f} |Cost of the solution per task: {final_agents_cost_per_task:.2f} | Runtime: {final_runtime:.2f} | Makespan: {final_makespan:.2f}\n")
        f.write("-" * 80 + "\n")
    # --------------------------------------------------
