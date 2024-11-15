from experiment import Experiment
from fire import Fire
import logging
import random

def main(continue_main=None,test_mode=False):
    if test_mode:
        experiment = Experiment(full_screen=True,test_mode=True, n_trial=10)
        experiment.intro()
        experiment.practice_timelimit()
        experiment.run_blocks()
        experiment.intro_locolizer()
        experiment.run_locolizer()
        experiment.save_data()
    if continue_main == None :
        experiment = Experiment(full_screen=True,test_mode=False, n_trial=120)
        experiment.intro()
        experiment.practice_timelimit()
        experiment.run_blocks()
        experiment.intro_locolizer()
        experiment.run_locolizer()
        experiment.save_data()
    else:
        experiment = Experiment(full_screen=True,test_mode=False)
        experiment.run_blocks(start_block = 1)
        experiment.save_data()

    
if __name__ == '__main__':
    Fire(main)