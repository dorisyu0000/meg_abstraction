import os
import logging
import json
import re
from datetime import datetime
import psychopy
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import numpy as np
from trials import GridWorld
from config import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_SELECT, KEY_ABORT, COLOR_RED, COLOR_BLUE, COLOR_GREY, COLOR_HIGHTLIGHT
from util import jsonify


import subprocess
from copy import deepcopy
from config import VERSION
import os

DATA_PATH = f'data/exp/{VERSION}'
SURVEY_PATH = f'data/survey'
CONFIG_PATH = f'config/{VERSION}'
LOG_PATH = 'log'
PSYCHO_LOG_PATH = 'psycho-log'
for p in (DATA_PATH, CONFIG_PATH, LOG_PATH, PSYCHO_LOG_PATH, SURVEY_PATH):
    os.makedirs(p, exist_ok=True)

def stage(f):
    def wrapper(self, *args, **kwargs):
        self.win.clearAutoDraw()
        logging.info('begin %s', f.__name__)
        try:
            f(self, *args, **kwargs)
        except:
            stage = f.__name__
            logging.exception(f"Caught exception in stage {stage}")
            if f.__name__ == "run_main":
                logging.warning('Continuing to save data...')
            else:
                self.win.clearAutoDraw()
                self.win.showMessage('The experiment ran into a problem! Press C to continue or Q to quit and save data')
                self.win.flip()
                keys = event.waitKeys(keyList=['c', 'q'])
                self.win.showMessage(None)
                if 'c' in keys:
                    logging.warning(f'Retrying {stage}')
                    wrapper(self, *args, **kwargs)
                else:
                    raise
        finally:
            self.win.clearAutoDraw()
            self.win.flip()


    return wrapper

class AbortKeyPressed(Exception): pass

class Experiment(object):
    def __init__(self, config_number, name=None, full_screen=False,n_trial = None, **kws):
        self.name = name
        self.full_screen = full_screen
        self.trial_index = 0
        self.survey = None
        self.data = []
        if n_trial is None:
            self.n_trial = len(self.trials['main'])
        else:
            self.n_trial = n_trial
        timestamp = datetime.now().strftime('%y-%m-%d-%H%M')
        timestamp = datetime.now().strftime('%y-%m-%d-%H%M')
        self.id = f'{timestamp}_P{config_number}'
        if name:
            self.id += '-' + str(name)

        self.setup_logging()
        logging.info('git SHA: ' + subprocess.getoutput('git rev-parse HEAD'))
        config_file = f'{CONFIG_PATH}/{config_number}.json'
        with open(config_file) as f:
            conf = json.load(f)
            self.trials = conf['trials']
        # self.parameters.update(kws)
        # logging.info('parameters %s', self.parameters)

        self.win = self.setup_window()
        self.total_score = 0
        self.eyelink = None
        self.done_message = 'All red tiles revealed. Moving to next trial in 1 second.'
        self._message = visual.TextBox2(
            self.win,
            '',  # No text initially
            pos=(0, 0.4),  # Centered horizontally, slightly above the middle of the screen
            color='black',
            size=(1, None),  # Full width of the window, height adjusts dynamically
            letterHeight=0.035,  # Font size
            anchor='center'  # Centered anchor point
        )
        self._tip = visual.TextBox2(
            self.win,
            '',  # No text initially
            pos=(0, 0.35),  # Slightly below the message box
            color='black',
            size=(1, None),  # Almost full width of the window
            letterHeight=0.025,  # Slightly smaller font size for tips
            anchor='left'  # Centered anchor point
        )

        # self._practice_trials = iter(self.trials['practice'])
        self.trial_data = []
        self.practice_data = []

    def setup_logging(self):

            logFormatter = logging.Formatter("%(asctime)s [%(levelname)s]  %(message)s")
            rootLogger = logging.getLogger()
            rootLogger.setLevel('DEBUG')

            fileHandler = logging.FileHandler(f"{LOG_PATH}/{self.id}.log")
            fileHandler.setFormatter(logFormatter)
            rootLogger.addHandler(fileHandler)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)
            consoleHandler.setLevel('INFO')
            rootLogger.addHandler(consoleHandler)

            logging.info(f'starting up {self.id} at {core.getTime()}')

            psychopy.logging.LogFile(f"{PSYCHO_LOG_PATH}/{self.id}-psycho.log", level=logging.INFO, filemode='w')
            psychopy.logging.log(datetime.now().strftime('time is %Y-%m-%d %H:%M:%S,%f'), logging.INFO)

    def setup_window(self):
        size = (1350, 750)
        win = visual.Window(size, allowGUI=True, color='white', units='height', fullscr=self.full_screen)
        logging.info(f'Setting up window with size: {size} and full_screen: {self.full_screen}')
        logging.info(f'Created window with size {win.size}')
        win.flip()
        return win

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
        visual.TextBox2(self.win, msg, color='white', letterHeight=.035).draw()
        self.win.flip()
        if space:
            event.waitKeys(keyList=['space'])
    
    def side_message(self, msg, space=False):
        visual.TextBox2(self.win, msg, pos=(-0.5, 0), color='white', letterHeight=.035).draw()
        self.win.flip()
        if space:
            event.waitKeys(keyList=['space'])


    def message(self, msg, space=False, tip_text=None):
        logging.debug('message: %s (%s)', msg, tip_text)
        self.show_message()
        self._message.setText(msg)
        self._tip.setText(tip_text if tip_text else 'press space to continue' if space else '')
        self.win.flip()
        if space:
            event.waitKeys(keyList=['space'])

        
    def wait_keys(self, keys, time_limit=float('inf')):
        keys = event.waitKeys(maxWait=time_limit, keyList=[*keys, KEY_ABORT])
        if keys and KEY_ABORT in keys:
            self.status = 'abort'
            raise AbortKeyPressed()
        else:
            return keys
    
    def teach_move(self, grid_world, direction_key, instruction):
        """ Guide the user to move in a specific direction with a given instruction. """
        self.message(instruction, space=False)  # Show the instruction without waiting for space

        while True:
            # Draw the grid and wait for key press
            grid_world.highlight_tile()
            grid_world.draw_grid()
            self.win.flip()

            # Capture key input
            keys = event.getKeys()
            if direction_key in keys:
                if direction_key == KEY_UP:
                    grid_world.move_cursor('up')
                elif direction_key == KEY_DOWN:
                    grid_world.move_cursor('down')
                elif direction_key == KEY_LEFT:
                    grid_world.move_cursor('left')
                elif direction_key == KEY_RIGHT:
                    grid_world.move_cursor('right')

                # Update the grid after the move
                grid_world.highlight_tile()
                grid_world.draw_grid()
                # self.win.flip()
                break
    def teach_select(self, grid_world, instruction):
        """ Guide the user to select a tile. """
        self.message(instruction, space=False)  # Show the instruction without waiting for space

        while True:
            # Draw the grid and wait for key press
            grid_world.draw_grid()
            self.win.flip()

            # Capture key input
            keys = event.getKeys()
            if KEY_SELECT in keys:
                # Reveal the current tile
                grid_world.reveal_tile()
                grid_world.draw_grid()
                # self.win.flip()
                break
    @stage
    def intro(self):
        """ Show intro instructions and allow user to practice moving the cursor. """
        self.message('Welcome!', space=True)
        self.message('In this game, you will select squares in a grid to get points.', space=True)
        self.message('Your goal is to uncover all the red tiles while uncovering as few blue tiles as possible.', space=True)

        # Load a sample practice grid for movement demonstration
        sample_grid = [
            [0, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0]
        ]
        start_pos = [1, 1]
        grid_world = GridWorld(win=self.win, grid=sample_grid, n=4, tile_size=0.1, trial_number=0, start=start_pos, done_message='You have found all the tiles!')

        # Draw the initial grid
        grid_world.highlight_tile()
        grid_world.draw_grid()
        self.win.flip()

        # Guide the user through the movement steps
        self.teach_move(grid_world, KEY_UP, f"Your current location is highlighted in yellow. Use the {KEY_UP} key to move the highlighted square up.")
        self.teach_move(grid_world, KEY_DOWN, f"Great! Now press the {KEY_DOWN} key to move down.")
        self.teach_move(grid_world, KEY_LEFT, f"Good! Now press the {KEY_LEFT} key to move left.")
        self.teach_move(grid_world, KEY_RIGHT, f"Well done! Now press the {KEY_RIGHT} key to move right.")

        # Teach how to select a tile
        self.teach_select(grid_world, f"Awesome! Now press the {KEY_SELECT} key to reveal the current tile.")
        self.message("You will get 1 point for each red tiles, and lost 1 point for each white tile you reveald. The score showing on top of the grids",tip_text = "Reveal all the red tiles to continue.")

        grid_world.run()
        # Final instruction
        self.message("You have completed the practice! Press space to continue.", space=True)
        self.message(f"Now you will start the main game. You have total {self.n_trial} trials. Good luck!", space=True)

    
    @stage
    def run_pratice(self):
        """ Run through all the practice trials. """
        for trial in self.trials['practice']:
            logging.info(f"Running trial {self.practice_i + 1}/{len(self.trials['practice'])}")
            grid_data = trial['grid']


    @stage
    def run_main(self):
        """ Run through all the main trials. """
        trials = self.trials['main']
        print(self.n_trial)
        for (i, trial) in enumerate(trials):
            try:
                logging.info(f"Running trial {self.trial_index + 1}/{self.n_trial}")
                prm = {**trial}
                print(prm)
                self.win.clearBuffer()
                gw = GridWorld(win=self.win,done_message=self.done_message, **prm)
                gw.run()
                psychopy.logging.flush()
                self.trial_data.append(gw.data)
                self.trial_index += 1
                if self.trial_index == self.n_trial -1:
                    self.done_message = 'You have completed the experiment!'
                if self.trial_index >= self.n_trial:
                    logging.info('All trials completed.')
                    return
                else:
                    self.win.clearBuffer()
            except:
                    logging.exception(f"Caught exception in run_main")
                    self.win.clearAutoDraw()
                    self.win.showMessage(
                        'The experiment ran into a problem! Please tell the experimenter.\n'
                        'Press C to continue or A to abort and save data'
                        )
                    self.win.flip()
                    keys = event.waitKeys(keyList=['c', 'a'])
                    self.win.showMessage(None)
                    print('keys are', keys)
                    if 'c' in keys:
                        continue
                    else:
                        return


    @property
    def all_data(self):
        return {
            'trial_data': self.trial_data,
            'practice_data': self.practice_data,
            'window': self.win.size,
        }

    @stage
    def save_data(self):
        self.message(f'Experiment complete! Total score: {self.total_score}', tip_text="saving data...", space=False)
        psychopy.logging.flush()

        fp = f'{DATA_PATH}/{self.id}.json'
        with open(fp, 'w') as f:
            f.write(jsonify(self.all_data))
        logging.info('wrote %s', fp)

        if self.eyelink:
            self.eyelink.save_data()
        self.message("Data saved! Please let the experimenter that you've completed the study.", space=True,)

    def emergency_save_data(self):
        logging.warning('emergency save data')
        fp = f'{DATA_PATH}/{self.id}.txt'
        with open(fp, 'w') as f:
            f.write(str(self.all_data))
        logging.info('wrote %s', fp)

# Running the Experiment
if __name__ == "__main__":

    experiment = Experiment(config_number=1, full_screen=True, n_trial=2)
    experiment.intro()
    experiment.run_main()
    experiment.save_data()