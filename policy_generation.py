import math
import itertools
import numpy as np

def analyze_graph(G, g):
    """Find the number of bits required and the diverging nodes in the graph.

    Outputs:
        B = int, number of bits
        P = dict {str: int}, keys are index of diverging nodes and values are number of outgoing paths
        splits = list, indices of diverging nodes"""

    init_dict = False  # have not initialized dictionary yet
    splits = []
    split_branches = {}
    for node in G.nodes:
        num_edges = len(g[str(node)])  # find number of out going edges for each node
        if num_edges>1:  # if a node has more than outgoing edge, it is a split
            if init_dict==False:  # start a dictionary if.when the first split is found
                P={str(node):[num_edges]}
                init_dict=True
            P[str(node)]=num_edges  # store each split in the split dictionary
            splits.append(str(node))  # store indices of splits in list
    B = 1  # 1 success bit required

    for split in P:
        split_branches[split]=g[split]  # add branches to split_branches dictionary
        B = math.ceil(math.log(P[str(split)],2)) + B  # find number of bits required to solve given graph
    print(B,"bits are required to solve this graph.")

    return P, B, splits


def define_policy_structure(P, B, splits):
    """ Takes in the number of bits and the diverging nodes

    Output:
        policy_bits = list, each element is the number of policy bits that hold the instructions for that diverging node """

    policy_structure = []
    policy_bits = []
    for i in splits:
        num_p = math.ceil(math.log(P[i],2)) # number of policy bits required for this split
        for p in list(range(num_p)):
            policy_structure.append("P") # append P (policy bit) for policy bits required for each split
        policy_structure.append("-")
        policy_bits.append(num_p)
    policy_structure.append("S")
    policy_structure =' '.join(policy_structure)
    print("Policy Structure:",policy_structure)

    return policy_bits


def assign_policies_to_nodes(P, splits, policy_bits, g):
    """Assign policies to graph transitions

    Outputs:
        transitions: dict {tuple(str,str): str}, a dictionary with key (node_i, node_i+1) and value policy that goes from the node_i to node_i+1
        node_policies list of lists, a list of polices outgoing from each node [[list of policies out from node 0], ... , [list of policies out from node n], ...]
        """

    # Find max number of branches in graph
    max_branches = P[splits[0]]
    for i in splits:
        if P[i] > max_branches:
            max_branches = P[i]

    # Find policies for each node
    num_splits=len(splits)
    node_policies = [[] for i in list(range(num_splits))]  # initialize lists
    temp_string = [[] for i in list(range(num_splits))]
    transitions = {}
    for ind, node in enumerate(P):  # for each split
        null_policy = '0'*policy_bits[ind]
        for branch in list(range(P[node])):  # for each branch in that split
            s = bin(branch)  # binary string
            ss=s.replace('0b','')  # without '0b'
            while len(ss)<policy_bits[ind]:  # add '0' to beginning until string is correct length for policy
                ss = '0'+ss
            node_policies[ind].append(ss)
            transitions[(str(node),g[str(node)][branch])]=ss  # add to transitions dictionary
    print("Transitions:")
    for element in transitions:
        print(element, transitions[element])
    return transitions, node_policies


def generate_random_policy(Si,num_splits,node_policies,policy_bits):
    """Generate a random policy"""
    for j in range(num_splits):  # for each set of policy bits
        rand_pol = np.random.choice(node_policies[j])   # random policy from each split (in string format)
        rand_pol_list = [int(rand_pol[k]) for k in range(len(rand_pol))]  # convert to list
        Si[sum(policy_bits[0:j]):sum(policy_bits[0:j+1])] = rand_pol_list  # assign policies to syncell
    return Si


def find_full_policies(node_policies, num_splits):
    """Find full policies for the whole graph, aka all possible policies"""

    fp = list(itertools.product(*node_policies))  # find each combination of node policies
    full_policies=[]
    for p in fp:  # for each policy
        temp = ''
        for j in range(num_splits):
            temp=temp+p[j]  # additevly construct a string
        temp=temp+"s"
        full_policies.append(temp)  # save to list

    return full_policies


def find_node_paths(full_policies,splits,g,transitions,policy_bits):
    """Find sequence of nodes that each policy passes through"""

    policy_paths = {}
    for full_pol in full_policies:
        temp_path = ['0']
        node_1='0'  # start at 0, where all policies pass
        node_2='A'  # random, nonzero number to initialize
        while node_2 != '0':
            if node_1 in splits:  # if at a split
                ind = splits.index(node_1)
                for node_2 in g[node_1]:  # find which node this policy goes to next
                     if transitions[node_1,node_2] == full_pol[sum(policy_bits[0:ind]):sum(policy_bits[0:ind+1])]:
                         break
            else:  # if not at a split
                node_2=g[node_1][0]  # continue on to only possible next node
            temp_path.append(node_2)
            node_1=node_2
        policy_paths[full_pol]=temp_path

    return policy_paths


def compare_policies(pol_1, pol_2, splits, policy_bits, transitions, g):
    """Compare two policies to see if they exhibit the same behavior in the graph,
    or if they are in fact different policies

    Output:
        diff_policies=True, if the policies take different paths through the graph"""

    old_node = '1'
    new_node_1 = '0'
    diff_policies = False

    while diff_policies==False and old_node!='0':
        old_node = new_node_1
        if old_node in splits:  # if old node was a split
            ind = splits.index(old_node)  # find out which split
            pol_1_bits = pol_1[sum(policy_bits[0:ind]):sum(policy_bits[0:ind+1])]  # find policy for this split
            pol_2_bits = pol_2[sum(policy_bits[0:ind]):sum(policy_bits[0:ind+1])]
            pol_1_list = [str(int(s)) for s in pol_1_bits]  # convert to a list of strings
            pol_2_list = [str(int(s)) for s in pol_2_bits]
            pol_1_str = ''.join(pol_1_list)  # reformat the string
            pol_2_str = ''.join(pol_2_list)
            for new_node_1 in g[old_node]:  # find which node policy 1 goes to next
                if transitions[old_node,new_node_1] == pol_1_str:
                     break
            for new_node_2 in g[old_node]:  # find which node policy 3 goes to next
                if transitions[old_node,new_node_2] == pol_2_str:
                     break
        else:
            new_node_1 = g[old_node]
            new_node_2 = g[old_node]

        if new_node_1 == new_node_2:
            diff_policies=False
        else:
            diff_policies=True

    return diff_policies
