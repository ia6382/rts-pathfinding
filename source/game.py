import time
import tcod
import tcod.event

import world
import agent
import renderer
import config

import cProfile, pstats, io
import random

MAP = "test_map.txt"
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
GUI_HEIGHT = 15

def profile(fnc):
    """A decorator that uses cProfile to profile a function"""
    
    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = fnc(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return inner

#@profile
def main():
    #grouping variables
    selecting = False
    selected = []
    select_start = None
    select_end = None

    #game variables
    paused = False

    #time system variables
    start_time = time.time()
    tick_rate = 0.1 # start new tick ("turn in a game") every 0.1 seconds
    loop_counter = 0
    fps = 0

    #create world map w_map
    w_map = world.Map(0, 0)
    w_map.read_map(MAP)

    #create heirarhical map
    w_map.build_hierahical_graph(10)
    
    SCREEN_WIDTH = w_map.width
    SCREEN_HEIGHT = w_map.height+GUI_HEIGHT #space for debug GUI

    #init console
    tcod.console_set_custom_font('terminal10x10.png', tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD)
    console = tcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'pathfindig project', order="F", renderer=tcod.RENDERER_SDL2, vsync=True)

    #agents
    agents = spawn_agents()
        
    #main game loop
    while True:
        #handle input
        for event in tcod.event.get():
            #close window
            if event.type == "QUIT":
                raise SystemExit()

            elif event.type == "KEYDOWN":
                #quit
                if event.sym == tcod.event.K_ESCAPE:
                    console.close()
                    return True

                #toggle common path for agents
                if event.sym == tcod.event.K_F1:
                    config.COMMON_PATH = not config.COMMON_PATH
                
                #toggle hierarhical a star for pathfinding
                if event.sym == tcod.event.K_F2:
                    config.HPA = not config.HPA

                #toggle fast renderer
                if event.sym == tcod.event.K_F3:
                    config.FAST_MAP_RENDER = not config.FAST_MAP_RENDER

                #toggle basic use case
                if event.sym == tcod.event.K_F4:
                    config.BASE_CASE = not config.BASE_CASE
                    agents = spawn_agents()

                #respawn agents
                if event.sym == tcod.event.K_r:
                    agents = spawn_agents()

                #pass the turn - move all the agents
                if event.sym == tcod.event.K_SPACE:
                    agent.execute_action(agents, w_map)   

                #pause/unpause game
                if event.sym == tcod.event.K_p:
                    paused = not(paused)                    

            elif event.type == "MOUSEBUTTONDOWN":
                #start selection
                if event.button == tcod.event.BUTTON_LEFT: 
                    selecting = True
                    select_start = event.tile
                    select_end = event.tile

                #set target
                if event.button == tcod.event.BUTTON_RIGHT and selected != []:
                    #make sure click is inside of map area
                    if event.tile.x < w_map.width and event.tile.x >= 0 and event.tile.y < w_map.height and event.tile.y >= 0:
                        search_time_start = time.time()
                        
                        agent.start_move(event.tile, selected, w_map)
                        
                        print("search time: "+str(round(time.time() - search_time_start, 3))+"s")

            elif event.type == "MOUSEMOTION":
                #update selection size
                if selecting:
                    select_end = event.tile

            elif event.type == "MOUSEBUTTONUP":
                #end selection
                if event.button == tcod.event.BUTTON_LEFT:
                    selected = agent.agents_in_square(agents, select_start, event.tile)
                    selecting = False               

        #redraw display
        renderer.render_all(console, w_map, agents, select_start, select_end, SCREEN_WIDTH, SCREEN_HEIGHT, GUI_HEIGHT, selected, selecting, paused)
        
        #time system
        loop_counter += 1
        end_time = time.time()
        if (end_time - start_time) >= tick_rate:

            if paused == False:
                agent.execute_action(agents, w_map)  

            fps = round(loop_counter / (end_time - start_time), 1)

            loop_counter = 0
            start_time = time.time()
        #display fps outside renderer - faster
        console.print(SCREEN_WIDTH-9, SCREEN_HEIGHT-GUI_HEIGHT+1, "FPS: "+str(fps), (255, 255, 255), None)


def spawn_agents():
    agents = []
    if config.BASE_CASE:
        agents += [agent.Agent(15, 15, '@', tcod.magenta, "Agent 1", 1)]
        agents += [agent.Agent(16, 18, '@', tcod.yellow, "Agent 2", 1)]
        agents += [agent.Agent(17, 11, '@', tcod.blue, "Agent 3", 1)]
        agents += [agent.Agent(18, 20, '@', tcod.cyan, "Agent 4", 1)]
        agents += [agent.Agent(19, 15, '@', tcod.red, "Agent 5", 1)]
        agents += [agent.Agent(20, 14, '@', tcod.green, "Agent 6", 1)]
        agents += [agent.Agent(13, 13, '@', tcod.orange, "Agent 7", 1)]
    else:
        
        for i in range(10, 15):
            for j in range(10, 15):
                agents += [agent.Agent(i, j, '@', tcod.Color(random.randrange(255), random.randrange(255), random.randrange(255)), "Agent "+str(i)+"."+str(j), 1)]
        
        for i in range(40,45):
            for j in range(40, 45):
                agents += [agent.Agent(i, j, '@', tcod.Color(random.randrange(255), random.randrange(255), random.randrange(255)), "Agent "+str(i)+"."+str(j), 1)]

    return agents

if __name__ == "__main__":
    main()