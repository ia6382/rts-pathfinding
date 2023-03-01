import numpy as np
import pathfinder
from queue import Queue

class Cluster:
    def __init__(self, x1, x2, y1, y2, E):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.E = E


class Map: #SoA (structure of arrays)
    # because of tcod Point object (x = column index, y = row index), we store the map as a transposed array (columns x rows)

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.char = np.full((width, height), ".")
        self.walkable = np.full((width, height), True, bool)
        self.G = None
        self.C = None

    def read_map(self, file):
        f = open(file, "r")
        world_map = f.read()
        f.close()
        world_map = world_map.split("\n")
        world_map = np.array(list(map(lambda x: list(x), world_map)))        

        width = len(world_map[0])
        height = len(world_map)

        walkable = np.zeros((height, width))
        walkable[:] = world_map[:] == "." 
        #walkable = [list(map(lambda y: self._is_walkable(y), x)) for x in world_map]

        self.width = width
        self.height = height
        self.char = world_map.transpose()
        self.walkable = walkable.transpose()
        self.G = None
        self.C = None

    def _is_walkable(self, char):
        if char == ".":
            return True
        else:
            return False

    def build_hierahical_graph(self, c_dim):
        """
        c_width = dimension of cluster
        """
        G = {} #graph - a dictionary of nodes(lists that contain edges to other nodes)

        #split map into clusters
        m = int(self.width/c_dim)
        n = int(self.height/c_dim)

        C = {}
        for i in range(m):
            for j in range(n):
                #cluster = self.walkable[i*c_dim: i*c_dim+c_dim, j*c_dim:j*c_dim+c_dim]
                C[(i,j)] = Cluster(i*c_dim, i*c_dim+c_dim-1, j*c_dim, j*c_dim+c_dim-1, [])

        self.C = C

        #find entrances between clusters
        for i in range(m):
            for j in range(n):
                c1 = C[(i,j)]

                if i+1 < m: #bottom neigbour
                    c2 = C[(i+1,j)]  

                    b1 = self.walkable[c1.x2, c1.y1:c1.y2+1] #bottom row
                    b2 = self.walkable[c2.x1, c2.y1:c2.y2+1] #top row

                    transitions = self._find_transitions(b1, b2, 6)

                    for t in transitions:
                        t1 = (c1.x2, c1.y1 + t)
                        if not(t1 in c1.E):
                            c1.E.append(t1)
                            
                        t2 = (c2.x1, c2.y1 + t)
                        if not(t2 in c2.E):
                            c2.E.append(t2)

                        #add inter edges between clusters
                        if t1 in G:
                            G[t1] += [(t2, 1)]
                        else:
                            G[t1] = [(t2, 1)]
                        if t2 in G:
                            G[t2] += [(t1, 1)]
                        else:
                            G[t2] = [(t1, 1)]

                if j+1 < n: 
                    c2 = C[(i,j+1)]  #right neighbour

                    b1 = self.walkable[c1.x1:c1.x2+1, c1.y2] #right column
                    b2 = self.walkable[c2.x1:c2.x2+1, c2.y1] #left column

                    transitions = self._find_transitions(b1, b2, 6)

                    for t in transitions:
                        t1 = (c1.x1 + t, c1.y2)
                        if not(t1 in c1.E):
                            c1.E.append(t1)
                        t2 = (c2.x1 + t, c2.y1)
                        if not(t2 in c2.E):
                            c2.E.append(t2)

                        #add inter edges between clusters
                        if t1 in G:
                            G[t1] += [(t2, 1)]
                        else:
                            G[t1] = [(t2, 1)]
                        if t2 in G:
                            G[t2] += [(t1, 1)]
                        else:
                            G[t2] = [(t1, 1)]

        #connect entrances - build graph
        for i in range(m):
            for j in range(n):
                c1 = C[(i,j)]

                #intra edges in the same cluster
                cluster = self.walkable[c1.x1:c1.x2+1, c1.y1:c1.y2+1]
                
                for e in c1.E:
                    start = (e[0] - i*c_dim, e[1] - j*c_dim) 
                    ends = list(map(lambda x: (x[0] - i*c_dim, x[1] - j*c_dim), c1.E))

                    e_distances = self._flood_fil(start, ends, cluster)
                    edges = zip(c1.E, e_distances)
                    edges = list(filter(lambda x: (x[0] != e and x[1] != -1), edges))
                    G[e] += edges
                
        self.G = G


    def add_hier_node(self, node):
        #determine cluster
        c_dim = next(iter(self.C.values())).x2 - next(iter(self.C.values())).x1 + 1 
        (i, j) = self.determine_cluster(node)
        c = self.C[(i,j)]

        #add node - add connections between node and borders of cluster
        cluster = self.walkable[c.x1:c.x2+1, c.y1:c.y2+1]
        start = (node[0] - i*c_dim, node[1] - j*c_dim) 
        ends = list(map(lambda x: (x[0] - i*c_dim, x[1] - j*c_dim), c.E))

        e_distances = self._flood_fil(start, ends, cluster)

        edges = zip(c.E, e_distances)
        edges = list(filter(lambda x: x[1] != -1, edges))
        self.G[node] = edges

        for e, d in edges:
            self.G[e] += [(node, d)]

    def determine_cluster(self, node):
        c_dim = next(iter(self.C.values())).x2 - next(iter(self.C.values())).x1 + 1 
        m = int(self.width/c_dim)
        n = int(self.height/c_dim)

        for i in range(m):
            if node[0] >= i*c_dim and node[0] < (i+1)*c_dim:
                break
        for j in range(n):
            if node[1] >= j*c_dim and node[1] < (j+1)*c_dim:
                break

        return (i, j)

        

    def remove_hier_node(self, node):
        edges = self.G.pop(node)

        for e, d in edges:
            self.G[e].remove((node,d))


    def _flood_fil(self, start, ends, cluster):
        width = len(cluster)
        D = np.full((width, width), -1, int) #distances

        Q = Queue()
        Q.put(start)
        D[start[0], start[1]] = 0

        while not(Q.empty()):
            n = Q.get()
            d = D[n[0], n[1]]

            if n[0]-1 >= 0 and D[n[0]-1, n[1]] == -1 and cluster[n[0]-1, n[1]]: #up
                Q.put((n[0]-1, n[1]))
                D[n[0]-1, n[1]] = d + 1

            if n[1]-1 >= 0  and D[n[0], n[1]-1] == -1  and cluster[n[0], n[1]-1]: #left
                Q.put((n[0], n[1]-1))
                D[n[0], n[1]-1] = d + 1

            if n[0]+1 < width and D[n[0]+1, n[1]] == -1  and cluster[n[0]+1, n[1]]: #down
                Q.put((n[0]+1, n[1]))
                D[n[0]+1, n[1]] = d + 1

            if n[1]+1 < width and D[n[0], n[1]+1] == -1  and cluster[n[0], n[1]+1]: #right
                Q.put((n[0], n[1]+1))
                D[n[0], n[1]+1] = d + 1

        e_distances = [(D[e[0], e[1]]) for e in ends]

        return e_distances


    def _find_transitions(self, b1, b2, treshold):
        #find transition indexes on b1 and b2 borders
        transitions = []

        i = 0
        while i < len(b1):
            if b1[i]==1 and b2[i]==1:
                counter = 0
                e = []
                while i+counter < len(b1) and b1[i+counter] and b2[i+counter]:
                    e.append(i+counter)
                    counter +=1
                
                if len(e) == 0:
                    pass
                elif len(e) < treshold:
                    #transition is in the middle of the entrance
                    t = e[int(len(e)/2)]
                    transitions.append(t)
                else:
                    #transitions are the edges of the entrance
                    t1 = e[0]
                    t2 = e[-1]
                    transitions.append(t1)
                    transitions.append(t2)

                i += counter
            else:
                i += 1

        return transitions

def write_empty_map(m, n):
    #generate empty m*n map
    f = open("map.txt", "w")
    f.write("#"*n+"\n")
    for i in range(m-2):
        f.write("#")
        f.write("."*(n-2))
        f.write("#\n")
    f.write("#"*n)
    f.close()  