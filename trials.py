import random
import os
import logging
import json
import re
from datetime import datetime
import psychopy
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import logging 
import numpy as np
from config import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_SELECT, KEY_ABORT, COLOR_RED, COLOR_BLUE, COLOR_GREY, COLOR_HIGHTLIGHT 
from graphics import Graphics 
from util import jsonify


class GridWorld:
    def __init__(self, grid, full_screen=False, n=7, tile_size=0.1, start=[1,1], score=0):
        """
        Initialize the grid world with a predefined grid.
        Parameters:
        ----------
        grid : list of lists
            A predefined grid where 1 represents red and -1 represents blue
        full_screen : bool
            Whether the window is in full screen mode or not
        n : int
            The size of the grid (n x n)
        tile_size : float
            The size of each tile in the grid
        start : list
            Starting position for the red tile
        score : int
            Initial score for the game
        """
        self.full_screen = full_screen
        self.win = self.setup_window()
        self.n = n
        self.tile_size = tile_size
        self.grid_code = grid  # Store the provided grid
        self.grid = self.create_grid()
        self.current_time = None
        self.start_time = None
        self.end_time = None
        self.score = score
        self.data = {
            'trial': {
                'grid_start': start,
                'score': score,
            },
            'events': [],
            "flips": [],
            "mouse": [],
        }
        self._message = visual.TextBox2(self.win, '', pos=(0.3, 0.42), color='black', autoDraw=True, size=(0.75, None), letterHeight=.035, anchor='center')
        self._tip = visual.TextBox2(self.win, '', pos=(0.3, 0.4), color='black', autoDraw=True, size=(0.65, None), letterHeight=.025, anchor='center')
        logging.info("begin trial " + str(self.data["trial"]))

        # Adjusted score text position and height
        self.score_text = visual.TextStim(self.win, text=f"Score: {self.score}", pos=(0, 0.85), height=0.05, color='black', bold=True)
        
        self.reveal_initial_red_tile(start)  # Reveal one red tile at the start
        self.mouse = event.Mouse()
        self.done = False
        self.red_revealed = 1
        self.total_red = sum([sum([1 for cell in row if cell['value'] == 1]) for row in self.grid])
    
    def setup_window(self):
        size = (1350,750)
        win = visual.Window(size, allowGUI=True, color='white', units='height', fullscr=self.full_screen)
        win.flip()
        return win

    def create_grid(self):
        """ Create a grid using the provided grid_code, where 1 is red and -1 is blue, and center the grid. """
        grid = []

        # Calculate the grid's total width and height
        grid_width = self.n * self.tile_size
        grid_height = self.n * self.tile_size

        # Centering offset: We shift by half of the grid's size
        x_offset = -(grid_width / 2) + self.tile_size / 2
        y_offset = -(grid_height / 2) + self.tile_size / 2

        for i in range(self.n):
            row = []
            for j in range(self.n):
                color_value = self.grid_code[i][j]  # Use the provided grid code
                color = 'red' if color_value == 1 else 'blue'

                # Calculate the centered position of each tile
                x_pos = i * self.tile_size + x_offset
                y_pos = j * self.tile_size + y_offset

                square = {
                    'rect': visual.Rect(self.win, width=self.tile_size, height=self.tile_size,
                                        pos=(x_pos, y_pos),
                                        fillColor='gray', lineColor='black'),
                    'revealed': False,
                    'color': color,
                    'value': color_value
                }
                row.append(square)
            grid.append(row)
        return grid


    def reveal_initial_red_tile(self, start_pos):
        """ Reveal the tile at the start_pos if it is red, otherwise pick a random red tile. """
        i, j = start_pos
        # Check if the start position is valid and contains a red tile
        if 0 <= i < self.n and 0 <= j < self.n and self.grid[i][j]['value'] == 1:
            # Reveal the red tile at the start position
            self.grid[i][j]['rect'].fillColor = 'red'
            self.grid[i][j]['revealed'] = True
        else:
            # Fallback: Reveal a random red tile if the start position is not red
            red_tiles = [(x, y) for x in range(self.n) for y in range(self.n) if self.grid[x][y]['value'] == 1]
            if red_tiles:
                x, y = random.choice(red_tiles)
                self.grid[x][y]['rect'].fillColor = 'red'
                self.grid[x][y]['revealed'] = True

    def draw_grid(self):
        """ Draw all the tiles in the grid. """
        for row in self.grid:
            for cell in row:
                cell['rect'].draw()

    def update_score(self, value):
        """ Update the score based on the revealed tile. """
        self.score += value
        self.score_text.setText(f"Score: {self.score}")  # Properly updating the text for the score

    def reveal_tile(self, pos):
        """ Reveal the tile that was clicked on (if any). """
        for row in self.grid:
            for cell in row:
                if cell['rect'].contains(pos) and not cell['revealed']:
                    cell['rect'].fillColor = cell['color']  # Change the color to reveal
                    cell['revealed'] = True
                    if cell['value'] == 1:
                        self.red_revealed += 1
                    self.update_score(cell['value'])  # Update score based on red (+1) or blue (-1)
                    return
    
    def on_flip(self):
        if 'q' in event.getKeys():
            exit()
        # if 'f' in event.getKeys():

        self.win.callOnFlip(self.on_flip)

    def hide_message(self):
        self._message.autoDraw = False
        self._tip.autoDraw = False
        self.win.flip()

    def show_message(self):
        self._message.autoDraw = True
        self._tip.autoDraw = True

    def message(self, msg, space=False, tip_text=None):
        logging.debug('message: %s (%s)', msg, tip_text)
        self.show_message()
        self._message.setText(msg)
        self._tip.setText(tip_text if tip_text else 'press space to continue' if space else '')
        # self.win.flip()
        if space:
            event.waitKeys(keyList=['space'])

    def run(self):
        """ Main loop to run the grid world. """
        while True:
            self.message(f'Score:{self.score}')
            self.draw_grid()
            self.win.flip()

            # Check for mouse clicks
            mouse = event.Mouse(visible=True, win=self.win)
            if mouse.getPressed()[0]:  # Left mouse button clicked
                pos = mouse.getPos()
                self.reveal_tile(pos)

            # Check for the escape key to exit
            if 'escape' in event.getKeys():
                break

        self.win.close()
        core.quit()


# Running the GridWorld experiment
if __name__ == "__main__":
    # Define the predefined grid where 1 is red and -1 is blue
    grid_code = [
        [1, 1, 1, 1, 1, 1, 1],
        [-1, -1, -1, -1, -1, -1, -1],
        [1, -1, 1, -1, 1, -1, 1],
        [-1, 1, -1, 1, -1, 1, -1],
        [1, -1, 1, -1, 1, -1, 1],
        [-1, 1, -1, 1, -1, 1, -1],
        [1, -1, 1, -1, 1, -1, 1]
    ]

    # Set the starting position for the initial red tile
    start_pos = [6, 0]  # Set the starting position

    # Instantiate the GridWorld with the window, grid_code, and grid size
    grid_world = GridWorld(grid=grid_code, n=7, tile_size=0.1, start=start_pos, full_screen=False)

    # Run the grid world experiment
    grid_world.run()
