from random import randrange
import tcod 

import config

#colours
BG = tcod.Color(0, 0, 0)
WALL = tcod.Color(245, 245, 245)
GROUND = tcod.Color(100, 100, 100)
SELECTBOX = tcod.Color(0, 255, 0)
SELECTED_BG = tcod.Color(0, 255, 0)
WOOD = tcod.Color(117, 70, 0)
TEXT = tcod.Color(255, 255, 255)

def fg_colour(char):
    #set colour depending on char
    if char == ".":
        return GROUND
    elif char == "~":
        shimmer = randrange(50)
        return tcod.Color(0+shimmer, 17+shimmer, 255)
    elif char == "*":
        return WOOD
    else:
        return WALL  

def render_map(console, w_map, screen_width, screen_height):
    # Draw all the chars in world map

    for y in range(w_map.height):
        for x in range(w_map.width):
            char = w_map.char[x, y]
            console.print(x, y, char, fg_colour(char), BG)

    if config.HPA:
        for e in w_map.G.keys():
            console.print(e[0], e[1], ".", GROUND, tcod.Color(100, 0, 0))

    console.blit(console, 0, 0, screen_width, screen_height, 0, 0, 0)

def render_mapFAST(console, w_map, screen_width, screen_height):
    #draw fast line by line instead char by char but without colours

    for y in range(w_map.height):
        s = ''.join(w_map.char[:, y]) #pobrere vecino casa
        console.print(0, y, s, GROUND, BG)
    
    if config.HPA:
        for e in w_map.G.keys():
            console.print(e[0], e[1], ".", GROUND, tcod.Color(100, 0, 0))
    
    console.blit(console, 0, 0, screen_width, screen_height, 0, 0, 0)

def render_agents(console, agents, screen_width, screen_height):
    #draw all agents

    for agent in agents:
        if agent.selected: 
            #highlight selected
            console.print(agent.x, agent.y, agent.char, agent.colour, SELECTED_BG)
            
            #mark destination
            #if agent.dest != None:
            #    console.print(agent.dest.x, agent.dest.y, "X", agent.colour, BG)

            #draw path to destnination
            for w, t in agent.waypoints:
                console.print(w[0], w[1], ".", GROUND, agent.colour)

            #print debug messege
            console.print(agent.x+1, agent.y, agent.debug_txt, agent.colour, BG)

        else: 
            console.print(agent.x, agent.y, agent.char, agent.colour, BG)
        
    console.blit(console, 0, 0, screen_width, screen_height, 0, 0, 0)

def clear_agents(console, agents, screen_width, screen_height):
    for agent in agents:
        console.print(agent.x, agent.y, " ", agent.colour, BG)

        if agent.selected:
            for w, t in agent.waypoints:
                console.print(w[0], w[1], " ", agent.colour, BG)

    console.blit(console, 0, 0, screen_width, screen_height, 0, 0, 0)

def render_selectbox(console, select_start, select_end, screen_width, screen_height):
    #draw selection box

    x = min(select_start.x, select_end.x)
    width = abs(select_start.x - select_end.x)
    y = min(select_start.y, select_end.y)
    height = abs(select_start.y - select_end.y)

    #vertical lines
    for i in range(height):
        console.print(x, y+i, "|", SELECTBOX, BG)
        console.print(x+width, y+i, "|", SELECTBOX, BG)

    #horizontal lines
    for i in range(width+1):
        console.print(x+i, y, "-", SELECTBOX, BG)
        console.print(x+i, y+height, "-", SELECTBOX, BG)

    console.blit(console, 0, 0, screen_width, screen_height, 0, 0, 0)

def render_gui(console, screen_width, screen_height, gui_height, selected, paused):
    info = "selected agents: " + str(len(selected))
    console.print(1, screen_height - gui_height+1, info, TEXT, BG)

    console.print(int(screen_width/2)+6, screen_height-gui_height+1, ("SHARED PATH:"+str(config.COMMON_PATH)), TEXT, BG)

    console.print(int(screen_width/2)+27, screen_height-gui_height+1, ("HPA*:"+str(config.HPA)), TEXT, BG)
    
    if paused:
        console.print(int(screen_width/2)-6, screen_height-gui_height+1, "PAUSED", SELECTBOX, BG)

    for i, a in enumerate(selected):
        info = a.name+" ( "+a.char+" ) at x="+str(a.x)+", y="+str(a.y)+"."+" Priority: "+str(a.priority)
        console.print(5, screen_height-gui_height+i*2+3, info, TEXT, BG)

    console.blit(console, 0, 0, screen_width, screen_height, 0, 0, 0)

def clear_gui(console, screen_width, screen_height, gui_height):
    for y in range(screen_height-gui_height, screen_height):
        s = " "*screen_width
        console.print(0, y, s, BG, BG)

    console.blit(console, 0, 0, screen_width, screen_height, 0, 0, 0)

def render_all(console, w_map, agents, select_start, select_end, screen_width, screen_height, gui_height, selected, selecting, paused):
        #refresh draw
        if config.FAST_MAP_RENDER:
            render_mapFAST(console, w_map, screen_width, screen_height)
        else:
            render_map(console, w_map, screen_width, screen_height)
        render_agents(console, agents, screen_width, screen_height)
        if selecting:
            render_selectbox(console, select_start, select_end, screen_width, screen_height)
        render_gui(console, screen_width, screen_height, gui_height, selected, paused)

        tcod.console_flush()

        clear_agents(console, agents, screen_width, screen_height)
        clear_gui(console, screen_width, screen_height, gui_height)