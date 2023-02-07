import math
import itertools
import numpy as np

def analyze_graph(g):
    """
    Find the number of bits required and the diverging nodes in the graph.

    Outputs:
        B = int, number of bits
        split_dict = dict {str: int}, keys are index of diverging nodes and
                     values are number of outgoing paths
        splits = list, indices of diverging nodes
    """
    # Loop through nodes
    split_dict = {}
    for node in range(len(g)):  # for each node
        num_edges = len(g[str(node)])  # find the number of outgoing edges
        if num_edges>1:  # if a node has more one than outgoing edge, it is a split
            split_dict[str(node)]=num_edges  # store each split in the split dictionary
    splits = list(split_dict.keys())  # store indices of splits in list

    B = 1  # 1 success bit required

    for node in split_dict:
        B = math.ceil(math.log(split_dict[str(node)],2)) + B  # find number of bits required to solve given graph
    print(B,"bits are required to solve this graph.")

    return split_dict, splits, B


def define_policy_structure(split_dict):
    """
    Takes in the number of bits and the diverging nodes, calculates the policy
    structure for this network, and displays it.

    Output:
        policy_bits = list, each element is the number of policy bits that hold
                      the instructions for that diverging node
    """

    policy_bits = []
    policy_structure = []
    splits = list(split_dict.keys())  # store indices of splits in list

    # Calculate number of policy bits needed at each diverging nodes
    for i in splits:
        num_policy_bits = math.ceil(math.log(split_dict[i],2)) # number of policy bits required for this split
        for p in list(range(num_policy_bits)):
            policy_structure.append("P") # append P (policy bit) for policy bits required for each split
        policy_structure.append("-")
        policy_bits.append(num_policy_bits)
    policy_structure.append("S")
    policy_structure =' '.join(policy_structure)

    # Display policy structure
    print("Policy Structure:",policy_structure)

    return policy_bits


def assign_policies_to_nodes(split_dict, policy_bits, g):
    """
    Assign policies to graph transitions

    Outputs:
        transitions: dict {tuple(str,str): str}, a dictionary with key (node_i, node_i+1) and value policy that goes from the node_i to node_i+1
        node_policies list of lists, a list of polices outgoing from each node [[list of policies out from node 0], ... , [list of policies out from node n], ...]
    """
    # Initialize
    splits = list(split_dict.keys())  # store indices of splits in list
    num_splits = len(splits)

    transitions = {}
    temp_string = [[] for i in list(range(num_splits))]
    node_policies = [[] for i in list(range(num_splits))]

    # Calculate max number of branches in graph
    max_branches = max(split_dict.values())

    # Find policies for each node
    for ind, node in enumerate(split_dict):  # for each split
        null_policy = '0'*policy_bits[ind]
        for branch in list(range(split_dict[node])):  # for each branch in that split
            s = bin(branch)  # binary string
            ss=s.replace('0b','')  # without '0b'
            while len(ss)<policy_bits[ind]:  # add '0' to beginning until string is correct length for policy
                ss = '0'+ss

            # Store policies for each node
            node_policies[ind].append(ss)
            transitions[(str(node),g[str(node)][branch])]=ss  #

    return transitions, node_policies


def find_full_policies(node_policies, num_splits):
    """Find full policies for the whole graph, aka all possible policies"""

    full_policies=[]
    node_policy_combinations = list(itertools.product(*node_policies))  # find each combination of node policies

    for node_policies in node_policy_combinations:  # for each policy
        policy = ''
        for j in range(num_splits):
            policy = policy + node_policies[j]  # additively construct a string
        policy = policy+"s"
        full_policies.append(policy)  # save to list

    return full_policies


def find_node_paths(full_policies, splits, g, transitions, policy_bits):
    """Find sequence of nodes that each policy passes through"""

    policy_paths = {}
    for full_pol in full_policies:
        temp_path = ['0']
        node_1 = '0'  # start at heart node, where all policies pass
        node_2 = 'A'  # random, nonzero number to initialize
        while node_2 != '0':
            if node_1 in splits:  # if at a split
                ind = splits.index(node_1)
                for node_2 in g[node_1]:  # find which node this policy goes to next
                    if transitions[node_1,node_2] == full_pol[sum(policy_bits[0:ind]):sum(policy_bits[0:ind+1])]:
                        break
            else:  # if not at a split
                node_2 = g[node_1][0]  # continue on to the only possible next node
            temp_path.append(node_2)
            node_1 = node_2
        policy_paths[full_pol] = temp_path

    return policy_paths


def generate_random_policy(Si, num_splits, node_policies, policy_bits):
    """Generate a random policy"""

    for j in range(num_splits):  # for each node / set of policy bits
        rand_pol = np.random.choice(node_policies[j])   # random policy from each split (in string format)
        rand_pol_list = [int(bit) for bit in rand_pol]  # convert to list
        Si[sum(policy_bits[0:j]):sum(policy_bits[0:j+1])] = rand_pol_list  # assign policies to agent

    return Si


def compare_policies(pol_1, pol_2, splits, policy_bits, transitions, g):
    """
    Compare two policies to see if they exhibit the same behavior in the graph,
    or if they are in fact different policies

    Output:
        diff_policies=True, if the policies take different paths through the graph
    """

    old_node = 'X'  # place holder to enter while loop
    diff_policies = False  # place holder to enter while loop
    new_node_A = '0'  # starting node

    while diff_policies==False and old_node!='0':
        old_node = new_node_A
        if old_node in splits:  # if old node is a split
            ind = splits.index(old_node)  # find out which split

            # Find policies for this split
            pol_1_bits = pol_1[sum(policy_bits[0:ind]):sum(policy_bits[0:ind+1])]
            pol_2_bits = pol_2[sum(policy_bits[0:ind]):sum(policy_bits[0:ind+1])]

            # Cnvert to a list of strings and reformat
            pol_1_list = [str(int(s)) for s in pol_1_bits]
            pol_1_str = ''.join(pol_1_list)  # reformat the string

            pol_2_list = [str(int(s)) for s in pol_2_bits]
            pol_2_str = ''.join(pol_2_list)

            # Find which node(s) each policy goes to next
            for new_node_A in g[old_node]:
                if transitions[old_node, new_node_A] == pol_1_str:
                     break
            for new_node_B in g[old_node]:
                if transitions[old_node, new_node_B] == pol_2_str:
                     break
        else:  # just step to the only possible next node
            new_node_A = g[old_node]
            new_node_B = g[old_node]

        # Check if future nodes are the same
        if new_node_A == new_node_B:
            diff_policies = False
        else:
            diff_policies = True

    return diff_policies
