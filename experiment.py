import os
import logging
import json
import re
from datetime import datetime
import psychopy
from psychopy import core, visual, gui, data, event
from psychopy.tools.filetools import fromFile, toFile
import numpy as np
from trials import GridWorld, Locolizer
from config import KEY_DOWN,KEY_UP,KEY_LEFT, KEY_RIGHT, KEY_SELECT, KEY_ABORT, KEY_CONTINUE,KEY_RETURN, COLOR_RED, COLOR_BLUE, COLOR_GREY, COLOR_HIGHTLIGHT, KEY_1, KEY_2, KEY_3, COLOR_1, COLOR_2, COLOR_3
from util import jsonify

from triggers import Triggers
import subprocess
from copy import deepcopy
from config import VERSION
import os

DATA_PATH = f'output/exp/{VERSION}'
SURVEY_PATH = f'output/survey'
CONFIG_PATH = f'config/{VERSION}'
FIG_PATH = f'fig'
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

def get_next_config_number():
    used = set()
    for fn in os.listdir(DATA_PATH):
        m = re.match(r'.*_P(\d+)\.', fn)
        if m:
            used.add(int(m.group(1)))

    possible = range(1, 1 + len(os.listdir(CONFIG_PATH)))
    try:
        n = next(i for i in possible if i not in used)
        return n
    except StopIteration:
        print("WARNING: USING RANDOM CONFIGURATION NUMBER")
        return np.random.choice(list(possible))
    
class AbortKeyPressed(Exception): pass

class Experiment(object):
    def __init__(self,score =0, config_number = None, block_size = 12,start_main_blocks = None, start_post_blocks = None, test_mode=True,name=None, full_screen=True,continue_trial = None, n_trial = None, **kws):
        if config_number is None and continue_trial is None:
            config_number = get_next_config_number()
        elif continue_trial is not None:
            config_number = get_next_config_number() - 1
        self.name = name
        self.full_screen = full_screen
        self.trial_index = 0
        self.survey = None
        self.data = []
        self.block_size = block_size
        self.continue_trial = continue_trial
        if start_main_blocks is None and start_post_blocks is None:
            self.start_blocks = 0
        else:
            self.start_blocks = start_main_blocks + start_post_blocks

        
        timestamp = datetime.now().strftime('%y-%m-%d-%H%M')
        timestamp = datetime.now().strftime('%y-%m-%d-%H%M')
        self.id = f'{timestamp}_P{config_number}'
        if name:
            self.id += '-' + str(name)
        self.setup_logging()
        logging.info('git SHA: ' + subprocess.getoutput('git rev-parse HEAD'))
        fig_path = f'{FIG_PATH}/rule_intro.png'
        with open(fig_path, 'rb') as f:
            self.rule_intro = f.read()
        config_file = f'{CONFIG_PATH}/{config_number}.json'
        with open(config_file) as f:
            conf = json.load(f)
            self.trials = conf['trials']
        if n_trial is None:
            self.n_trial_main = int(len(self.trials['main']))
            self.n_trial_post = int(len(self.trials['post']))
        else:
            self.n_trial_main  = n_trial
            self.n_trial_post = n_trial
        self.rule_index = conf['rule_index']
        print(self.rule_index)
        # self.parameters.update(kws)
        # logging.info('parameters %s', self.parameters)

        self.win = self.setup_window()
        self.total_score = score
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
        self.locolizer_data = []
        self.triggers = self.triggers = Triggers(**({'port': 'dummy'} if test_mode else {}))

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


    def message(self, msg, select=False, tip_text=None):
        logging.debug('message: %s (%s)', msg, tip_text)
        self.show_message()
        self._message.setText(msg)
        self._tip.setText(tip_text if tip_text else f'press {KEY_SELECT} to continue' if select else '')
        self.win.flip()
        if select:
            event.waitKeys(keyList=KEY_SELECT)

        
    def wait_keys(self, keys, time_limit=float('inf')):
        keys = event.waitKeys(maxWait=time_limit, keyList=[*keys, KEY_ABORT])
        if keys and KEY_ABORT in keys:
            self.status = 'abort'
            raise AbortKeyPressed()
        else:
            return keys
    
    def teach_move(self, grid_world, direction_key, instruction):
        """ Guide the user to move in a specific direction with a given instruction. """
        self.message(instruction, select=False)  # Show the instruction without waiting for select key

        while True:
            # Draw the grid and wait for key press
            grid_world.highlight_tile()
            grid_world.draw_grid()
            self.win.flip()

            # Capture key input
            keys = event.getKeys()
            if direction_key in keys:
                if direction_key == KEY_DOWN:
                    grid_world.move_cursor('down')
                elif direction_key == KEY_UP:
                    grid_world.move_cursor('up')
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
        self.message(instruction, select=False)  # Show the instruction without waiting for select key 

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
        self.triggers.send(4)
        self.message('Welcome!', select=True)
        self.message('In this game, you will select squares in a grid to get points.', select=True)
        self.message('Your goal is to uncover all the red tiles while uncovering as few white tiles as possible.', select=True)

        # Load a sample practice grid for movement demonstration
        sample_grid = [
            [0, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0]
        ]
        start_pos = [[2, 1]]
        grid_world = GridWorld(win=self.win, grid=sample_grid, n=4, tile_size=0.1, trial_number=0, time_limit=None,trial_block='practice', trial_index=0, start=start_pos, done_message='You have found all the tiles!')

        # Draw the initial grid
        grid_world.highlight_tile()
        grid_world.draw_grid()
        self.win.flip()

        # Guide the user through the movement steps
        self.teach_move(grid_world, KEY_DOWN, f"Your current location is highlighted. Use key {KEY_DOWN} to move yourself down.")
        # self.teach_move(grid_world, KEY_UP, f"Good! Now press the {KEY_UP} key to move down.")
        self.teach_move(grid_world, KEY_RIGHT, f"Good! Now press the key {KEY_RIGHT} to move right.")
        self.teach_move(grid_world, KEY_LEFT, f"Good! Now press the key {KEY_LEFT} to move left.")
        self.teach_move(grid_world, KEY_DOWN, f"If you press the key {KEY_DOWN} again.")
        self.teach_move(grid_world, KEY_DOWN, f"You will find yourself at the top of the grid. When your hit the boundary, it will start from the other side. Now press the key {KEY_DOWN}.")
        self.teach_select(grid_world, f"Awesome! Now press the key {KEY_SELECT} to reveal where you are.")
        self.message("You will get 1 point for each red tiles, and lost 1 point for each white tile you reveald. The score showing on top of the grids", tip_text = "Reveal all the red tiles to continue.")

        grid_world.run()
        # Final instruction
        self.message(f"You have completed the practice! Please let the experimenter know if you have any questions.", select=True)

        
    @stage
    def practice_timelimit(self):
        sample_grid = [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0]
        ]
        start_pos = [[2, 1]]
        gw = GridWorld(win=self.win, grid=sample_grid, n=4, tile_size=0.1, trial_number=0, trial_block='practice', trial_index=0, start=start_pos, time_limit=7, done_message='You have found all the tiles!')

        self.message("To make things more exciting, each round has a time limit.", select=True)
        gw.draw_grid()
        gw.draw_timer()
        gw.timer.setLineColor('#FFC910')
        gw.timer.setLineWidth(5)
        gw.win.flip()

        self.message("The time left is indicated by a bar on the right.", select=True)
        gw.timer.setLineWidth(0)
        self.message("You need to find all the red tiles before the time runs out, which will give you 3 points bonus!", select=False,
            tip_text='Try to find all the red tiles before the time runs out!')
        gw.run()
        self.message("If you run out of time, the game will end immediately.", select=True)
        self.message("Now you will start the main game. It's harder than the practice!", select=True)
        self.message(f" You have total {self.n_trial_main} trials. Your current score is {self.total_score}.", select=True)
        self.message("Please wait for the experimenter to start the next part.")
        event.waitKeys(keyList=[KEY_CONTINUE])
    
    @stage
    def run_pratice(self):
        """ Run through all the practice trials. """
        for trial in self.trials['practice']:
            logging.info(f"Running trial {self.practice_i + 1}/{len(self.trials['practice'])}")
            grid_data = trial['grid']


    

    @stage
    def run_blocks(self, n_trial_main=None):
        """
        Run through trials in blocks, with breaks between each block.
        Each block consists of a fixed number of trials (e.g., 10 trials).
        """

        start_block = self.start_blocks
        if start_block is None:
            start_block = 0
        

        total_blocks = (self.n_trial_main + self.block_size - 1) // self.block_size  # Calculate total number of blocks
        self.main_blocks = total_blocks
        if self.start_blocks > total_blocks:
            start_block = total_blocks - 1

        # Determine which block to start at (default is 0)
        if start_block >= total_blocks:
            start_block = total_blocks - 1
        block_start_trial = start_block * self.block_size  # Determine starting trial based on block

        # Iterate through the trials in blocks
        for block in range(start_block, total_blocks):
            logging.info(f"Starting block {block + 1}/{total_blocks}")

            # Run each trial in the block
            block_end_trial = min(block_start_trial + self.block_size, self.n_trial_main)
            for trial_index in range(block_start_trial, block_end_trial):
                logging.info(f"Running trial {trial_index + 1}/{self.n_trial_main}")
                trial = self.trials['main'][trial_index]  # Get the trial data
                prm = {**trial}
                gw = GridWorld(win=self.win, trial_index = trial_index,trial_block = block, done_message=self.done_message,triggers=self.triggers, **prm)
                # Run the trial
                gw.run()
                psychopy.logging.flush()
                self.trial_data.append(gw.data)
                self.total_score += gw.data['trial']['score']
                print("gw.data['trial']['score']", gw.data['trial']['score'])
                self.trial_index = trial_index
                print("score is total_score", self.total_score)

                # If we've reached the last trial, show the final message
                if self.trial_index == self.n_trial_main:
                    self.done_message = 'You have finished the largest part of the experiment! Please tell the experimenter that you are ready for the next part.'
                    self.message('You have completed the first part of the experiment!', select=True)
                    logging.info('Main completed.')
                    return  # Exit after the last trial

            if self.trial_index < self.n_trial_main:  # Avoid break if this is the last block
                self.message(
                    f"You have completed Block {block + 1} out of {total_blocks} blocks for the first part of the experiment. Your current score is {self.total_score}. Take a break. Please tell the experimenter if you are ready to the next block.",
                    select=False
                )
                keys = event.waitKeys(keyList=[KEY_CONTINUE, KEY_ABORT])
                if KEY_CONTINUE in keys:
                    self.hide_message()
                    
                if KEY_ABORT in keys:
                    logging.warning('Experiment aborted by user.')
                    self.message('Experiment aborted. Exiting...', select=True)
                    return  # Exit the experiment if the user presses the abort key

            # Move to the next block of trials
            block_start_trial = block_end_trial
    
    @stage
    def intro_locolizer(self, display=False):
        rule_intro_image = visual.ImageStim(self.win, image=f'{FIG_PATH}/rule_intro.png')


        self.message("Now you will start the second part of the experiment. In this part, the game is a bit different.", select=True)
    
        self.message("You see a series of grids with pattern. Those are the examples of the grid from the game you just played.", select=True)
        self.message("Here is the example of the rules. ", select=True)
        
        rule_intro_image.draw()
        self.message("You need to find the rule that generates the pattern on the each row.", select=True)
        rule_intro_image.draw()
        self.message("Take your time to think and remeber those patterns. THIS IS THE LAST TIME YOU CAN SEE THESE PATTERNS.", select=True)
        rule_intro_image.draw()
        self.win.flip()
        self.message("In this part, you need to classify the rule that generates the pattern with the partial grids shown.", select=True)
        trial = self.trials['practice'][0]
        gw = Locolizer(win=self.win,rule_index = self.rule_index,trial_index = self.trial_index,trial_block = -1,triggers=self.triggers,time_limit=5, **trial)
        gw.draw_grid()
        gw.grid_plot()
        gw.draw_timer()
        self.message(f"You need to press key {KEY_1}, key {KEY_2}, or key {KEY_3} to make your choice.", select=True)
        self.message("There is also a time limit for each trial. The time left is indicated by a bar on the right.", select=True)
        gw.timer.setLineColor('#FFC910')
        gw.timer.setLineWidth(5)
        self.message("Your current choice is highlighted. You can always change your choice before the time runs out.", select=True)
        self.message("MAKE YOUR CHOICE NOW!")
        gw.run()
        self.message("You will be compensated for your performance in this part. If your answer is correct, you will get 1 point. If you answer is incorrect, you will lose 1 point. ", select=True)
        self.message("If you are not sure about the answer, you can choose not to make a choice. In this case, you will not get or loss any points.", select=True)
        self.message(f" The starting score is {self.total_score}, which is the score you got from the last part of the experiment.", select=True)
        self.message("Let the experimenter know when you are ready to start the next part.")
        keys = event.waitKeys(keyList=[KEY_RETURN, KEY_CONTINUE])
        if KEY_RETURN in keys:
            self.message("This is the example of the rule you need to learn.")
            rule_intro_image.draw()
            self.win.flip()
            event.waitKeys(keyList=[KEY_CONTINUE])  # Wait for continue after showing the image


    

    @stage
    def run_locolizer(self):    
        # start_block = self.start_blocks - self.main_blocks
        start_block = 0
        num_blocks = 4
        # block_size = 3
        block_size = self.n_trial_post // num_blocks  # Use floor division
        block_start_trial = start_block * block_size 
        total_blocks = start_block + num_blocks
        trials = self.trials['post']
        self.message(f"The experiment starts now. Good luck!", select=True)
        self.hide_message()
        for block in range(start_block, total_blocks):
            block_end_trial = min(block_start_trial + block_size, self.n_trial_post)
            logging.info(f"Running trial {self.trial_index + 1}/{self.n_trial_post}")
            for i in range(block_start_trial, block_end_trial):
                logging.info(f"Running trial {self.trial_index + 1}/{self.n_trial_post}")
                trial = self.trials['post'][i]
                gw = Locolizer(win=self.win,rule_index = self.rule_index,trial_index = self.trial_index,trial_block = block,triggers=self.triggers, **trial)
                gw.run()
                self.trial_index += 1
                psychopy.logging.flush()
                self.locolizer_data.append(gw.data)
                self.total_score += gw.data['locolizer']['score']
                print("self.total_score", self.total_score)
                
                if self.trial_index == self.n_trial_post:
                    self.done_message = 'You have completed the second part of the experiment!'
                    self.message('This is the end of the experiment!', select=True)
                    logging.info('Main completed.')
                    return 
                
            if self.trial_index < self.n_trial_post:  # Avoid break if this is the last block
                self.message(
                    f"You have completed Block {block + 1} out of {total_blocks} blocks for the first part of the experiment. Your current score is {self.total_score}. Take a break. Please tell the experimenter if you are ready to the next block.",
                    select=False
                )
                keys = event.waitKeys(keyList=[KEY_CONTINUE, KEY_ABORT])

                if KEY_CONTINUE in keys:
                    self.hide_message()
                    
                if KEY_ABORT in keys:
                    logging.warning('Experiment aborted by user.')
                    self.message('Experiment aborted. Saving data and exiting...', select=True)
                    return  # Exit the experiment

            # Move to the next block of trials
            block_start_trial = block_end_trial


    @property
    def all_data(self):
        return {
            'trial_data': self.trial_data,
            'practice_data': self.practice_data,
            'locolizer_data': self.locolizer_data,
            'window': self.win.size,
        }

    @stage
    def save_data(self):
        self.message(f'Experiment complete! Total score: {self.total_score}', tip_text="saving data...", select=False)
        psychopy.logging.flush()

        fp = f'{DATA_PATH}/{self.id}.json'
        with open(fp, 'w') as f:
            f.write(jsonify(self.all_data))
        logging.info('wrote %s', fp)

        if self.eyelink:
            self.eyelink.save_data()
        self.message("Data saved! Please let the experimenter that you've completed the study.", select=True,)

    def emergency_save_data(self):
        logging.warning('emergency save data')
        fp = f'{DATA_PATH}/{self.id}.txt'
        with open(fp, 'w') as f:
            f.write(str(self.all_data))
        logging.info('wrote %s', fp)


if __name__ == "__main__":
    experiment = Experiment(full_screen=False, n_trial=4,trial_index=0,start_main_blocks=0,start_post_blocks=0)
    # experiment.intro()
    # experiment.practice_timelimit()
    experiment.run_blocks()
    experiment.intro_locolizer()
    experiment.run_locolizer()
