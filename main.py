import csv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

import utils as utils
import graph_generation as graph_gen
import policy_generation as policy_gen


def calculate_parameters(g, M, policy_paths, num_policies, target):
    """Calculate q (the probability of passing by the target) and N (the number of agents required)"""

    target_policies = utils.find_target_policies(policy_paths,[target])  # find which policies will bypass the target (not used in simulation, just to print)
    q = utils.chance_of_target(g, policy_paths, target)  # probability of passing by the target
    print(f"Chance of finding the target: {q}")

    gamma = 1.
    N = int((gamma/q) + np.log2(M)**2)
    print(f"Number of agents required for this graph: {N}")

    return q, N


def record_results_csv(M, A, N, B, comm, target, q, z_fp, z_fn, target_count, first_trial):
    """Write output to a csv file"""

    filename = "20_nodes/comm/graph_1_rand_" + str(M) + "_nodes_" + str(N) + "_agents_" + str(target) + "_target"  # csv filename with parameters

    with open(filename+'.csv', 'a', newline='') as csvfile:  # save data
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        if first_trial==True:
            writer.writerow([str(A),  "graph"])
        writer.writerow([str(N),  "agents"])
        writer.writerow([str(B), "bits"])
        writer.writerow([str(comm), "comm"])
        writer.writerow([str(target), "target"])
        writer.writerow([str(q), "q"])
        writer.writerow([str(z_fp), "p_fp"])
        writer.writerow([str(z_fn), "p_fn"])
        writer.writerow(["data",target_count])
        writer.writerow([])


def run_simulation(M, G, g, A, P, B, splits, policy_bits, transitions, node_policies, full_policies, policy_paths, paths, target, q, N, first_trial):
    # Parameters
    comm = True  # agent communication (true = bayesian particle algorithm. false = independent agents searching)
    z_fp = 0.0  # probability of false positive
    z_fn = 0.0  # probability of false negative
    z_bh = 0.000  # probability of falling into black hole/getting lost
    L = 3*12  # number of steps without detecting target before success bit resets
    delta = 2*12  # the amount the success bit "charges"

    target_pol_count = 0
    agent_target_count = [False]*N
    sbi = B-1  # success bit index
    num_splits = len(splits)

    # Initialize agents
    S = np.zeros((N,B),dtype=int)  # array to keep track of agents' polices and successes. each row represents an agent
    for i in range(N):  # for each agent
        S[i] = policy_gen.generate_random_policy(S[i],num_splits,node_policies,policy_bits)  # generate a random policy
    current_nodes = ['0']*N  # list to keep track of each agents' location. start every agent at node '0'

    # Count agents
    t_list = []  # list to store t values (time steps)
    target_count = []  # list to store number of agents that have policies that pass the target
    blackhole_count = []  # list to store the number of agents that have been lost

    count_dict = utils.count_policies(num_splits,policy_bits,full_policies,S)  # count how many agents have each policy
    count_dict_hist = {}
    for c in count_dict:  # for each possible combination of policies (each path)
        count_dict_hist[c] = []

    # Simulate Bayesian Particles
    while target_pol_count < 0.98*N:

        old_nodes = current_nodes.copy()

        # Policy Execution
        for i in range(N):  # each agent executes path, and may or may not detect the target
            if S[i,-1]!=1000:  # if agent is not lost, execute:
                old_node = current_nodes[i]  # record old node

                # Check if agent is at target node
                if current_nodes[i]==target:
                    target_detected=True  # if currently at target node, target detected is True
                else:
                    target_detected=False

                if target_detected:  # if agent has the target policy
                    S[i,sbi] = np.random.choice([S[i,sbi],1], 1, p=[z_fn, 1-z_fn])  # SUCCESS (chance of false negative = leave success bit the same)
                    if S[i,sbi]==1:
                        agent_target_count[i]=True  # if at target node AND true positive detection, count agent
                else:  # if not currently at target node
                    # Count another time step since agent has seen target
                    if S[i,sbi]>0:  # if success bit is ON
                        S[i,sbi]=S[i,sbi]+1  # add timer count (chemical decay)
                    S[i,sbi] = np.random.choice([S[i,sbi],1], 1, p=[1-z_fp, z_fp])  # chance of false positive

                # If unsuccessful and at heart node, generate new policy
                if S[i,sbi]==0:  # if unsuccessful
                    agent_target_count[i]=False  # lose target policy count (if it had it)
                    if current_nodes[i] == '0':
                        S[i] = policy_gen.generate_random_policy(S[i],num_splits,node_policies,policy_bits)  # generate new random policy

                # Step forward according to your policy
                if old_node in splits:  # if old node was a split
                    ind = splits.index(old_node)  # find out which split
                    S_pol = S[i,sum(policy_bits[0:ind]):sum(policy_bits[0:ind+1])]
                    S_pol_list = [str(int(s)) for s in S_pol]
                    S_pol_str = ''.join(S_pol_list)
                    for new_node in g[old_node]:  # find which node this policy goes to next
                        if transitions[old_node,new_node] == S_pol_str:
                             break
                else:  # if old node was not a split
                    new_node = g[old_node][0]  # just step forward to the only possible node

                # Chance of self loop (depending on number of outgoing branches)
                self_loop = np.random.choice(len(g[old_node])+1)==1  # some chance of not moving forward, depending on nmber of outgoing branches
                if self_loop:
                    current_nodes[i] = old_node  # stay at old node
                else:
                    current_nodes[i] = new_node  # move forward to new node

                # If agent has been through L loops and not detected the target, change success bit to 0
                if S[i,sbi]>=L:
                    S[i,sbi]=0
                    agent_target_count[i]=False

                # Get "lost" aka enter black hole
                S[i,sbi] = np.random.choice([S[i,sbi],100], 1, p=[1-z_bh, z_bh])  # chance of BLACK HOLE

            occupied_nodes = list(set([i for i in current_nodes if current_nodes.count(i)>1]))  # find nodes occupied by more than one agent

            if comm:
                for node in occupied_nodes:
                    output = utils.communication(S, current_nodes, agent_target_count, delta, splits, policy_bits, g, transitions, node)
                    S_out, target_count_out, indices = output
                    for j in indices:
                        S[j] = S_out[j]
                        agent_target_count[j] = target_count_out[j]

        # Count Policies
        target_pol_count = sum(agent_target_count)
        target_count.append(target_pol_count)  # number of successful agents at this time
    print(f"Converged in {len(target_count)} steps")

    # Record results to a csv file
    record_results_csv(M, A, N, B, comm, target, q, z_fp, z_fn, target_count, first_trial)



def main():
    """Function to generate a random graph and target location, and simulate agents finding the target"""

    # Parameters
    M = 20  # number of nodes in randomly generated graph
    num_trials = 100  # number of times to run this simulation
    num_targets = 5

    # Generate graph
    G, g, entropy, A, paths, max_cycle_length = graph_gen.create_graph(M)
    print(f"There are {paths} paths in this graph. \nThe maximum cycle length is {max_cycle_length}.")  # number of paths counted

    # Generate Policies
    split_dict, splits, B = policy_gen.analyze_graph(g)  # analyze graph
    policy_bits = policy_gen.define_policy_structure(split_dict)  # find policy structure
    transitions, node_policies = policy_gen.assign_policies_to_nodes(split_dict, policy_bits, g)  # assign policies to graph transitions
    full_policies = policy_gen.find_full_policies(node_policies, len(splits))  # find full list of all possible policies
    policy_paths = policy_gen.find_node_paths(full_policies, splits, g, transitions, policy_bits)  # find sequence of nodes that each policy passes through


    # # Randomly place the target at a (non-heart) node in the graph
    # target = str(np.random.choice(np.arange(1,M-1)))
    # print(f"\nTarget at {target}")

    # Run simulation
    # q, N = calculate_parameters(g,M,policy_paths,len(full_policies),target)
    # first_trial = True
    # for _ in range(num_trials):
    #     run_simulation(M, G, g, A, split_dict, B, splits, policy_bits, transitions, node_policies, full_policies, policy_paths, paths, target, q, N, first_trial)
    #     first_trial = False


    target_list = []
    for ttt in range(num_targets):
        target = str(np.random.choice(np.arange(1,M-1)))
        while target in target_list:
            target = str(np.random.choice(np.arange(1,M-1)))
        target_list.append(target)
        print(f"target_list {target_list}")
        q, N = calculate_parameters(g, M, policy_paths, len(full_policies), target)
        first_trial = True
        for _ in range(num_trials):
            run_simulation(M, G, g, A, split_dict, B, splits, policy_bits, transitions, node_policies, full_policies, policy_paths, paths, target, q, N, first_trial)
            first_trial = False


if __name__ == "__main__":
    main()
