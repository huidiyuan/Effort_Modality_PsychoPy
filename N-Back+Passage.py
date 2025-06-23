from psychopy import visual, core, event, gui, sound
import pandas as pd
import random
import os
from datetime import datetime


# === PARTICIPANT INFO ===

expInfo = {'Participant ID': ''}
dlg = gui.DlgFromDict(expInfo, title='Experiment Information')
if not dlg.OK:
    core.quit()
    
# === CREATE DATA FOLDER ===
data_folder = 'data/'
os.makedirs(data_folder, exist_ok=True)
current_date = datetime.now().strftime("%Y-%m-%d")

# === LOAD PASSAGES & AUDIO FILES ===
df = pd.read_excel("passages.xlsx", header=1)
df.columns = df.columns.str.strip()
df = df.sample(frac=1).reset_index(drop=True)

# === WINDOW SETTINGS ===
win = visual.Window(monitor = "testMonitor", fullscr=True, color='grey', units='pix')

# ASSIGN CONDITIONS
ppt_id = int(expInfo['Participant ID'])
remainder = ppt_id % 4

# === Assign Conditions ===
## Passage difficulty 
if remainder in [1, 3]:
    difficulty = 'easy'
    field_cols = ['Field1', 'Field2', 'Field3']
else:
    difficulty = 'difficult'
    field_cols = ['Field1.1', 'Field2.1', 'Field3.1']
    
## N-Back letter vs. audio 
is_letter_trial = remainder in [1, 2]

if remainder == 1:
    condition = 'letter_easy'
elif remainder == 2:
    condition = 'letter_difficult'
elif remainder == 3:
    condition = 'audio_easy'
else:
    condition = 'audio_difficult'

# Press 9 to escape study
def get_response(key_list, timing=False):
    if timing:
        clock = core.Clock()
        keys = event.waitKeys(keyList=key_list, timeStamped=clock)
        key, rt = keys[0]
        if key == '9':
            win.close()
            core.quit()
        return key, rt
    else:
        keys = event.waitKeys(keyList=key_list)
        if '9' in keys:
            win.close()
            core.quit()
        return keys[0]
        

# === N-BACK ===

# === STIMULI PARAMETERS ===
stim_duration = 2.0
feedback_duration = 1.0
iti_duration = 1.0

letters = list("CGHKPQTW")
audio_folder = "audio-alphabet"

# === FUNC: N-Back training demo 1 ===
def run_training_demo_1(is_letter_trial, win, audio_folder, iti_duration, condition):
    demo_sequence = '0010001101'
    demo_letters = ['G', 'H', 'G', 'P', 'W', 'T', 'W', 'T', 'C', 'T']

    demo_pos_y = 200
    demo_spacing = 60
    highlight_color = 'yellow'
    
    # Create top letter row
    demo_texts = [
        visual.TextStim(win, text=l, color='white', height=40,
                        pos=(-270 + i * demo_spacing, demo_pos_y))
        for i, l in enumerate(demo_letters)
    ]

    # Create highlight and feedback boxes
    demo_box = visual.Rect(win, width=50, height=60, lineColor=highlight_color, pos=(0, 0))
    match_box = visual.Rect(win, width=50, height=60, lineColor=highlight_color, pos=(0, 0))
    response_highlight = visual.Rect(win, width=140, height=60, lineColor=highlight_color, pos=(0, 0))

    # UI elements
    fixation = visual.TextStim(win, text='+', color='white', height=40)
    center_stim = visual.TextStim(win, text='', color='white', height=60, pos=(0, 0))
    bottom_left = visual.TextStim(win, text='D\nDiffer', color='white', pos=(-300, -250), height=30)
    bottom_right = visual.TextStim(win, text='K\nMatch', color='white', pos=(300, -250), height=30)
    incorrect_text = visual.TextStim(win, text="Incorrect\nPress 'SPACE' to move on", color='red', height=40, pos=(0, -80))
    explanation_text = visual.TextStim(win, text='', color='white', height=22, wrapWidth=500)
    
    responses = []
    clock = core.Clock()
    
    for i, letter in enumerate(demo_letters):
        correct_resp = 'k' if demo_sequence[i] == '1' else 'd'
        responded_correctly = False
        
        while not responded_correctly:
            # === ITI Fixation ===
            fixation.draw()
            win.flip()
            core.wait(iti_duration)

            # === DRAW ALL STIMULI ===
            if is_letter_trial:
                # Center letter shown visually
                center_stim.text = letter
                center_stim.draw()
            else:
                # Keep fixation
                fixation.draw()

                # Play audio
                letter_file = os.path.join(audio_folder, f"{letter}.wav")
                snd = sound.Sound(letter_file)
                snd.play()

            # Top row (up to current letter)
            for stim in demo_texts[:i+1]:
                stim.draw()

            # Response cues
            bottom_left.draw()
            bottom_right.draw()

            # Highlight current letter
            demo_box.pos = (-270 + i * demo_spacing, demo_pos_y)
            demo_box.draw()

            win.flip()

            # === RESPONSE ===
            clock.reset()
            keys = event.waitKeys(keyList=['k', 'd'],timeStamped=clock)
            
            response_key = keys[0][0] if keys else None
            rt = keys[0][1] if keys else None
            correct = (response_key == correct_resp) if response_key else None
            
            center_stim.text = letter

            if correct:
                responded_correctly = True
            else:
                # === Feedback Screen ===
                for stim in demo_texts[:i+1]:
                    stim.draw()
                center_stim.draw()
                demo_box.draw()
                bottom_left.draw()
                bottom_right.draw()
                incorrect_text.draw()

                if demo_sequence[i] == '1' and i >= 2:
                    match_box.pos = (-270 + (i - 2) * demo_spacing, demo_pos_y)
                    match_box.draw()
                
                if correct_resp == 'k':
                    response_highlight.pos = (300, -250)
                    explanation_text.text = "This letter is the same as two steps ago, so the correct answer is 'k'."
                    explanation_text.pos = (180, -180)
                else:
                    response_highlight.pos = (-300, -250)
                    explanation_text.text = "This letter is different from two steps ago, so the correct answer is 'd'."
                    explanation_text.pos = (-180, -180)

                response_highlight.draw()
                explanation_text.draw()
                win.flip()

                event.waitKeys(keyList=['space'])  # Wait for user to continue
                responded_correctly = True  # Still move on after explanation
        
            # === Append Response ===
            responses.append({
                'ppt_ID': ppt_id,
                'condition': condition, 
                'section': 'train_1',
                'trial': i + 1,
                'stim': letter,
                'is_target': demo_sequence[i] == 1,
                'response': response_key,
                'rt': rt,
                'correct': correct
            })
        
    return responses

# === FUNC: N-Back training demo 2 ===
def run_training_demo_2(is_letter_trial, win, audio_folder, stim_duration, feedback_duration, iti_duration, condition):
    # === DEMO 2 SETUP ===
    demo_sequence = '0001001001'
    demo_letters = ['W', 'C', 'G', 'C', 'K', 'P', 'K', 'H', 'Q', 'H']
    demo_pos_y = 200
    demo_spacing = 60
    highlight_color = 'yellow'

    # Top letter row
    demo_texts = [
        visual.TextStim(win, text=l, color='white', height=40,
                        pos=(-270 + i * demo_spacing, demo_pos_y))
        for i, l in enumerate(demo_letters)
    ]

    # Visual elements
    fixation = visual.TextStim(win, text='+', color='white', height=40)
    center_stim = visual.TextStim(win, text='', color='white', height=60, pos=(0, 0))
    bottom_left = visual.TextStim(win, text='D\nDiffer', color='white', pos=(-300, -250), height=30)
    bottom_right = visual.TextStim(win, text='K\nMatch', color='white', pos=(300, -250), height=30)
    feedback_stim = visual.TextStim(win, text='', color='white', height=40, pos=(0, 0))
    move_on_text = visual.TextStim(win, text="Please press [SPACE] to move on.", height=20, pos=(0, -80))
    explanation_text = visual.TextStim(win, text='', color='white', height=22, wrapWidth=500)

    demo_box = visual.Rect(win, width=50, height=60, lineColor=highlight_color, pos=(0, 0))
    match_box = visual.Rect(win, width=50, height=60, lineColor=highlight_color, pos=(0, 0))
    response_highlight = visual.Rect(win, width=140, height=60, lineColor=highlight_color, pos=(0, 0))
    
    # === TRIAL LOOP ===
    responses = []
    clock = core.Clock()
    
    for i, letter in enumerate(demo_letters):
        correct_resp = 'k' if demo_sequence[i] == '1' else 'd'
        responded_correctly = False

        while not responded_correctly:
            # === Fixation ITI ===
            fixation.draw()
            win.flip()
            core.wait(iti_duration)

            # === Stimulus Screen ===
            if is_letter_trial:
                center_stim.text = letter
                center_stim.draw()
            else:
                # Keep fixation and play sound
                try:
                    fixation.draw()
                    snd = sound.Sound(os.path.join(audio_folder, f"{letter}.wav"))
                    snd.play()
                except Exception as e:
                    print(f"Audio error: {e}")

            bottom_left.draw()
            bottom_right.draw()
            win.flip()

            # === Wait for Response ===
            clock.reset()
            keys = event.waitKeys(maxWait=stim_duration, keyList=['k', 'd'], timeStamped=clock)
            
            response_key = keys[0][0] if keys else None
            rt = keys[0][1] if keys else None
            correct = (response_key == correct_resp) if response_key else None

            # === Feedback Text ===
            if response_key is None:
                feedback_stim.text = "Too slow"
            elif correct:
                feedback_stim.text = "Correct"
            else:
                feedback_stim.text = "Incorrect"

            if correct:
                feedback_stim.draw()
                win.flip()
                core.wait(feedback_duration)
                responded_correctly = True
            else:
                # === Feedback + Explanation Screen ===
                for stim in demo_texts[:i+1]:
                    stim.draw()
                demo_box.pos = (-270 + i * demo_spacing, demo_pos_y)
                demo_box.draw()

                bottom_left.draw()
                bottom_right.draw()
                feedback_stim.draw()
                move_on_text.draw()

                if demo_sequence[i] == '1' and i >= 2:
                    match_box.pos = (-270 + (i - 2) * demo_spacing, demo_pos_y)
                    match_box.draw()

                if correct_resp == 'k':
                    response_highlight.pos = (300, -250)
                    explanation_text.text = "This letter is the same as two steps ago, so the correct answer is 'k'."
                    explanation_text.pos = (180, -180)
                else:
                    response_highlight.pos = (-300, -250)
                    explanation_text.text = "This letter is different from two steps ago, so the correct answer is 'd'."
                    explanation_text.pos = (-180, -180)

                response_highlight.draw()
                explanation_text.draw()
                win.flip()

                event.waitKeys(keyList=['space'])
                responded_correctly = True
                
            # === Append Response ===
            responses.append({
                'ppt_ID': ppt_id,
                'condition': condition, 
                'section': 'train_2',
                'trial': i + 1,
                'stim': letter,
                'is_target': demo_sequence[i] == 1,
                'response': response_key,
                'rt': rt,
                'correct': correct
            })
        
    return responses

# === FUNC: N-Back Test ===
def run_test(is_letter_trial, win, audio_folder, stim_duration, feedback_duration, iti_duration, condition, section):
    # === N-BACK TASK PARAMETERS ===
    n_back = 2
    total_blocks = 1 # 5 blocks × 10 trials = 50 total
    trials_per_block = 10
    
    # === GENERATE TRIAL SEQUENCE ===
    sequence = []
    sequence.extend([0]*n_back)
    for _ in range(total_blocks):
        block = [1]*3 + [0]*7
        random.shuffle(block)
        sequence.extend(block)
    
    stim_list = []
    for i, is_target in enumerate(sequence):
        if i < n_back:
            stim_list.append(random.choice(letters))
        else:
            if is_target:
                stim_list.append(stim_list[i - n_back])
            else:
                non_match = random.choice(letters)
                while non_match == stim_list[i - n_back]:
                    non_match = random.choice(letters)
                stim_list.append(non_match)
    
    # Visual elements
    fixation = visual.TextStim(win, text='+', color='white', height=40)
    center_stim = visual.TextStim(win, text='', color='white', height=60, pos=(0, 0))
    feedback_stim = visual.TextStim(win, text='', color='white', height=40, pos=(0, 0))

    # === RUN THE TASK ===
    responses = []
    clock = core.Clock()

    for i, letter in enumerate(stim_list):
        # Fixation
        fixation.draw()
        win.flip()
        core.wait(iti_duration)

        # UI elements
        if is_letter_trial:
            center_stim.text = letter
            center_stim.draw()
        else:
            try:
                fixation.draw()
                snd = sound.Sound(os.path.join(audio_folder, f"{letter}.wav"))
                snd.play()
            except Exception as e:
                print(f"Audio error for {letter}: {e}")
        win.flip()       

        clock.reset()
        keys = event.waitKeys(maxWait=stim_duration, keyList=['k', 'd'], timeStamped=clock)

        correct_response = 'k' if i >= n_back and stim_list[i] == stim_list[i - n_back] else 'd'
        response_key = keys[0][0] if keys else None
        rt = keys[0][1] if keys else None
        correct = (response_key == correct_response) if response_key else None

        # Show feedback
        if response_key is None:
            feedback_stim.text = "Too slow"
        elif correct:
            feedback_stim.text = "Correct"
        else:
            feedback_stim.text = "Incorrect"
        feedback_stim.draw()
        win.flip()
        core.wait(feedback_duration)

        responses.append({
            'ppt_ID': ppt_id,
            'condition': condition,
            'section': section,
            'trial': i + 1,
            'stim': letter,
            'is_target': i >= n_back and stim_list[i] == stim_list[i - n_back],
            'response': response_key,
            'rt': rt,
            'correct': correct
        })
        
    return responses

# === BEGINNING STUDY INSTRUCTIONS ====

# Welcome
welcome_text = '''
Welcome! This study has three parts. 

- First, you will see or hear a sequence of letters and determine any letters that are repeated. 
- Next, you will read several passages and answer some questions about them.
- Finally, you will repeat the letter sequence task. 

Press [SPACE] to begin
'''

welcome_page = visual.TextStim(
    win, 
    text= welcome_text, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')

welcome_page.draw()
win.flip()
event.waitKeys(keyList=['space'])

# === N-Back INSTRUCTION ===
# Move on text
move_on_text = visual.TextStim(
    win,
    text="Press [SPACE] to move on.",
    pos=(0, -300), 
    height=22,
    alignText='center',
    color='white',
    wrapWidth=800
)

start_game_text = visual.TextStim(
    win,
    text="Press [SPACE] when you are ready to begin.",
    pos=(0, -300),
    height=22,
    alignText='center',
    color='white',
    wrapWidth=800
)


# N-Back Train 1
n_back_train_1_instruction_1 = '''
Before we begin, let’s practice the letter sequence task. 

In this task, you will {modality} a series of letters one-by-one. 

Your goal is to remember the letter sequence and press:
- K if the current letter is the SAME as the one {modality2} 2 letters ago
- D if it is DIFFERENT
'''.format(
    modality="see" if is_letter_trial else "hear",
    modality2="seen" if is_letter_trial else "heard")

n_back_train_1_instruction_2 = '''
In this practice round, you will see the letters at the top of the screen to help show you the letter sequence. 

The current letter will be highlighted, and if there's a match, the letter from two steps ago will be highlighted too.

You'll get feedback after each answer. If you're wrong, it will explain why. This is so you become familiar with this task. 
'''.format(modality="see" if is_letter_trial else "hear")

n_back_train_1_instruction_3 = '''
Remember, your goal is to press:
- K if the current letter is the SAME as the one {modality} 2 letters ago
- D if it is DIFFERENT
'''.format(modality="seen" if is_letter_trial else "heard")

# N-Back Train 2
n_back_train_2_instruction_1 = """
Great Job! You've learned the basic setup of the task. 

Next, you'll have another practice round. 

In this round: 
    - The letter sequence at the top will no longer be shown. 
    - You'll have limited time to respond, so please respond as quickly and accurately as possible 
    - You'll still recieve feedback, but the letter sequence, highlight boxes, and explaination will only appear if your answer is incorrect.
""".format(modality="see" if is_letter_trial else "hear")

n_back_train_2_instruction_2 = """
Remember, your goal is to press:
- 'K' if the current letter is the SAME as the one {modality} 2 letters ago
- 'D' if it is DIFFERENT
""".format(modality="seen" if is_letter_trial else "heard")

# N-Back Pre Test
n_back_pre_test_instruction_1 = """
You are ready to begin the study! 

The letter list and highlights will not appear in this test session. 
"""

n_back_pre_test_instruction_2 = """
Remember, press:
- 'K' if the current letter is the SAME as the one {modality} 2 letters ago
- 'D' if it is DIFFERENT
Respond as quickly and accurately as you can. You’ll receive short feedback after each response.
""".format(modality="seen" if is_letter_trial else "heard")

# N-Back Post Test
n_back_post_test_instruction = '''
You will complete the letter task again. 
Remember, press:
- K if the current letter is the SAME as the one {modality} 2 letters ago
- D if it is DIFFERENT
Respond as quickly and accurately as you can. You’ll receive short feedback after each response.
'''.format(modality="seen" if is_letter_trial else "heard")


# ================ RUN N-BACK ================

all_responses = []
results = []
# === Instruction: training demo 1 ===
instruction_t1_1 = visual.TextStim(
    win, 
    text=n_back_train_1_instruction_1, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')

instruction_t1_2 = visual.TextStim(
    win, 
    text=n_back_train_1_instruction_2, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')
    
instruction_t1_3 = visual.TextStim(
    win, 
    text=n_back_train_1_instruction_3, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')

# instruction_t1_1
instruction_t1_1.draw()
move_on_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

# instruction_t1_2
instruction_t1_2.draw()
move_on_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

# instruction_t1_3
instruction_t1_3.draw()
start_game_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

# === Run training demo 1 ===
train1_responses = run_training_demo_1(is_letter_trial, win, audio_folder, iti_duration, condition)

# === Instruction: training demo 2 ===
instruction_t2_1 = visual.TextStim(
    win, 
    text=n_back_train_2_instruction_1, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')

instruction_t2_2 = visual.TextStim(
    win, 
    text=n_back_train_2_instruction_2, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')

# instruction_t2_1
instruction_t2_1.draw()
move_on_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

# instruction_t2_2
instruction_t2_2.draw()
start_game_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

# === Run training demo 2 ===
train2_responses = run_training_demo_2(is_letter_trial, win, audio_folder, stim_duration, feedback_duration, iti_duration, condition)


# === Instruction: N-back pre-test === 
instruction_pre_1 = visual.TextStim(
    win, 
    text=n_back_pre_test_instruction_1, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')

instruction_pre_2 = visual.TextStim(
    win, 
    text=n_back_pre_test_instruction_2, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')
    
instruction_pre_1.draw()
move_on_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

instruction_pre_2.draw()
start_game_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

# === Run N-Back Pre Test ===
pre_responses = run_test(is_letter_trial, win, audio_folder, stim_duration, feedback_duration, iti_duration, condition, section = 'pre')

# === PASSAGE ===

# Allow 9 to exit study
def get_response(key_list, timing=False):
    if timing:
        clock = core.Clock()
        keys = event.waitKeys(keyList=key_list, timeStamped=clock)
        key, rt = keys[0]
        if key == '9':
            win.close()
            core.quit()
        return key, rt
    else:
        keys = event.waitKeys(keyList=key_list)
        if '9' in keys:
            win.close()
            core.quit()
        return keys[0]
        

# Instructions

passage_instruction = """
In this next task, you will read three passages, each on a different topic. 

Read each passage carefully to fully understand it.

After each one, you will answer some questions about what you read. Do your best to answer correctly. 

Press [SPACE] to begin.
"""

continue_text = visual.TextStim(
    win,
    text="Press [SPACE] to continue.",
    pos=(0, -300), 
    height=22,
    alignText='center',
    color='white',
    wrapWidth=800
)

passage_instruction_1 = visual.TextStim(
    win, 
    text=passage_instruction, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')

passage_instruction_1.draw()
win.flip()
event.waitKeys(keyList=['space'])

_, rt = get_response(['space'], timing=True)

results.append({
    'participant': ppt_id,
    'topic': 'instructions',
    'trial': 0,
    'question_num': 'instruction_screen',
    'condition': difficulty,
    'response': 'space',
    'reaction_time': rt
})

text_stim = visual.TextStim(win, color='white', height=28, wrapWidth=800, alignText='left', anchorHoriz='center', pos=(0, 0))

# Comprehension questions
def ask_question(row, idx, qnum):
    topic = str(row['Topic'])
    question = str(row[f'Comprehension_Q{qnum}'])
    correct_answer = str(row[f'Comprehension_Q{qnum}_Option_1_answer'])
    options = [correct_answer] + [str(row[f'Comprehension_Q{qnum}_Option_{i}']) for i in range(2, 5)]
    random.shuffle(options)
    correct_key = str(options.index(correct_answer) + 1)

    full_text = f"{question}\n\n"
    for i, opt in enumerate(options):
        full_text += f"{i+1}. {opt}\n"
    text_stim.text = full_text
    text_stim.draw()
    win.flip()

    response, rt = get_response(['1', '2', '3', '4', '9'], timing=True)
    is_correct = (response == correct_key)

    results.append({
        'participant': ppt_id,
        'topic': topic,
        'trial': idx + 1,
        'question_num': str(qnum),
        'condition': difficulty,
        'response': response,
        'correct_key': correct_key,
        'is_correct': is_correct,
        'question': question,
        'correct_answer': correct_answer,
        'option_1': options[0],
        'option_2': options[1],
        'option_3': options[2],
        'option_4': options[3],
        'reaction_time': rt
    })
    core.wait(1)

# Loop through passages
for idx, row in df.iterrows():
    for field in field_cols:
        if pd.isna(row[field]):
            continue
        text_stim.text = str(row[field])
        text_stim.draw()
        continue_text.draw()
        win.flip()
        _, rt = get_response(['space', '9'], timing=True)

        results.append({
            'participant': ppt_id,
            'topic': row['Topic'],
            'trial': idx + 1,
            'question_num': 'passage',
            'condition': difficulty,
            'response': 'space',
            'reaction_time': rt
        })

    core.wait(0.5)
    ask_order = [1, 2]
    random.shuffle(ask_order)
    for qnum in ask_order:
        ask_question(row, idx, qnum)

# === Instruction: N-back Post Test === 
instruction_post = visual.TextStim(
    win, 
    text=n_back_post_test_instruction, 
    color='white', 
    height=28, 
    wrapWidth=800, 
    alignText='left')

instruction_post.draw()
start_game_text.draw()
win.flip()
event.waitKeys(keyList=['space'])

# === Run N-Back Post Test ===
post_responses = run_test(is_letter_trial, win, audio_folder, stim_duration, feedback_duration, iti_duration, condition, section = 'post')

# === Combine responses to one dictionary and save ===
all_responses.extend(train1_responses)
all_responses.extend(train2_responses)
all_responses.extend(pre_responses)
all_responses.extend(post_responses)

# Save combined responses
df = pd.DataFrame(all_responses)
filename = f"data/{ppt_id}-{remainder}-{current_date}_nback.csv"
df.to_csv(filename, index=False)


# Demographic intro screen
text_stim.text = "Finally, please answer some questions about yourself. \n Press [SPACE] to continue."
text_stim.draw()
win.flip()
event.waitKeys(keyList=['space'])

demographics = {}

# Demographic multiple choice questions
def ask_multiple_choice(win, text, key_list, height=28):
    text_stim.text = text
    text_stim.height = height
    text_stim.draw()
    win.flip()
    return event.waitKeys(keyList=key_list)[0]

demographics['participant'] = ppt_id

demographics['Effort'] = ask_multiple_choice(win, "How effortful was this study?\n\n1. Not at all\n2. Slightly\n3. Moderately\n4. Quite a bit\n5. Very much", ['1', '2', '3', '4', '5'])
demographics['Gender'] = ask_multiple_choice(win, "What is your gender?\n\n1. Male\n2. Female\n3. Non-binary\n4. Prefer not to say", ['1', '2', '3', '4'])
demographics['Race'] = ask_multiple_choice(win, "What race do you identify with?\n\n1. Asian\n2. White\n3. Black\n4. Latinx\n5. Multiracial\n6. Prefer not to say", ['1', '2', '3', '4', '5', '6'])
demographics['Education'] = ask_multiple_choice(win, "What is the highest level of education completed?\n\n1. Some high school\n2. High school graduate\n3. 2-year college degree\n4. 4-year college degree\n5. Graduate degree", ['1', '2', '3', '4', '5'])

# Numeric age input
def ask_numeric_response(win, prompt_text, height=28):
    response = ''
    valid = False
    prompt_stim = visual.TextStim(win, text='', pos=(0, 100), height=height, color='white', wrapWidth=800)
    input_stim = visual.TextStim(win, text='', pos=(0, 0), height=height, color='white')
    box = visual.Rect(win, width=500, height=100, fillColor='grey', lineColor='white', pos=(0, 0))
    error_stim = visual.TextStim(win, text='Please enter a valid number.', pos=(0, -300), height=22, color='red')

    while not valid:
        prompt_stim.text = prompt_text
        input_stim.text = response
        prompt_stim.draw()
        box.draw()
        input_stim.draw()
        continue_text.draw()
        win.flip()

        keys = event.getKeys()
        for key in keys:
            if key == 'space':
                if response.isdigit():
                    while 'space' in event.getKeys():
                        continue
                    core.wait(0.1)
                    valid = True
                    break
                else:
                    prompt_stim.draw()
                    box.draw()
                    input_stim.draw()
                    continue_text.draw()
                    error_stim.draw()
                    win.flip()
                    core.wait(1)
            elif key == 'backspace':
                response = response[:-1]
            elif key in '0123456789':
                response += key
            elif key == 'escape':
                win.close()
                core.quit()

    return int(response)

demographics['Age'] = int(ask_numeric_response(win, "In years, what is your age?"))

# Wait for clean space
while event.getKeys(keyList=['space']):
    continue
core.wait(0.1)
event.clearEvents()
event.waitKeys(keyList=['space'])

# Comment section
question_stim = visual.TextStim(win, text='Thank you for taking part in this study! Please let us know if you have any comments or concerns.', pos=(0, 150), height=28, color='white')
response_text = visual.TextStim(win, text='', pos=(0, 0), height=28, color='white', alignText='left', anchorHoriz='center')
continue_stim = visual.TextStim(win, text='Press ENTER to submit', pos=(0, -300), height=22, color='white')
box = visual.Rect(win, width=800, height=200, fillColor='grey', lineColor='white', pos=(0, 0))

response = ''
typing = True

while typing:
    question_stim.draw()
    box.draw()
    response_text.text = response
    response_text.draw()
    continue_stim.draw()

    win.flip()

    keys = event.getKeys()
    for key in keys:
        if key == 'return':
            typing = False
        elif key == 'backspace':
            response = response[:-1]
        elif key == 'space':
            response += ' '
        elif key in ['lshift', 'rshift', 'shift']:
            continue
        elif len(key) == 1:
            response += key

demographics['Comments'] = response


# Save data
pd.DataFrame(results).to_csv(f"data/{ppt_id}-{remainder}-{current_date}_passagedata.csv", index=False)
pd.DataFrame([demographics]).to_csv(f"data/{ppt_id}-{remainder}-{current_date}_demographics.csv", index=False)

win.close()
core.quit()