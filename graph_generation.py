import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


def create_graph(N):  # N = number of nodes in a random graph
    """Create a random Circulative Network """

    # Parameters
    outgoing_threshold = 5  # max number of outgoing edges

    # Generate graph
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

    G = nx.from_numpy_array(A, create_using = nx.MultiDiGraph())  # generate graph from adjacency matrix
    E = G.edges  # find edges of generated graph

    # Find entropy of graph
    h=0
    for i in A:
        s = np.sum(i)
        h = h+s*np.log(s)

    # Plot graph
    plt.clf()
    pos = nx.circular_layout(G)  # another possible layout: nx.random_layout(G)
    nx.draw_networkx(G, pos,arrows=True,arrowsize=10,node_size=1000)
    plt.axis('off')
    plt.show()

    return(G,h,A)
