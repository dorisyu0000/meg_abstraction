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
from config import KEY_DOWN,KEY_LEFT,KEY_UP ,KEY_RIGHT, KEY_SELECT, KEY_ABORT, KEY_CONTINUE, COLOR_HIGHTLIGHT, KEY_1, KEY_2, KEY_3, COLOR_1, COLOR_2, COLOR_3
from util import jsonify

from triggers import Triggers

wait = core.wait

TRIGGERS = {
    'start': 0,
    'move': 1,
    'reveal_red': 2,
    'reveal_white': 3,
    'done': 4,
    'choice': 5,
}


class GridWorld:
    def __init__(self, win, grid, start,n,trial_number,trial_index,trial_block, done_message = None, time_limit = 20,rule = 'defualt', triggers=None, full_screen=False, tile_size=0.1, eyelink=None, score=0):
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
        self.gfx = Graphics(win)
        self.n = n
        self.press_tol = 0.1
        self.gap = 0.001  # Gap between each tile
        self.tile_size = tile_size
        self.grid_code = grid  # Store the provided grid
        self.grid = self.create_grid()
        self.current_pos = start[0]  # Starting position for the cursor
        self.score = score
        self.rule = rule
        self.trial_number = trial_number
        self.time_limit = time_limit
        self.triggers = triggers

        self.current_time = None
        self.start_time = None
        self.end_time = None

        self._message = visual.TextBox2(self.win, '', pos=(0.3, 0.42), color='black', autoDraw=True, size=(0.75, None), letterHeight=.035, anchor='center')
        self._tip = visual.TextBox2(self.win, '', pos=(0.3, 0.4), color='black', autoDraw=True, size=(0.65, None), letterHeight=.025, anchor='center')
        self.mask = visual.Rect(win, width=2, height=2, fillColor='white', opacity=0)
        self.mask.setAutoDraw(False)
        
        self.score_text = self.gfx.text(f"Score: {self.score}", pos=(0.7, 0.85), height=0.08, color='black', bold=True)

         # Reveal one red tile at the start
        self.done = False
        self.red_revealed = 1
        self.total_reveald = 1
        self.total_red = sum([sum([1 for cell in row if cell['value'] == 1]) for row in self.grid])
        self.done_message = done_message
        self.timeout_message = "Sorry, you ran out of time. Try to be faster next time."
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
            "white_tiles": [],
            "red_tiles": [],
        }
        self.reveal_initial_red_tile(start[0]) 
        print(self.current_pos)
        self.timer = None  

    
    def log(self, event, info={}):
        time = core.getTime()
        logging.debug(f'{self.__class__.__name__}.log {time:3.3f} {event} ' + ', '.join(f'{k} = {v}' for k, v in info.items()))
        datum = {
            'time': time,
            'event': event,
            **info
        }
        print("event", event)
        print("TRIGGERS", TRIGGERS)
        if self.triggers and event in TRIGGERS:
            self.triggers.send(TRIGGERS[event])
        print("triggers", self.triggers)
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
                    'rect': self.gfx.rect((x_pos, y_pos), self.tile_size, self.tile_size,
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
                rect = self.gfx.rect((x_pos, y_pos), self.tile_size, self.tile_size,
                                     fillColor=color, lineColor='black')

                # Draw the tile
                rect.setAutoDraw(True)

    def reveal_initial_red_tile(self, start_pos):
        """ Reveal the tile at the start_pos if it is red, otherwise pick a random red tile. """
        i, j = start_pos
        self.data["red_tiles"].append(start_pos)
        # Check if the start position is valid and contains a red tile
        if 0 <= i < self.n and 0 <= j < self.n and self.grid[i][j]['value'] == 1:
            # Reveal the red tile at the start position
            self.grid[i][j]['rect'].setColor('red')
            self.grid[i][j]['revealed'] = True
            self.log('start', {'color': 'red', 'pos': start_pos})
        else:
            # Fallback: Reveal a random red tile if the start position is not red
            red_tiles = [(x, y) for x in range(self.n) for y in range(self.n) if self.grid[x][y]['value'] == 1]
            if red_tiles:
                x, y = random.choice(red_tiles)
                self.grid[x][y]['rect'].setColor('red')
                self.grid[x][y]['revealed'] = True

    
    def highlight_tile(self):
        """ Highlight the currently selected tile by changing the line color and width. """
        for i in range(self.n):
            for j in range(self.n):
                if [i, j] == self.current_pos:
                    # Highlight the selected tile by changing line color and making the line thicker
                    self.grid[i][j]['rect'].setLineColor(COLOR_HIGHTLIGHT)
                    self.grid[i][j]['rect'].setLineWidth(6)  # Increase the line width to make it stand out
                else:
                    # Reset others: Only reset if they are not revealed yet
                    self.grid[i][j]['rect'].setLineColor('black')  # Reset the line color for unselected tiles
                    self.grid[i][j]['rect'].setLineWidth(1)  # Reset line width to default

    def reveal_tile(self):
        """ Reveal the currently highlighted tile. """
        i, j = self.current_pos
        if not self.grid[i][j]['revealed']:
            # Change the color to reveal the tile
            self.grid[i][j]['rect'].setColor(self.grid[i][j]['color'])
            self.grid[i][j]['revealed'] = True
            self.update_score(self.grid[i][j]['value'])  # Update score based on red (+1) or blue (-1)
            self.log('reveal', {'color': self.grid[i][j]['color'], 'pos': [i, j]})
            if self.grid[i][j]['value'] == 1:
                self.red_revealed += 1
                self.data["red_tiles"].append([i, j])
                self.log('reveal_red', {'pos': [i, j]})
            else:
                self.data["white_tiles"].append([i, j])
                self.log('reveal_white', {'pos': [i, j]})


    def update_score(self, value):
        if value != 1:
            self.score -= 1
        else:
            self.score += value


    def draw_grid(self):
        """ Draw all the tiles in the grid. """
        for row in self.grid:
            for cell in row:
                cell['rect'].setAutoDraw(True)  # Ensure each rectangle is set to be drawn

    def draw_timer(self):
        if self.time_limit is not None:
            self.timer_wrap = self.gfx.rect((0.5,-0.45), .02, 0.9, anchor='bottom', color=-.1)
            self.timer = self.gfx.rect((0.5,-0.45), .02, 0.9, anchor='bottom', color=-.2)
        else:
            self.timer = None 
        
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

        # Create the text stimulus once, if not already created
        if not hasattr(self, 'text_stim'):
            self.text_stim = self.gfx.text('', pos=(0, y_pos), color='black', height=.05)
            self.text_stim.setAutoDraw(True)  # Set to auto-draw

        # Update the text content
        self.text_stim.setText(msg)
        self._tip.setText(tip_text if tip_text else 'press space to continue' if space else '')
        self.win.flip()  # Flip to show the message

        if space:
            event.waitKeys(keyList=KEY_SELECT)


    def move_cursor(self, direction):
        """ Move the cursor based on key input. """
        if direction == 'up' and self.current_pos[0] > 0:
            self.current_pos[0] -= 1  # Move up (decrease row index)
        elif direction == 'down':
            if self.current_pos[0] == self.n - 1:  # Bottom of the grid (y-axis)
                self.current_pos[0] = 0
            else: 
                self.current_pos[0] += 1
        elif direction == 'left':
            if self.current_pos[1] == 0:
                self.current_pos[1] = self.n - 1
            else:
                self.current_pos[1] -= 1  # Move left (decrease column index)
        elif direction == 'right':
            if self.current_pos[1] == self.n - 1:
                self.current_pos[1] = 0
            else:
                self.current_pos[1] += 1  # Move right (increase column index)
        print(f"Current position: {self.current_pos}")  # Debugging print statement

    def tick(self):
        self.current_time = core.getTime()
        if self.start_time is not None and self.time_limit is not None:
            time_left = self.start_time + self.time_limit - core.getTime()
            if time_left > 0:
                p = time_left / self.time_limit
                if self.timer is not None:
                    self.timer.setHeight(0.9 * p)
                if time_left < 3:
                    p2 = time_left / 3
                    original = -.2 * np.ones(3)
                    red = np.array([1, -1, -1])
                    if self.timer is not None:
                        self.timer.setColor(p2 * original + (1-p2) * red)
        self.last_flip = t = self.win.flip()
        return t
    
    def do_timeout(self):
        for i in range(3):
            self.timer_wrap.setColor('red'); self.win.flip()
            wait(0.3)
            self.timer_wrap.setColor(-.2); self.win.flip()
            wait(0.3)
        self.log('timeout')
        self.draw_full_grid()
        self.done_time = core.getTime()
        self.center_message(f'{self.timeout_message}')
        core.wait(2) 
        self.win.flip()
        self.done = True
    

    def run(self):
        """ Main loop to run the grid world. """
        event.clearEvents()
        self.draw_timer()
        self.start_time = self.current_time = core.getTime()
        self.end_time = None if self.time_limit is None else self.start_time + self.time_limit
        self.start_time = self.tick()
        self.log('start')
        while not self.done:
            # Highlight the current tile and draw the grid
            self.highlight_tile()
            self.draw_grid()
            self.message(f'Score: {self.score}')
            self.win.flip()

            # Get key input and check for combinations
            keys = event.getKeys()

            if not self.done and self.end_time is not None and self.current_time > self.end_time:
                self.do_timeout()
                self.done = True
  
            self.tick()
            # Handle movement and selection when all movement keys are pressed at the same time
            if KEY_ABORT in keys:
                logging.info("Abort key pressed. Exiting the game.")
                self.done = True
                self.status = 'abort'
            if KEY_CONTINUE in keys:
                self.done = True
            if KEY_DOWN in keys:
                self.log('move', {'direction': 'down'})
                self.move_cursor('down')  # Normal move down
            if KEY_LEFT in keys:
                self.log('move', {'direction': 'left'})
                self.move_cursor('left')
            if KEY_RIGHT in keys:
                self.log('move', {'direction': 'right'})
                self.move_cursor('right')
            elif KEY_SELECT in keys:
                self.reveal_tile()
                if self.red_revealed == self.total_red:
                    self.log('done')
            

            if self.red_revealed >= self.total_red:
                self.draw_full_grid()
                self.center_message(f'{self.done_message}')
                while self.current_time < self.end_time:
                    self.tick()
                    self.win.flip()
                
                logging.info("All red tiles revealed. Moving to next trial.")
                self.done = True

            

        # Clean up and finish
        self.hide_message()
        self.fade_out()

class Locolizer(GridWorld):
    def __init__(self, win, grid, start, n, trial_index, trial_block, rule, rule_index, triggers = None, full_screen=False, tile_size=0.08, time_limit=3):
        self.start_positions = start
        super().__init__(win, grid, start, n, trial_index, trial_block, rule,rule_index, triggers=None, full_screen=full_screen, tile_size=tile_size, time_limit=time_limit)
        self.grid_code = self.grid
        self.time_limit = time_limit
        self.n = n
        self.tile_size = tile_size
        self.gap = 0.01
        self.current_choice = None  
        self.correct_choice = rule
        self.rule_index = rule_index
        self.score = 0
        self.triggers = triggers
        self.data = {
            "locolizer": {
                "rule": self.rule,
                "grid": self.grid_code,
                "score": self.score,  # Initialize score here
                "final_choice": self.current_choice,
                "start": start,
                "trial_index": trial_index,
                "trial_block": trial_block,
            },
            "events": [],
        }

    def log(self, event, info={}):
        time = core.getTime()
        logging.debug(f'{self.__class__.__name__}.log {time:3.3f} {event} ' + ', '.join(f'{k} = {v}' for k, v in info.items()))
        datum = {
            'time': time,
            'event': event,
            **info
        }
        print("event", event)
        print("TRIGGERS", TRIGGERS)
        if self.triggers and event in TRIGGERS:
            self.triggers.send(TRIGGERS[event])
        print("triggers", self.triggers)
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
                color_value = self.grid_code[i][j]
                color = 'red' if color_value == 1 else 'white'

                # Calculate the position of each tile: x_pos for column, y_pos for row (inverted y)
                x_pos = j * (self.tile_size + self.gap) + x_offset
                y_pos = -(i * (self.tile_size + self.gap)) - y_offset

                # Determine if the current position is in the start positions
                is_start_position = [i, j] in self.start_positions

                # Set the fill color based on whether the tile is a start position
                fill_color = color if is_start_position else 'gray'

                square = {
                    'rect': self.gfx.rect((x_pos, y_pos), self.tile_size, self.tile_size,
                                     fillColor=fill_color, lineColor='black'),  # Set lineWidth for border tiles
                    'highlight': False,
                    'revealed': is_start_position,
                    'color': color,
                    'value': color_value
                }
                row.append(square)
            grid.append(row)
        return grid
    
    def update_score(self):
        """ Update the score based on the current choice and rule index. """
        # Check if the current choice matches the correct choice in the rule index
        if self.current_choice and self.rule_index.get(self.current_choice) == self.correct_choice:
            self.score += 1
            logging.info(f"Correct choice! Score increased to {self.score}.")
        else:
            logging.info(f"Incorrect choice or no choice made. Score remains {self.score}.")
        self.data["locolizer"]["score"] = self.score

    def grid_plot(self):
        """ Draw labels 1, 2, 3 with colors KEY_1, KEY_2, KEY_3 and place them on white squares. """
        # Define positions for the squares and labels
        self.choice_pos = [(-0.3, -0.4), (0, -0.4), (0.3, -0.4)]
        colors = [COLOR_1, COLOR_2, COLOR_3]
        labels = ['1', '2', '3']

        self.choice_squares = []  # Store references to the choice squares

        for pos, color, label in zip(self.choice_pos, colors, labels):
            # Draw the white square
            square = self.gfx.rect(pos, 0.15, 0.15, fillColor='white', lineColor='black')
            square.setAutoDraw(True)
            self.choice_squares.append(square)

            # Draw the label with the specified color
            text_stim = self.gfx.text(label, pos=pos, color=color, height=0.1)
            text_stim.setAutoDraw(True)

    def highlight_choice(self, index):
        """ Highlight the choice at the given index by changing the border of the square. """
        # Clear any existing highlight
        for i, square in enumerate(self.choice_squares):
            if i == index:
                square.setLineColor(COLOR_HIGHTLIGHT)
                square.setLineWidth(6)
            else:
                square.setLineColor('white')
                square.setLineWidth(1)
    
    def do_timeout(self):
        for i in range(3):
            self.timer_wrap.setColor('red'); self.win.flip()
            wait(0.1)

        self.log('done')
        if self.current_choice is None:
            self.center_message('Warning: No choice made!')
        logging.info('timeout')
        self.done_time = core.getTime()
        self.log('done')
        core.wait(1) 
        self.win.flip()
        self.done = True

    def run(self):
        """ Main loop to run the grid world without highlighting or moving. """
        event.clearEvents()
        self.draw_timer()
        self.start_time = self.current_time = core.getTime()
        self.end_time = None if self.time_limit is None else self.start_time + self.time_limit
        self.start_time = self.tick()
        self.grid_plot()  # Draw the choice squares

        while not self.done:
            self.draw_grid()
            self.win.flip()

            if not self.done and self.end_time is not None and self.current_time > self.end_time:
                self.do_timeout()
                self.done = True
                logging.info(f"Confirmed choice: {self.current_choice}")

            self.tick()

            keys = event.getKeys()

            if KEY_ABORT in keys:
                logging.info("Abort key pressed. Exiting the game.")
                self.done = True
                self.status = 'abort'
            if KEY_CONTINUE in keys:
                self.done = True
            if KEY_1 in keys:
                self.current_choice = '1'
                self.highlight_choice(0)
                self.log('choice', {'choice': '1'})
            elif KEY_2 in keys:
                self.current_choice = '2'
                self.highlight_choice(1)
                self.log('choice', {'choice': '2'})
            elif KEY_3 in keys:
                self.current_choice = '3'
                self.highlight_choice(2)
                self.log('choice', {'choice': '3'})
            if KEY_ABORT in keys:
                logging.info("Abort key pressed. Exiting the game.")
                self.done = True
                self.status = 'abort'

        # Clean up and finish
        self.update_score()
        print('self.triggers', self.triggers)
        self.hide_message()
        self.fade_out()

if __name__ == '__main__':
    win = visual.Window([800, 800], fullscr=False, color='white', units='height')
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0]
    ]
    start_pos = [[3, 3], [3, 4], [4, 3], [4, 4]]
    n = 7
    rule_index = []
    trial_number = 1
    grid_world = Locolizer(win=win, grid=grid, start=start_pos, n=n, trial_number=trial_number, trial_index=0, trial_block=0, rule='default', full_screen=False, tile_size=0.08)
    grid_world.run()
    win.close()
