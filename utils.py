import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import policy_generation as policy_gen


def count_policies(num_splits,policy_bits,full_policies,S):
    """Count instances of each policy"""

    # Put full policies in useful format (list of lists of ints)
    fp = [full_policies[i].replace("s", "") for i in range(len(full_policies))]
    full_policies_list=[[int(fp[i][j]) for j in range(len(fp[i]))] for i in range(len(full_policies))]  # create list of lists of ints describing full policies

    # Create count dictionary
    count_dict = {}
    for i in range(len(full_policies)):  # for each possible combination of policies (each path)
        count_dict[full_policies[i]] = 0

    # Count number of agents with each policy
    for ind, pol in enumerate(full_policies):  # for each possible policy
        count_dict[pol] = 0  # set count for this path to 0
        for i in range(len(S)):  # for each agent
            pol_check = np.zeros(num_splits)  # reset check - policy doesn't match anywhere yet
            for k in range(num_splits):  # for each split
                if all(S[i,sum(policy_bits[0:k]):sum(policy_bits[0:k+1])]==full_policies_list[ind][sum(policy_bits[0:k]):sum(policy_bits[0:k+1])]):
                    pol_check[k]=1  # this part of the policy matches
            if sum(pol_check)==num_splits:  # every part of the policy matches
                count_dict[pol]=count_dict[pol]+1  # increment count in dict
    return count_dict


def find_target_policies(policy_paths,target_node):
    """Find which policies will bypass the target (for printing)"""

    target_policies = []

    for pol in policy_paths:
        for node in policy_paths[pol]:
            if node in target_node:
                target_policies.append(pol)
                break
    return target_policies


def communication(S, current_nodes, agent_target_count, delta, splits, policy_bits, g, transitions, node):
    """Run through communication step of algorithm"""
    indices = [n for n, x in enumerate(current_nodes) if x==node]   # find indices of other agents at the current node

    list_to_comm_with = indices.copy()

    for j in indices:
        list_to_comm_with.remove(j)  # remove agents already communicated with (and don't communicate with self)
        for k in list_to_comm_with:
            # if j and k both have success bit 0, neither will convey information
            if S[j,-1]>0 and S[k,-1]==0:  # if j has positive success bit and k has success bit 0, k will listen to j
                S[k,0:-1] = S[j,0:-1]  # communicate policy, WITH NO ERROR
                S[k,-1] = delta  # charge success bit a small amount
            elif S[k,-1]>0 and S[j,-1]==0:  # if k has positive success bit and j has success bit 0, j will listen to k
                S[j,0:-1] = S[k,0:-1]  # communicate policy, WITH NO ERROR
                S[j,-1] = delta  # charge success bit a small amount
            elif S[k,-1]>0 and S[j,-1]>0 and any(S[j,0:-1]!=S[k,0:-1]):  # if both have positive success bits and seemingly different policies
                diff_paths = policy_gen.compare_policies(S[k], S[j], splits, policy_bits, transitions, g) # ensure that the two agents have different paths through the graph
                if diff_paths==True:
                    h = np.random.choice(2, 1)  # randomly choose which agent listens
                    if h==0:  # j listens to k
                        if agent_target_count[k]==False and agent_target_count[j]==True:  # if a non target policy was communicated
                            agent_target_count[j]=False  # lose target policy count (if it had it)
                        S[j,0:-1] = S[k,0:-1]  # communicate policy, WITH NO ERROR
                        S[j,-1] = delta  # reset success bit (but give them a lap or two to find the target)
                    else:  # k listens to j
                        if agent_target_count[j]==False and agent_target_count[k]==True:  # if a non target policy was communicated
                            agent_target_count[k]=False  # lose target policy count (if it had it)
                        S[k,0:-1] = S[j,0:-1]  # communicate policy, WITH NO ERROR
                        S[k,-1] = delta  # reset success bit (but give them a lap or two to find the target)
    output = [S, agent_target_count, indices]

    return output


def chance_of_target(g, policy_paths, target):
    """Calculate q, the chance of finding the target based on the graph and target node"""
    target_paths=[]
    for pol in policy_paths:
        path=[]
        for node in policy_paths[pol]:
            path.append(node)
            if node==target and path not in target_paths:
                target_paths.append(path)
                break
            elif int(node)>=int(target):
                break

    q=0 # chance of visiting the target node
    for path in target_paths:
        prob = 1 # chance of visiting the next node along this path
        for node in path:
            if node != target:
                out_degree = len(g[node])
                prob = prob * (1/out_degree)
        q += prob

    return q
