from experiment import Experiment
from fire import Fire
import logging
import random

def main(config_number=None, name=None, test=False, fast=False, full=False, **kws):
    n_trial = None
    if test and name is None:
        name = 'test'
    if fast:
        n_trial = 4
    # exp = Experiment(config_number, n_trial = n_trial, full_screen=(not test) or full )
    exp = Experiment(config_number, n_trial = n_trial, full_screen=False)
    if test:
        if test == 'survey':
            exp.save_data(survey=True)
        elif test == 'main':
            exp.run_main()
        else:
            exp.intro()
            exp.run_main()
            exp.save_data()
        return
    else:
        try:
            if fast:
                exp.intro()
                exp.run_main()
                exp.save_data()
        except:
            if test:
                exit(1)
            logging.exception('Uncaught exception in main')
            exp.win.clearAutoDraw()
            exp.win.showMessage("Drat! The experiment has encountered an error.\nPlease inform the experimenter.")
            exp.win.flip()
            try:
                exp.save_data()
                raise
            except:
                logging.exception('error on second save data attempt')
                exp.emergency_save_data()
                raise

if __name__ == '__main__':
    Fire(main)