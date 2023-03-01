# Pathfinding and Movement System for a Real Time Strategy Game

## About
Abstract from the included paper:

Moving units across the map in real time strategy
(RTS) games need to be done quickly while also looking natural
to the player. Depending on the map size and the number of units
this can pose a problem. Standard pathfinding algorithms can
become insufficient and tricks need to be used to avoid or hide
their limitations. In this paper, several known approaches are
presented and tested in a prototype RTS game. Results offer
insights into the gameplay mechanics of some popular RTS games of
the late 1990s and early 2000s.

---
We developed a prototype RTS game with Python and the [tcod library](https://github.com/libtcod/python-tcod), in the vein of classic roguelike games. 
With it we tested several popular pathfinding approaches: 
* naive A*
* shared path A*
* HPA*
* shared path HPA*

Results and discussion are included in the `paper.pdf`. 
Below is a demo gif showing unit movement with different algorithms (note the algorithm selection in the lower right corner).

![demo](demo.gif)

The repository includes both the source code and the executable file (`dist/game.exe`). 

This was a personal assignment project for the Artificial Intelligence course at the University of Ljubljana, Faculty of Computer and Information Science. 
The course covered the following main topics: path searching, planning (goal regression, partial order planning, graph planning), reinforcement learning,
qualitative reasoning and modelling, inductive logic programming.

It also served as an inspiration for my Master's thesis; [Multi-Agent Pathfinding in a Real-Time Strategy Game](https://repozitorij.uni-lj.si/IzpisGradiva.php?id=141866&lang=eng).

## Controls
* Game map can be changed by editing the `test_map.txt` file. "#" is a wall, "~" is water, "." is an empty ground tile, and "T" is a tree. 
* Units are repesented with a coloured "@" character - **left click** selects a unit and **right click** orders the selected units to the desired destination.
* **R** resets the map
* **P** pauses the game
* **SPACE** moves the units for one turn (you can hold down the key to speed up the movement)
* **F1** toggle the shared path approach
* **F2** toggle the HPA\* approach
* **F3** toggle the fancy coloured renderer
* **F4** toggle the preset unit positions