import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

paths = -1 # global variable
max_length = 0  # global variable
def dfs(visited, graph, node):
    """Modified depth first search algorithm.
    Returns the number of cycles (paths) in the graph
    and the maximum cycle length in the graph"""

    global paths, max_length
    if node == '0':  # if we've returned to the heart node
        paths = paths+1  # count an additional path
    if node not in visited:  # if this is a new node
        visited.append(node)  # append the node to the list of visited nodes
        for neighbor in graph[node]:  # for each downstream node
            dfs(visited, graph, neighbor)
            max_length = max(max_length, len(visited))
            visited = ['0']
    return paths, max_length


def create_graph(N):  # N = number of nodes in a random graph
    """Create a random Circulative Network"""

    # Parameters
    outgoing_threshold = 5  # max number of outgoing edges
    c = 3  # constant for ensuring max cycle length <= c * log(N)
    max_cycle_length = float('inf')  # initialize variable for while loop
    g = {}  # initialize graph dictionary

    # Generate graph
    while max_cycle_length >= c*np.log(N):  # ensure that the maximum cycle length is less than the threshold
        # Intialize variables
        global paths, max_length
        paths = -1
        max_length = 0

        # Define adjacency matrix
        A_0 = np.random.choice([0,1], p=[(1-2/N), (2/N)],size=(N,N))  # start with randomly generated adjacency matrix
        A = np.triu(A_0,1)  # make the matrix upper trianglar so the graph flows "forward"
        A[:,0]=A_0[:,0]   # but allow nodes to return to initial node (0)

        for i in range(N):  # for each row (node) in the matrix (graph)
            A[i,i]=0  # remove self transitions (simulated seperately)

            # No dead ends
            if sum(A[i])==0:
                if i==N-1:  # if the last node is a dead end
                    nodes_ahead = [0]  # it can only point to node 0
                else:
                    nodes_ahead = [(N-1)-j for j in reversed(range(0,(N-1)-i))]
                A[i,np.random.choice(nodes_ahead)]=1  # step to one random node ahead

            # No dead "beginnings"
            if sum(A[:,i])==0:
                if i==0:  # if the first node is a dead beginning
                    nodes_behind = [j for j in range(0,N)]  # any node can point to it
                else:
                    nodes_behind = [j for j in range(0,i)]
                A[np.random.choice(nodes_behind),i]=1  # step from at least one random node behind

            # Fewer than outgoing_threshold outgoing edges
            out_inds = np.where(A[i] == 1)  # number of outgoing edges
            while len(out_inds[0])>outgoing_threshold:
                A[i][np.random.choice(out_inds[0])]=0  # remove one random connection
                out_inds = np.where(A[i] == 1)

        # Create dictionary format of graph
        for i in range(N):  # for each row (node) in the matrix (graph)
            g[str(i)] = [str(j) for j in range(N) if A[i,j]==1]  # save outgoing nodes

        # Max cycle length is less than c*log(N)
        paths, max_cycle_length = dfs([], g, '0')  # determine number of possible paths in graph

    G = nx.from_numpy_array(A, create_using = nx.MultiDiGraph())  # generate graph from adjacency matrix
    E = G.edges  # find edges of generated graph


    # Find entropy of graph
    h=0
    for i in A:
        s = np.sum(i)
        h = h+s*np.log(s)

    # # Plot graph
    # plt.clf()
    # pos = nx.circular_layout(G)  # another possible layout: nx.random_layout(G)
    # nx.draw_networkx(G, pos,arrows=True,arrowsize=10,node_size=1000)
    # plt.axis('off')
    # plt.show()

    return(G, g, h, A, paths, max_cycle_length)
