from queue import PriorityQueue
from queue import Queue

def a_star_graph(start, goal, G):
    g = {}
    g[start] = 0

    open_set = PriorityQueue()
    open_set.put((h(start, goal), start))

    came_from = {}

    min_f = float('inf')
    closest = start

    while open_set.empty() == False:
        curr = open_set.get()[1]

        if curr == goal:
            return reconstruct_path(goal, came_from, start)

        #check neighbours
        neighbours = G[curr]

        for (n, p) in neighbours:
            gn = g[curr] + p
            prev_gn = None

            if not (n in g):
                prev_gn = float('inf')
            else:
                prev_gn = g[n]

            if gn < prev_gn:
                came_from[n] = curr
                g[n] = gn
                hn = h(n, goal)
                f = gn + hn

                #remember closest node and f score
                min_f, closest = min((min_f, closest), (hn, n), key = lambda x: x[0])

                if not (n in open_set.queue):
                    open_set.put((f , n))

    #if we didnt reach the goal find path to closest node
    return reconstruct_path(closest, came_from, start)

def a_star(start, goal, w_map):
    height = w_map.height
    width = w_map.width

    g = {}
    g[start] = 0

    open_set = PriorityQueue()
    open_set.put((h(start, goal), start))

    came_from = {}

    min_f = float('inf')
    closest = start

    while open_set.empty() == False:
        curr = open_set.get()[1]

        if curr == goal:
            return reconstruct_path(goal, came_from, start)

        #check neighbours
        neighbours = neighbouring_tiles(curr[0], curr[1], w_map, diagonals=False, walkable=True)

        for n in neighbours:
            gn = g[curr] + 1
            prev_gn = None

            if not (n in g):
                prev_gn = float('inf')
            else:
                prev_gn = g[n]

            if gn < prev_gn:
                came_from[n] = curr
                g[n] = gn
                hn = h(n, goal)
                f = gn + hn

                #remember closest node and f score
                min_f, closest = min((min_f, closest), (hn, n), key = lambda x: x[0])

                if not (n in open_set.queue):
                    open_set.put((f , n))

    #if we didnt reach the goal find path to closest node
    return reconstruct_path(closest, came_from, start)


def reconstruct_path(current, came_from, start):
    path = [current]
    while current != start:
        current = came_from[current]
        path.append(current)

    return path[:-1]


def h(v1, v2):
    #manhattan
    d = abs(v1[0] - v2[0]) + abs(v1[1] - v2[1])
    return d


def closest_target(agent, target, w_map):
    #using modified breadth first search
    Q = Queue()
    discovered = set()
    
    discovered.add(target)
    Q.put((target, 0))

    new_target = target
    min_h = float('inf')
    max_level = float('inf')

    while Q.empty() == False:
        #remember level of "tree" so we can pick the closest walkeable tile in smallest level
        curr = Q.get()
        curr_pos = curr[0]
        curr_level = curr[1]

        d = h(curr_pos, (agent.x, agent.y))

        if w_map.walkable[curr_pos[0]][curr_pos[1]] and curr_level <= max_level:
            max_level = curr_level
            min_h, new_target = min((min_h, new_target), (d, curr_pos), key = lambda x: x[0])

        neighbours = neighbouring_tiles(curr_pos[0], curr_pos[1], w_map, diagonals=False)

        for n in neighbours:
            if not(n in discovered):
                discovered.add(n)

                if (curr_level + 1) <= max_level:
                    Q.put((n, curr_level+1)) 

    return new_target

def neighbouring_tiles(x, y, w_map, diagonals=False, walkable=False):
    neighbours = []

    if x-1 >= 0:
        neighbours.append((x-1, y)) #up
    if y-1 >= 0:
        neighbours.append((x, y-1)) #left
    if x+1 < w_map.width: 
        neighbours.append((x+1, y)) #down
    if y+1 < w_map.height: 
        neighbours.append((x, y+1)) #right
    if diagonals:
        if x-1 >= 0 and y-1 >= 0:
            neighbours.append((x-1, y-1)) #up left
        if x-1 >= 0 and y+1 < w_map.height:
            neighbours.append((x-1, y+1)) #up right
        if x+1 < w_map.width and y-1 >= 0:
            neighbours.append((x+1, y-1)) #down left
        if x+1 < w_map.width and y+1 < w_map.height:
            neighbours.append((x+1, y+1)) #down right

    if walkable:
        walkable_neighbours = []
        for n in neighbours:
            if w_map.walkable[n[0], n[1]]:
                walkable_neighbours.append(n)

        return walkable_neighbours
    else:
        return neighbours