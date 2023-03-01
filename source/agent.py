import tcod
import tcod.event
from tcod.event import Point

from collections import deque
import math
from enum import Enum

import pathfinder
import collision_system
import world
import config

class State(Enum):
    IDLE = 0
    WAITING = 1
    ACTIVE = 2

class Waypoint(Enum):
    LOW_L = 0
    HIGH_L = 1

class Agent:
    """
    A generic object to represent agents
    """
    def __init__(self, x, y, char, colour, name, priority):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
        self.name = name
        self.priority = priority
        
        self.selected = False
        self.dest = None
        self.waypoints = deque() #stack
        self.state = State.IDLE
        self.ticks_waiting = 0
        self.debug_txt = ""

    def move(self, dx, dy):
        # Move the agent by a given amount
        self.x += dx
        self.y += dy

    def distance(self, agent_b):
        return math.sqrt((agent_b.x - self.x)**2 + (agent_b.y - self.y)**2)



def agents_in_square(agents, select_start, select_end):
    selected = []

    #fix orientation
    x1 = min(select_start.x, select_end.x)
    x2 = max(select_start.x, select_end.x)
    y1 = min(select_start.y, select_end.y)
    y2 = max(select_start.y, select_end.y)

    for a in agents:
        if a.x >= x1 and a.x <= x2 and a.y >= y1 and a.y <= y2:
            a.selected = True
            selected.append(a)
        else:
            a.selected = False

    return selected

def start_move(group_target, selected, w_map):
    if config.COMMON_PATH:
        common_path(group_target, selected, w_map)
    else:
        individual_path(group_target, selected, w_map)

def individual_path(group_target, selected, w_map):
    MAX_F_DISTANCE = 3

    #get leader of group - mediod
    min_d = float('inf')
    leader = selected[0]
    for a in selected:
        d = 0
        for b in selected:
            d += a.distance(b)

        if d < min_d:
            min_d = d
            leader = a

    #set targets for agents
    for a in selected:
        a.waypoints.clear()

        #calculate offset considering max formation distance between agents and leader
        offset = [a.x - leader.x, a.y - leader.y]
        if offset[0] < 0:
            offset[0] = max(offset[0], -MAX_F_DISTANCE)
        else:
            offset[0] = min(offset[0], MAX_F_DISTANCE)
        if offset[1] < 0:
            offset[1] = max(offset[1], -MAX_F_DISTANCE)
        else:
            offset[1] = min(offset[1], MAX_F_DISTANCE)

        target = group_target[0] + offset[0], group_target[1] + offset[1]

        #limit the target to inside of map area
        target = (min(target[0], w_map.width-1), min(target[1], w_map.height-1))
        target = (max(target[0], 0), max(target[1], 0))
        
        #check if target is unwalkable
        if w_map.walkable[target[0]][target[1]] == False:
            target = pathfinder.closest_target(a, target, w_map)    
        
        a.dest = Point(target[0], target[1])

        #find path to targets
        a.waypoints = init_path((a.x, a.y), target, w_map)

        #set status of agent to active
        if len(a.waypoints) > 0:
            a.state = State.ACTIVE
        else:
            a.state = State.IDLE


def common_path(group_target, selected, w_map):
    """
    one path for all agents 
    """
    MAX_F_DISTANCE = 3

    #get center of group
    center = [0,0]
    for a in selected:
        center[0] += a.x
        center[1] += a.y
    center[0] = round(center[0] / len(selected))
    center[1] = round(center[1] / len(selected))

    #limit the center to inside of map area
    center = (min(center[0], w_map.width-1), min(center[1], w_map.height-1))
    center = (max(center[0], 0), max(center[1], 0))
        
    #check if center is unwalkable
    if w_map.walkable[center[0]][center[1]] == False:
        center = pathfinder.closest_target(a, (center[0], center[1]), w_map)  

    #get leader of group - mediod
    min_d = float('inf')
    leader = selected[0]
    for a in selected:
        d = 0
        for b in selected:
            d += a.distance(b)

        if d < min_d:
            min_d = d
            leader = a

    #correct group_target for leader
    #limit the target to inside of map area
    group_target = (min(group_target[0], w_map.width-1), min(group_target[1], w_map.height-1))
    group_target = (max(group_target[0], 0), max(group_target[1], 0))
        
    #check if target is unwalkable
    if w_map.walkable[group_target[0]][group_target[1]] == False:
        group_target = pathfinder.closest_target(a, group_target, w_map)  

    #find the main part of path for all agents
    #main_path = pathfinder.a_star((center[0], center[1]), group_target, w_map)
    main_waypoints = init_path((center[0], center[1]), group_target, w_map)
    if len(main_waypoints) > 0:
        group_target = main_waypoints[0][0]

    #add beginning and end path for agents
    for a in selected:
        a.waypoints.clear()

        #find path from agent to center of group
        #begin_path = pathfinder.a_star((a.x, a.y), (center[0], center[1]), w_map)
        begin_waypoints = init_path((a.x, a.y), (center[0], center[1]), w_map)

        #calculate offset considering max formation distance between agents and leader
        offset = [a.x - leader.x, a.y - leader.y]
        if offset[0] < 0:
            offset[0] = max(offset[0], -MAX_F_DISTANCE)
        else:
            offset[0] = min(offset[0], MAX_F_DISTANCE)
        if offset[1] < 0:
            offset[1] = max(offset[1], -MAX_F_DISTANCE)
        else:
            offset[1] = min(offset[1], MAX_F_DISTANCE)

        target = group_target[0] + offset[0], group_target[1] + offset[1]

        #limit the target to inside of map area
        target = (min(target[0], w_map.width-1), min(target[1], w_map.height-1))
        target = (max(target[0], 0), max(target[1], 0))
        
        #check if target is unwalkable
        if w_map.walkable[target[0]][target[1]] == False:
            target = pathfinder.closest_target(a, target, w_map)    
        
        a.dest = Point(target[0], target[1])

        #find path from leaders target to agents target
        #end_path = pathfinder.a_star(group_target, target, w_map)
        end_waypoints = init_path(group_target, target, w_map)

        #combine paths
        a.waypoints = end_waypoints + main_waypoints + begin_waypoints
        #[a.waypoints.append(w) for w in path]

        #set status of agent to active
        if len(a.waypoints) > 0:
            a.state = State.ACTIVE
        else:
            a.state = State.IDLE


def execute_action(agents, w_map):
    for a in agents:
        a.debug_txt = ""

        #if agent has a path to travel
        if a.state != State.IDLE:

            #check if next waypoint is high level
            next_waypoint, way_type = a.waypoints[len(a.waypoints)-1]
            if(way_type == Waypoint.HIGH_L):
                next_waypoint, way_type = a.waypoints.pop()
                
                #find low level path to waypoint
                path = pathfinder.a_star((a.x, a.y), next_waypoint, w_map)
                [a.waypoints.append((w, Waypoint.LOW_L)) for w in path]

            #find all possible collisions
            collisions = collision_system.collision_prediction(agents, a)
            collisions.sort(reverse=True, key=lambda x: x.priority)

            #resolve collisions
            for c in collisions:
                a.debug_txt = c.coll_type.name
                collision_system.resolve_collision(c, agents, w_map)
            
            if a.state == State.WAITING and len(collisions) > 0:
                #collision solver wants agent to wait this turn
                a.ticks_waiting += 1    
            else:
                #move to next waypoint
                a.state = State.ACTIVE #in case if we were waiting and now there are no collisions
                ticks_waiting = 0

                next_waypoint, way_type = a.waypoints.pop()

                dx = next_waypoint[0] - a.x
                dy = next_waypoint[1] - a.y
                a.move(dx, dy)

                #if out of waypoints - stop
                if len(a.waypoints) == 0:
                    a.state = State.IDLE

def init_path(start, target, w_map):
    #find path to targets
    (si, sj) = w_map.determine_cluster(start)
    (ti, tj) = w_map.determine_cluster(target)

    waypoints = deque()    

    if (si, sj) == (ti, tj) or config.HPA == False:
        #if target is in the same cluster use low level pathfinding
        path = pathfinder.a_star(start, target, w_map)
        [waypoints.append((w, Waypoint.LOW_L)) for w in path]
        return waypoints
    else:
        #if not, first use high level, rough pathfinding
        added_start = False
        if not(start in w_map.G):
            w_map.add_hier_node(start)
            added_start = True

        added_goal = False
        if not(target in w_map.G):
            w_map.add_hier_node(target)
            added_goal = True

        hier_path = pathfinder.a_star_graph(start, target, w_map.G)
        [waypoints.append((w, Waypoint.HIGH_L)) for w in hier_path]
            
        if added_start:
            w_map.remove_hier_node(start)
        if added_goal:
            w_map.remove_hier_node(target)

        #path first segment low level for better collision avodiance
        if len(waypoints) > 0:
            next_waypoint, way_type = waypoints.pop()
                    
            path = pathfinder.a_star(start, next_waypoint, w_map)
            [waypoints.append((w, Waypoint.LOW_L)) for w in path]

        return waypoints