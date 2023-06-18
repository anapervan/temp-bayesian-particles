import os
import csv
import sys
import click
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# csv file format: graph_filename, entropy, nodes, agents, t_75, t_90, t_95, t_99, bits, rho, target, list
def string_to_list(row):
   """Convert the string of comma-seperated data into a list"""

   s = row[1][1:-1]  # remove row formatting
   string_data = s.split(',')
   data = [int(str) for str in string_data]

   return data


def row_to_array(M, row):
    """Convert string to adjacency matrix"""
    adjacency_arr = np.zeros((M, M))  # initialize array
    matrix_values_str = row[0][1:-1]  # remove row formatting
    row_ind = 0
    col_ind = 0
    for j in range(len(matrix_values_str)):  # step through each element of string
        if matrix_values_str[j]=='0' or matrix_values_str[j]=='1':  # if we see an element of the matrix (0 or 1)
            adjacency_arr[row_ind,col_ind] = int(matrix_values_str[j])
            col_ind += 1
        elif col_ind==M:  # if we've reached the end of a row
            row_ind += 1
            col_ind = 0

    return adjacency_arr


def parse_csv_filename(file_path):
    """Read a csv filename and output:
            M: number of nodes in the graph
            p: number or agents
            t: target location
    """
    filename = os.path.basename(file_path)

    # Read file name as list of strings, without _ or .
    f_list =  filename.split("_")
    info_list = [item.split(".")[0] for item in f_list]

    # Find indices and values of M, p, t
    node_ind = info_list.index("nodes")
    M = info_list[node_ind -1]

    agents_ind = info_list.index("agents")
    p = info_list[agents_ind -1]

    target_ind = info_list.index("target")
    t = info_list[target_ind -1]

    return int(M), int(p), int(t)


def plot_output_data(output_path):
    """Read data from csv files and plot."""

    # Search directory for csv files
    filename_list = [output_path + "/" + file for file in os.listdir(output_path) if file.endswith('.csv')]

    # Store number of nodes, number of agents, and target locations from filename
    M_list, p_list, target_list = [], [], []
    for file in filename_list:
        M, p, t = parse_csv_filename(file)
        M_list.append(M)
        p_list.append(p)
        target_list.append(t)

    plt.figure(figsize=(10,7))

    f=-1
    avg_agents_per_target = []
    agent_increments_per_target = []
    for filename in filename_list:
        M, _, _ = parse_csv_filename(filename)

        agent_count_lists = []
        f+=1
        with open(filename, newline='') as csvfile:
            filereader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            data_list = []
            line_count = -1
            row_count = 0  # initialize row counter
            for row in filereader:
                if row_count==0: # the first row is the adjacency matrix
                    A = row_to_array(M, row)
                    row_count+=1
                elif len(row)>0 and row[0]=="data":  # reformat csv data for this row
                    data = string_to_list(row)
                    data_list.append(data)
                else:
                    data = [item for item in row]
                    data_list.append(data)

                line_count += 1
                if line_count==9:
                    # Read the data
                    N = int(data_list[0][0])  # agents
                    B = int(data_list[1][0])  # bits
                    comm = str(data_list[2][0])  # commm
                    target = int(data_list[3][0])  # target
                    q = float(data_list[4][0])  # q
                    p_fp = float(data_list[5][0])  # probablilty of false positive
                    p_fn = float(data_list[6][0])  # probablilty of false negative
                    agent_count_xN = data_list[7]  # total number of agents that have detected the target
                    agent_count = [count/N for count in agent_count_xN]  # portion of agents that have detected the target
                    agent_count_lists.append(agent_count)

                    # Plot the number of successful agents at each timestep
                    num_timesteps = len(agent_count)
                    color_palette_dark = plt.cm.Set1
                    color_palette_light = plt.cm.Pastel1
                    plt.plot(range(num_timesteps), agent_count, color=color_palette_light(f), alpha=0.2, marker='.')

                    data_list=[]
                    line_count=0

        # Calculate averages for all of the trials for each target location
        total_time_per_trial = [len(trial) for trial in agent_count_lists]
        max_time_per_trial = max(total_time_per_trial)

        average_agent_count = []
        agent_increments = np.linspace(0, 1, 10)
        for agent_portion in agent_increments:  # for each number of agents
            agent_portion_timesteps = []
            for trial in agent_count_lists:  # for each trial in this simulation
                for timestep, trial_agent_portion in enumerate(trial):
                    if trial_agent_portion>=agent_portion:
                        agent_portion_timesteps.append(timestep)
                        break
            average_agent_count.append(np.mean(agent_portion_timesteps))

        avg_agents_per_target.append(average_agent_count)
        agent_increments_per_target.append(agent_increments)

    # Plot averages
    for targ in range(len(filename_list)):
        num_entries = len(avg_agents_per_target[targ])
        plt.plot(avg_agents_per_target[targ], agent_increments_per_target[targ], c=color_palette_dark(targ), marker='o')

    # Plot details
    for ind,target in enumerate(target_list):
        plt.scatter([], [], color=color_palette_dark(ind), marker='o', label=f'Target at node {target}')

    plt.xlabel("Time (Iterations)")
    plt.ylabel("Portion of successful agents")
    plt.title(f"Randomly generated graph with {M} nodes")
    plt.legend(loc='lower right')
    plt.xlim([0,max_time_per_trial+max_time_per_trial/100])

    # Plot graphs
    G = nx.from_numpy_array(A,create_using = nx.MultiDiGraph())   # generate graph from adjacency matrix

    node_color = np.array([0.6875, 0.765625, 0.8671875, 1.])  # 'lightsteelblue'
    color_map = np.tile(node_color, (M, 1))

    for ind, targ in enumerate(target_list):
        color_map[int(targ)] = color_palette_dark(ind)

    plt.figure()

    pos = nx.circular_layout(G)
    nx.draw_networkx(G, pos, arrows=True, arrowsize=15, node_size=700, node_color=color_map, with_labels=True)
    plt.axis('off')
    plt.show()

plt.show()


@click.command()
@click.option('-o', '--output_path', help='Path to the output data.')
def plot_output_data_cli(output_path):
    plot_output_data(output_path)


if __name__ == "__main__":
    plot_output_data_cli()
