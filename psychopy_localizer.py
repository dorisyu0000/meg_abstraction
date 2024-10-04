# on the MEG mac: conda activate psychopy_py3
# Please don't install anything in this environment so things stay reproducible.

# if you need to install psychopy from scrath:
# conda create -n psychopy python=3.8 ipython
# conda install psychopy

# ================ #
fullscr = True # set to false when debugging
send_triggers = False # set to False if running locally
skip_localiser = False
skip_sequences = True
# ================ #

from psychopy import visual, core, event, data
from os.path import join
import random, os
from params import parameters
from port_open_send import *
import pickle

directory = os.getcwd()
dir_pictures = join(directory, 'pictures')
dir_logs = join(directory, 'logs/') # to output the logs .csv

# make sure output directories exist
if not os.path.exists(dir_logs):
    os.mkdir(dir_logs)

# send init trigger to refresh channels, else first actual trigger can fail
sendTrigger(parameters['trigger_map']['init'])

print('\n\n')
if not send_triggers:
    print('TRIGGERS SET TO OFF')

print('\n\n')
Participant = input('Participant: ') # participant number is defined by user input here.

'''========================== Objects ======================================='''
# create the objects used to build the experiment
win = visual.Window(monitor="default", units="pix", fullscr=fullscr, colorSpace='rgb255', color=[127,127,127])
prompt = visual.TextStim(win, text='', font='Courier New', wrapWidth=1000, alignHoriz='center', height=40, color=(-1,-1,-1))
image = visual.ImageStim(win, size=(400,400), image=None)
fixation = visual.TextStim(win, text='+', height=60, color=(-1,-1,-1))
red_fixation = visual.TextStim(win, text='+', height=60, color=(1,0,0))
green_fixation = visual.TextStim(win, text='+', height=60, color=(0,1,0))

instructions = visual.TextStim(win,text='', font='Courier New', wrapWidth=700, alignHoriz='center', height=18, color=(-1,-1,-1))
photodiode = visual.Rect(win, width=57, height=57, pos=[-483,355], fillColor=[255,255,255], fillColorSpace='rgb255')
rtClock = core.Clock()
win.mouseVisible = False # This hides the mouse.

'''================================ Timings ================================'''
frame_time_ms = win.monitorFramePeriod * 1000 # get screen refresh rate

fixation_ON_ms = 1000
fixation_OFF_ms = 0
picture_ON_ms = parameters['timing']['localiser_img'] * 1000
picture_OFF_ms = 0

'''========================== Display Functions =============================='''
def present_experimenterControl(text=''):
    '''
    presents instructions, can only advance by pressing "s" on the keyboard. This avoids
    participants accidentally pressing a button and starting the experiment while you set
    things up. **NOTE** the instructions assume the button box is in the participant's left hand
    '''
    instructions.setText(text)
    instructions.draw()
    win.flip()
    return event.waitKeys(keyList=['s'])


def present_instructions(text=''):
    '''
    Participants can press 1 or 2 to advance.
    '''
    instructions.setText(text)
    instructions.draw()
    win.flip()
    return event.waitKeys(keyList=parameters['key_responses'])

def present_fix(frame_time=frame_time_ms, fix_onscreen=fixation_ON_ms, fix_offscreen=fixation_OFF_ms, feedback=None, fix_triggers=False):
    '''
    Fixation cross.
    '''
    if send_triggers and fix_triggers:
        win.callOnFlip(sendTrigger, channel=parameters['trigger_map']['fixation'], duration=0.02) # the trigger will be sent on the next screen refresh. i.e. when win.flip() is called.
    fixation_obj = fixation
    if feedback == False:
        fixation_obj = red_fixation
    if feedback == True:
        fixation_obj = green_fixation
    soa_time = fix_onscreen + fix_offscreen
    for frame in range(1, int(soa_time/frame_time_ms+1)):
        if frame < (fix_onscreen/frame_time_ms):
            fixation_obj.draw()
        win.flip()

def present_picture(img, pic_path, frame_time=frame_time_ms, pic_onscreen=picture_ON_ms, pic_offscreen=picture_OFF_ms, sequence=None):
    soa_time = pic_onscreen + pic_offscreen
    display_tracker = []

    image.setImage(pic_path)
    if send_triggers:
        if sequence:
            win.callOnFlip(sendTrigger, channel=parameters['trigger_map'][sequence], duration=0.01) # the trigger will be sent on the next screen refresh. i.e. when win.flip() is called.
        win.callOnFlip(sendTrigger, channel=parameters['trigger_map']['image'], duration=0.01) # the trigger will be sent on the next screen refresh. i.e. when win.flip() is called.

    for frame in range(1, int(soa_time/frame_time_ms+1)):
        if frame <= (pic_onscreen/frame_time_ms):
            image.draw()
            photodiode.draw()
        time = win.flip()
        if frame == 1:
            display_tracker.append((time, 'ON'))
        if frame == 3:
            display_tracker.append((time, 'OFF'))
    return display_tracker


def present_prompt(word1, word2):
    '''
    Edit this to add some prompts from the trial_list.csv, also keep track of correct answer.
    See commented part towards the end.

    '''
    if send_triggers:
        win.callOnFlip(sendTrigger, channel=parameters['trigger_map']['prompt'], duration=0.02) # the trigger will be sent on the next screen refresh. i.e. when win.flip() is called.
    win.callOnFlip(rtClock.reset)
    prompt.setText(f'{word1}            {word2}') # done the easy way here, but can adjust spacing more accurately. Also see "wrapWidth" in prompt definition above.
    prompt.draw()
    win.flip()
    return event.waitKeys(keyList=['1','2'], timeStamped=rtClock) # expects a 1-2 button press and returns the RT.

def present_text(text, onscreen):
    for frame in range(1, int(onscreen/frame_time_ms+1)):
        if frame < (onscreen/frame_time_ms):
            prompt.setText(text)
            prompt.draw()
        win.flip()


'''===================== Import stim, shuffle, etc  ====================='''
stim = parameters['state_images']['all_states']
word_descriptions = stim + [
      "hat",
      "pen",
      "dog",
      "bed",
      "garden",
      "carrot",
      "phone",
      "bottle",
      "shoe",
      "sofa",
    ]
fl_reps = int(parameters['trial_numbers']['nTrlLocaliser'] / len(stim))
n_blocks = parameters['trial_numbers']['nBlockLocaliser']
if skip_localiser:
    n_blocks = 0
'''===================== Experiment starts here  =========================== '''

present_experimenterControl('Please wait while we set up the brain measurements.')
present_experimenterControl("""
PICTURE VIEWING

We will show you a bunch of different pictures in a row.

After each picture shows up, it will disappear, and then two words will show up.

One of these words will be what the picture you just saw was.

For example, there might be a picture of an apple, then two words: APPLE and PLATE. You would choose APPLE.

""")

present_experimenterControl("""
PICTURE VIEWING

You need to choose either the LEFT or RIGHT word.

Use your MIDDLE finger for LEFT, and your POINTER finger for RIGHT.

Remember to stay very still.
""")

# Create expt handler: this takes care of saving a csv once the script finishes running. alternatively one could write this using standard text writing stuff
exp = data.ExperimentHandler(dataFileName=dir_logs+f'{Participant}_logfile', autoLog=False, savePickle=False)

total_trials_elapsed = 0
last_trial_feedback = None
for block in range(n_blocks):
    present_instructions('Press any button to start.')
    block_stimuli = []
    for i in range(fl_reps):
        block_stimuli += random.sample(stim, len(stim))
    for trial_num in range(parameters['trial_numbers']['nTrlLocaliser']):
        img =  block_stimuli[trial_num]
        image_fname = img + parameters['state_images']['file_ext']
        word_options = [img, random.choice([w for w in word_descriptions if w != img])]
        random.shuffle(word_options)
        word1 = word_options[0]
        word2 = word_options[1]

        # Create ability to quit and save logfile csv so far. else you lose data if you quit halfway through.
        if event.getKeys('q'):
            instructions.setText('Researcher pressed "q" to quit the experiment.\nPress "c" to confirm or "r" to resume')
            instructions.draw()
            win.flip()
            key = event.waitKeys(keyList=['c', 'r'])
            if key[0] == 'c':
                win.close()
                core.quit()

        # Trial presentation
        random_isi = round(random.uniform(*parameters['timing']['localiser_isi']), 1) * 1000 # can add a random ISI
        present_fix(fix_onscreen = random_isi, feedback=last_trial_feedback, fix_triggers=True)
        display_tracker = present_picture(img, pic_path=join(dir_pictures, image_fname))
        resp = present_prompt(word1, word2)
        win.flip() #necessary?

        # Create log
        exp.addData('participant', Participant)
        exp.addData('trial_type', 'localiser')
        exp.addData('display_tracker', display_tracker)
        exp.addData('trial', trial_num + 1)
        exp.addData('block', block + 1)
        exp.addData('ground_truth', img)
        exp.addData('choices', word_options)
        exp.addData('rt', resp[0][1])
        exp.addData('isi', random_isi)
        accuracy = parameters['key_responses'].index(resp[0][0]) == word_options.index(img)
        if accuracy: #look up what the correct answer is, add 1 or 0 for hit/miss
            exp.addData('acc', 1)
        else:
            exp.addData('acc', 0)
        exp.addData('totaltrialnum', total_trials_elapsed)
        exp.addData('resp', resp[0][0]) # add response button to logs

        exp.nextEntry() # moves to next line
        last_trial_feedback = accuracy
        total_trials_elapsed += 1

    present_experimenterControl('End of block ' + str(block+1) + '.\n Please wait for the researcher.')


if skip_sequences == False:
    present_experimenterControl("""
    PICTURE ORDER

    Now we will show you four pictures in a row, then one mixed-up picture. These pictures will be shown really fast.

    Before each group of four pictures, we will show you a specific picture to look for.

    After you see all four pictures, we'll ask you if the picture we said to look for was picture 1, 2, 3 or 4.

    For example, if we tell you to look for APPLE, then show pictures of DOG, SCHOOL, APPLE, PLATE, in order,
    APPLE would be picture "3" because it was the third picture.
    """)

    present_experimenterControl("""
    PICTURE ORDER

    Two number choices will be shown on screen to pick from, for example "1" and "3".

    You will choose the number that matches what place the picture was in.

    Use your MIDDLE finger to choose the LEFT number.
    Use your POINTER finger to choose the RIGHT number.

    Remember to stay very still.
    """)

    speeds = [frame_time_ms*2,frame_time_ms*10]

    sequences = []
    for f in ['sequences4.pkl','sequences3.pkl']:
        with open(f, 'rb') as handle:
            s = pickle.load(handle)
            s = random.sample(s, 2)
            # add speed from speeds to each of the sequences
            for idx, seq in enumerate(s):
                s[idx] = [(x, speeds[idx]) for x in seq]
            # flatten sequences into one list and shuffle
            s = [item for sublist in s for item in sublist]
            s = random.sample(s, len(s))
            sequences += s

    present_instructions('Press any button to start.')
    for idx, seq in enumerate(sequences):
        (cue, seq), speed = seq
        cue = stim[cue]
        seq = [stim[x] for x in seq] + ['mask']

        # Create ability to quit and save logfile csv so far. else you lose data if you quit halfway through.
        if event.getKeys('q'):
            instructions.setText('Experimenter pressed "q" to quit the experiment.\nPress "c" to confirm or "r" to resume')
            instructions.draw()
            win.flip()
            key = event.waitKeys(keyList=['c', 'r'])
            if key[0] == 'c':
                win.close()
                core.quit()

        present_text(cue,1000)
        present_fix(fix_onscreen = 0, fix_offscreen = 700)
        present_fix(fix_onscreen = 300, fix_offscreen = 0)

        display_tracker = []
        for i, img in enumerate(seq):
            image_fname = img + parameters['state_images']['file_ext']
            trigger = None
            if i == 0:
                if len(seq) == 5:
                    trigger = 'sequences4'
                else:
                    trigger = 'sequences3'
            display_tracker += present_picture(img, pic_path=join(dir_pictures, image_fname), pic_onscreen=frame_time_ms*2, pic_offscreen=speed, sequence=trigger)
        present_fix(fix_onscreen = 1000, fix_offscreen = 0)

        correct_order = seq.index(cue) + 1
        options = [correct_order, random.choice([w+1 for w in range(len(seq)-1) if w+1 != correct_order])]
        random.shuffle(options)
        resp = present_prompt(str(options[0]), str(options[1]))
        display_tracker = [((t - display_tracker[0][0])*1000, state) for (t, state) in display_tracker]

        # Create log
        exp.addData('participant', Participant)
        exp.addData('trial_type', 'sequences')
        exp.addData('sequence', seq)
        exp.addData('sequence ISI', speed)
        exp.addData('display_tracker', display_tracker)
        exp.addData('trial', idx + 1)
        exp.addData('choices', options)
        exp.addData('rt', resp[0][1])
        exp.addData('ground_truth', correct_order)
        exp.addData('cue', cue)
        accuracy = parameters['key_responses'].index(resp[0][0]) == options.index(correct_order)
        if accuracy: #look up what the correct answer is, add 1 or 0 for hit/miss
            exp.addData('acc', 1)
        else:
            exp.addData('acc', 0)
        exp.addData('resp', resp[0][0]) # add response button to logs
        exp.nextEntry() # moves to next line
        present_fix(fix_onscreen = 1000, fix_offscreen = 0, feedback=accuracy)
        if idx == 95:
            present_experimenterControl('End of block. Please wait for the researcher.')
            present_instructions('Press any button to start.')
            last_trial_feedback = None

present_experimenterControl('The study is over. Thank you! \n\nPlease stay still while we finalize the measurements.')
win.close()
