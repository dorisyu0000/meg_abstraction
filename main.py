from experiment import Experiment
from fire import Fire
import logging
import random

# Running the Experiment
if __name__ == "__main__":

    experiment = Experiment(config_number=1, full_screen=True, n_trial=2)
    experiment.intro()
    experiment.run_main()
    experiment.save_data()