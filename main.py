from experiment import Experiment
from fire import Fire
import logging
import random

def main():
    experiment = Experiment(full_screen=False, n_trial=4)
    experiment.intro()
    experiment.run_blocks()
    experiment.save_data()

    
if __name__ == '__main__':
     Fire(main)