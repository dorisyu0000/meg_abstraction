from experiment import Experiment
from fire import Fire
import logging
import random

def main(continue_main=None):
    if continue_main == None :
        experiment = Experiment(full_screen=False, n_trial=120)
        experiment.intro()
        experiment.run_blocks()
        experiment.save_data()
    else:
        experiment = Experiment(full_screen=False)
        experiment.run_blocks(start_block = continue_main)
        experiment.save_data()

    
if __name__ == '__main__':
    Fire(main)