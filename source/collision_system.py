from enum import Enum
import agent
import pathfinder

class Type(Enum):
    GLANCING = 0
    TOWARD = 1
    REAR = 2
    STATIC = 3 

class Collision:
    def __init__(self, agent1, agent2, tile, coll_type, priority):
        self.agent1 = agent1
        self.agent2 = agent2
        self.tile = tile
        self.coll_type = coll_type
        self.priority = priority


def collision_prediction(agents, a):   
    a_move_pred, a_type = a.waypoints[len(a.waypoints)-1] #predict next movement
    collisions = []

    for i in agents:
        if a != i:
            if i.state != agent.State.IDLE:
                i_move_pred, i_type = i.waypoints[len(i.waypoints)-1]

                if a_move_pred == i_move_pred:
                    collisions.append(Collision(a, i, a_move_pred, Type.GLANCING, 2))

                elif a_move_pred == (i.x, i.y): 
                    if i_move_pred == (a.x, a.y):
                        collisions.append(Collision(a, i, a_move_pred, Type.TOWARD, 4))

                    else:
                        collisions.append(Collision(a, i, a_move_pred, Type.REAR, 1))

            else:
                if a_move_pred == (i.x, i.y):
                    collisions.append(Collision(a, i, a_move_pred, Type.STATIC, 3))
        
    return collisions
    

def resolve_collision(collision, agents, w_map):
    a1 = collision.agent1 #calling agent
    a2 = collision.agent2 #other agent

    #if one square away stop as if reached goal
    if a1.waypoints[0][0] == collision.tile:
        a1.waypoints.clear()
        a1.waypoints.append(((a1.x, a1.y), agent.Waypoint.LOW_L))
        
        return None 
    
    #if waiting dont override with other collisions
    if a1.state == agent.State.WAITING :
        #if we waited more then one round try to resolve collision again
        if a1.ticks_waiting > 0:
            a1.state = agent.State.ACTIVE
            a1.ticks_waiting = 0
        else:
            return None

    a1.priority = agent_priority(a1, agents, w_map)
    a2.priority = agent_priority(a2, agents, w_map)

    if collision.coll_type == Type.GLANCING:
        if a2.state == agent.State.WAITING:
            #if other agent is waiting we pass by
            pass

        elif a1.priority <= a2.priority:
            a1.state = agent.State.WAITING

    elif collision.coll_type == Type.TOWARD:
        if a1.priority <= a2.priority or a2.state == agent.State.WAITING:
            a2.state = agent.State.WAITING
            repath(a1, agents, w_map)
            
            #if completly blocked from target stop moving
            if len(a1.waypoints) == 0: 
                a1.waypoints.append(((a1.x, a1.y), agent.Waypoint.LOW_L))
        else:
            a1.state = agent.State.WAITING

    elif collision.coll_type == Type.REAR:
        a1.state = agent.State.WAITING

    elif collision.coll_type == Type.STATIC:
        if a1.priority < 4: 
            #agent should have enough space to find a way around
            repath(a1, agents, w_map)

            #if completly blocked from target stop moving
            if len(a1.waypoints) == 0: 
                a1.waypoints.append(((a1.x, a1.y), agent.Waypoint.LOW_L))
        else:
            #order other agent to move away
            #calculate push direction for one square
            push = [a2.x - a1.x, a2.y - a1.y]
            if push[0] < 0:
                push[0] = max(push[0], -1)
            else:
                push[0] = min(push[0], 1)
            if push[1] < 0:
                push[1] = max(push[1], -1)
            else:
                push[1] = min(push[1], 1)
            target = a2.x + push[0], a2.y + push[1]

            #check which neighbouring tiles can be pushed into
            neighbours = pathfinder.neighbouring_tiles(a2.x, a2.y, w_map, diagonals=False, walkable=True)
            free_direction = []
            agents_pos = [(j.x, j.y) for j in agents] 
            for i in neighbours:
                if not(i in agents_pos):
                    free_direction.append(i)

            if target in free_direction:
                #we can push in optimal direction
                a1.state = agent.State.WAITING
                agent.start_move(target, [a2], w_map)
            else:
                if len(free_direction) == 0:
                    #no free directions - repath and hope there is a way out
                    repath(a1, agents, w_map)
                    
                    #if completly blocked from target stop moving
                    if len(a1.waypoints) == 0: 
                        a1.waypoints.append(((a1.x, a1.y), agent.Waypoint.LOW_L))
                else:
                    #push into a free direction
                    a1.state = agent.State.WAITING
                    agent.start_move(free_direction[0], [a2], w_map)

def repath(a1, agents, w_map):
    #repath a part of old path to goal with updated unwalkable obstacles
    new_obstacles = []

    #update walkable map with still agents
    for i in agents:
        if i.state == agent.State.IDLE or i.state == agent.State.WAITING:
            new_obstacles.append((i.x, i.y))
            w_map.walkable[i.x, i.y] = False
    #agent.start_move(a1.waypoints[0], [a1], w_map) #replace whole path with a new one
    
    #find a waypoint on agents path that is not blocked by other agents
    steps = 2
    target, way_type = a1.waypoints[len(a1.waypoints)-steps]
    while w_map.walkable[target[0]][target[1]] == False and way_type == agent.Waypoint.LOW_L:
        if len(a1.waypoints) < steps:
            break 
        else:
            steps += 1
            target, way_type = a1.waypoints[len(a1.waypoints)-steps]

    if w_map.walkable[target[0]][target[1]] == False:
        #all low level waypoints are blocked - repath everything
        agent.start_move(a1.waypoints[0][0], [a1], w_map)
    else:
        path = pathfinder.a_star((a1.x, a1.y), target, w_map)
        if len(path) > 0:

            if path[0] != target:
                #target is unreachable, replace whole low level path
                way, way_type = a1.waypoints[len(a1.waypoints)-1]

                while way_type == agent.Waypoint.LOW_L:
                    a1.waypoints.pop()
                    if len(a1.waypoints) == 0:
                        break
                    way, way_type = a1.waypoints[len(a1.waypoints)-1]

                [a1.waypoints.append((w, agent.Waypoint.LOW_L)) for w in path]
            else:
                #replace steps of old path with new one
                for i in range(steps):
                    a1.waypoints.pop()
                [a1.waypoints.append((w, agent.Waypoint.LOW_L)) for w in path]

            if len(a1.waypoints) == 0: 
                print("prazen po pop v repathu")
        else:
            #bugfix: in case we go forward and backwards again remove unecessary path
            a1.state = agent.State.WAITING
            for i in range(steps):
                a1.waypoints.pop()
            if len(a1.waypoints) == 0: 
                #be careful not to remove everything
                a1.waypoints.append(((a1.x, a1.y), agent.Waypoint.LOW_L))
    
    #reset walkable map
    for i in new_obstacles:
        w_map.walkable[i[0], i[1]] = True
    
def agent_priority(a, agents, w_map):
    priority = 0

    neighbours = pathfinder.neighbouring_tiles(a.x, a.y, w_map, diagonals=True, walkable=False)

    agents_pos = [(j.x, j.y) for j in agents] 
    for i in neighbours:
        if i in agents_pos or w_map.walkable[i[0], i[1]] == False:
            priority += 1

    return priority     