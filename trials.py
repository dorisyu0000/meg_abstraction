import random
import os
import json
import re
from datetime import datetime
import psychopy
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import logging 
import numpy as np
from graphics import Graphics 
from config import KEY_DOWN,KEY_LEFT,KEY_UP ,KEY_RIGHT, KEY_SELECT, KEY_ABORT, KEY_CONTINUE, COLOR_HIGHTLIGHT 
from util import jsonify


TRIGGERS = {
    'show graph': 0,
    'show grid': 1,
    'move': 2,
    'done': 3,
}


class GridWorld:
    def __init__(self, win, grid, start,n,trial_number,trial_index,trial_block, done_message, rule = 'defualt', full_screen=False, tile_size=0.1, eyelink=None, triggers=None, score=0):
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
        self.eyelink = eyelink
        self.win = win
        self.n = n
        self.press_tol = 0.1
        self.gap = 0.001  # Gap between each tile
        self.tile_size = tile_size
        self.grid_code = grid  # Store the provided grid
        self.grid = self.create_grid()
        self.current_pos = [start[0], start[1]]  # Starting position for the cursor
        self.score = score
        self.rule = rule
        self.trial_number = trial_number
        self.gfx = Graphics(win)
        self.triggers = triggers

        self._message = visual.TextBox2(self.win, '', pos=(0, 0.42), color='black', autoDraw=True, size=(0.75, None), letterHeight=.035, anchor='center')
        self._tip = visual.TextBox2(self.win, '', pos=(0, 0.4), color='black', autoDraw=True, size=(0.65, None), letterHeight=.025, anchor='center')
        self.mask = visual.Rect(win, width=2, height=2, fillColor='white', opacity=0)
        self.mask.setAutoDraw(False)
        
        self.score_text = visual.TextStim(self.win, text=f"Score: {self.score}", pos=(0.7, 0.85), height=0.08, color='black', bold=True)

         # Reveal one red tile at the start
        self.done = False
        self.red_revealed = 1
        self.total_reveald = 1
        self.total_red = sum([sum([1 for cell in row if cell['value'] == 1]) for row in self.grid])
        self.done_message = done_message
        self.data = {
            "trial": {
                "kind": self.__class__.__name__,
                "rule": self.rule,
                "trial_number": self.trial_number,
                "grid": self.grid_code,
                "score": self.score,
                "total_reveal": self.total_reveald,
                "start": start,
                "trial_index": trial_index,
                "trial_block": trial_block,
            },
            "events": [],
            "flips": [],
            "key": [],
        }
        self.reveal_initial_red_tile(start) 
    
    def log(self, event, info={}):
        time = core.getTime()
        logging.debug(f'{self.__class__.__name__}.log {time:3.3f} {event} ' + ', '.join(f'{k} = {v}' for k, v in info.items()))
        datum = {
            'time': time,
            'event': event,
            **info
        }
        self.data["events"].append(datum)
        
    
    def create_grid(self):  
        """ Create a grid using the provided grid_code, where 1 is red and -1 is blue, and center the grid with gaps. """
        grid = []

        # Calculate the grid's total width and height including gaps
        grid_width = self.n * (self.tile_size + self.gap)
        grid_height = self.n * (self.tile_size + self.gap)

        # Centering offset: We shift by half of the grid's size
        x_offset = -(grid_width / 2) + (self.tile_size / 2)
        y_offset = -(grid_height / 2) + (self.tile_size / 2)

        for i in range(self.n):
            row = []
            for j in range(self.n):
                color_value = self.grid_code[i][j]  # Use the provided grid code
                color = 'red' if color_value == 1 else 'white'

                # Calculate the position of each tile: x_pos for column, y_pos for row (inverted y)
                x_pos = j * (self.tile_size + self.gap) + x_offset
                y_pos = -(i * (self.tile_size + self.gap)) - y_offset # Invert i for correct top-to-bottom row placement

                square = {
                    'rect': visual.Rect(self.win, width=self.tile_size, height=self.tile_size,
                                        pos=(x_pos, y_pos),
                                        fillColor='gray', lineColor='black'),
                    'highlight': False,  # Keep track of whether this tile is highlighted
                    'revealed': False,
                    'color': color,
                    'value': color_value
                }
                row.append(square)
            grid.append(row)
        return grid
    
    def draw_full_grid(self):
        """ Create a grid using the provided grid_code, where 1 is red and -1 is white, and center the grid with gaps. Reveal all tiles. """
        grid = []

        # Calculate the grid's total width and height including gaps
        grid_width = self.n * (self.tile_size + self.gap)
        grid_height = self.n * (self.tile_size + self.gap)

        # Centering offset: We shift by half of the grid's size
        x_offset = -(grid_width / 2) + (self.tile_size / 2)
        y_offset = -(grid_height / 2) + (self.tile_size / 2)

        for i in range(self.n):  # Loop through rows
            for j in range(self.n):  # Loop through columns
                color_value = self.grid_code[i][j]  # Use the provided grid code
                color = 'red' if color_value == 1 else 'white'

                # Calculate the position of each tile: x_pos for column, y_pos for row (top to bottom)
                x_pos = j * (self.tile_size + self.gap) + x_offset
                y_pos = -(i * (self.tile_size + self.gap)) - y_offset  # Inverted y for top-to-bottom

                # Create the tile (rectangle) and set its fill color and position
                rect = visual.Rect(self.win, width=self.tile_size, height=self.tile_size,
                                pos=(x_pos, y_pos),
                                fillColor=color, lineColor='black')

                # Draw the tile
                rect.draw()

    def reveal_initial_red_tile(self, start_pos):
        """ Reveal the tile at the start_pos if it is red, otherwise pick a random red tile. """
        i, j = start_pos
        # Check if the start position is valid and contains a red tile
        if 0 <= i < self.n and 0 <= j < self.n and self.grid[i][j]['value'] == 1:
            # Reveal the red tile at the start position
            self.grid[i][j]['rect'].fillColor = 'red'
            self.grid[i][j]['revealed'] = True
            self.log('start', {'color': 'red', 'pos': start_pos})
        else:
            # Fallback: Reveal a random red tile if the start position is not red
            red_tiles = [(x, y) for x in range(self.n) for y in range(self.n) if self.grid[x][y]['value'] == 1]
            if red_tiles:
               
                x, y = random.choice(red_tiles)
                self.grid[x][y]['rect'].fillColor = 'red'
                self.grid[x][y]['revealed'] = True

    def move_cursor(self, direction):
        """ Move the cursor based on key input. """
        if direction == 'up' and self.current_pos[0] > 0:
            self.current_pos[0] -= 1  # Move up (decrease row index)
        elif direction == 'down' and self.current_pos[0] < self.n - 1:
            self.current_pos[0] += 1  # Move down (increase row index)
        elif direction == 'left' and self.current_pos[1] > 0:
            self.current_pos[1] -= 1  # Move left (decrease column index)
        elif direction == 'right' and self.current_pos[1] < self.n - 1:
            self.current_pos[1] += 1  # Move right (increase column index)

    def highlight_tile(self):
        """ Highlight the currently selected tile by changing the line color and width. """
        for i in range(self.n):
            for j in range(self.n):
                if [i, j] == self.current_pos:
                    # Highlight the selected tile by changing line color and making the line thicker
                    self.grid[i][j]['rect'].lineColor = COLOR_HIGHTLIGHT
                    self.grid[i][j]['rect'].lineWidth = 10  # Increase the line width to make it stand out
                else:
                    # Reset others: Only reset if they are not revealed yet
                    self.grid[i][j]['rect'].lineColor = 'black'  # Reset the line color for unselected tiles
                    self.grid[i][j]['rect'].lineWidth = .1  # Reset line width to default

    def reveal_tile(self):
        """ Reveal the currently highlighted tile. """
        i, j = self.current_pos
        if not self.grid[i][j]['revealed']:
            self.grid[i][j]['rect'].fillColor = self.grid[i][j]['color']  # Change the color to reveal
            self.grid[i][j]['revealed'] = True
            self.update_score(self.grid[i][j]['value'])  # Update score based on red (+1) or blue (-1)
            self.log('reveal', {'color': self.grid[i][j]['color'], 'pos': [i, j]})
            if self.grid[i][j]['value'] == 1:
                self.red_revealed += 1


    def update_score(self, value):
        """ Update the score based on the revealed tile. """
        self.score += value


    def draw_grid(self):
        """ Draw all the tiles in the grid. """
        for row in self.grid:
            for cell in row:
                cell['rect'].draw()
    
    def fade_out(self):
        """ Fade-out effect using the mask to cover the screen. """
        self.mask.setAutoDraw(True) 
        for p in self.gfx.animate(.3):
            self.mask.setOpacity(p) 
            self.win.flip()
        self.gfx.clear()

        # After fade-out, reset the mask
        self.mask.setAutoDraw(False) 
        self.mask.setOpacity(0)      
        self.win.flip()


    def update_score(self, value):
        """ Update the score based on the revealed tile. """
        if value != 1:
            self.score -= 1
        else:
            self.score += value
        self.score_text.setText(f"Score: {self.score}")  # Properly updating the text for the score
    
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
    
    def center_message(self, msg, space=False):
        y_pos = -(self.n * (self.tile_size + self.gap)) / 2 - 0.1
        visual.TextBox2(self.win, msg,pos = (0,y_pos), color='black', letterHeight=.035).draw()
        self.win.flip()
        if space:
            event.waitKeys(keyList=['space'])
    

    def message(self, msg, space=False, tip_text=None):
        y_pos = (self.n * (self.tile_size + self.gap)) / 2 + 0.05
        logging.debug('message: %s (%s)', msg, tip_text)
        self.show_message()
        visual.TextBox2(self.win, msg,pos = (0.35,y_pos), color='black', letterHeight=.05).draw()
        self._tip.setText(tip_text if tip_text else 'press space to continue' if space else '')
        # self.win.flip()
        if space:
            event.waitKeys(keyList=KEY_SELECT)

    
    def run(self):
        """ Main loop to run the grid world. """
        while not self.done:
            # Highlight the current tile and draw the grid
            self.highlight_tile()
            self.draw_grid()
            self.message(f'Score: {self.score}')
            self.win.flip()

            # Get key input and check for combinations
            keys = event.getKeys()

            # Handle movement and selection when all movement keys are pressed at the same time
            if set([KEY_UP, KEY_DOWN]).issubset(keys):
                # All movement keys pressed simultaneously: select the current tile
                self.log('select', {'pos': self.current_pos})
                self.reveal_tile()  # Reveal the current highlighted tile
                if self.red_revealed == self.total_red:
                    self.log('done')

            else:
                # Handle individual movement for each key
                if KEY_UP in keys:
                    self.log('move', {'direction': 'up'})
                    self.move_cursor('up')
                if KEY_DOWN in keys:
                    self.log('move', {'direction': 'down'})
                    self.move_cursor('down')
                if KEY_LEFT in keys:
                    self.log('move', {'direction': 'left'})
                    self.move_cursor('left')
                if KEY_RIGHT in keys:
                    self.log('move', {'direction': 'right'})
                    self.move_cursor('right')

            # Check if all red tiles are revealed
            if self.red_revealed >= self.total_red:
                self.draw_full_grid()
                self.center_message(f'{self.done_message}')
                self.done_time = core.getTime()
                self.log('done')
                core.wait(2)  # Pause for 2 seconds
                self.win.flip()
                logging.info("All red tiles revealed. Moving to next trial.")
                self.done = True

            # Handle abort case
            if KEY_ABORT in keys:
                logging.info("Abort key pressed. Exiting the game.")
                self.done = True
                self.status = 'abort'

        # Clean up and finish
        self.hide_message()
        self.fade_out()


        

if __name__ == '__main__':
    win = visual.Window([800, 800], fullscr=False, color='white', units='height', done_message='All red tiles revealed. Moving to next trial in 1 second.')
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ]
    start_pos = [3, 3]
    n = 7
    trial_number = 1
    grid_world = GridWorld(win=win, grid=grid, start=start_pos, n=n, trial_number=trial_number, rule='default', full_screen=False, tile_size=0.1)
    grid_world.run()
    win.close()
