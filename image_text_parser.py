from PIL import Image 
import pytesseract
import os
import datetime
import json
import string

'''
To run use: python3 image_text_parser.py

rxs = {
    '2/21/2025': { 
        'activities': [
            {
                'name': 'Systemic 4/45 min'
                'tasks': [
                    {
                    'name': 'Dumbbell Incline Skull Crusher'
                    'video': 'https://www.youtube.com/embed/asdf'
                    'details': ['3x10 reps at 3010, rest 30s', '*Take this to a floor press if you need help']
                    'comments': 'no weight'
                    }
                ]
            }
        ]
    }
}
'''
g_garbage_lines = ['oO', 'Hy', 'ft', 'v', 'Did. B', '‘a', 'nt', 'ar', '00', 'c1', 'c2', 'A', 'Al', 'MN', 'x', '-', '@)', 'YOUR DAILY RX', 'Home', 'CALENDAR', '2v1N ranc M) 201N ract 2Ne', 'd.', 'A 20A ND vact 90', 'x icth+ Clava ctan.', 'a ~ A']
known_tasks = ['Standing cable rear delt fly', 'Facing away dual cable curl', 'Wide grip upper back pull down']
known_comments = ['10,15,15']
exercise_videos = {
    "seated low cable row": "https://www.youtube.com/embed/J9h9AZnXXpo",
    "lying hamstring curl": "https://www.youtube.com/embed/jxctD6fL_FQ",
    "rear foot elevated split squat": "https://www.youtube.com/embed/3fxmRoIE_fk",
    "rope cable tricep pushdown": "https://www.youtube.com/embed/y6EdXBdL75A",
    "standing cable rear delt fly": "https://www.youtube.com/embed/JENKmsEZQO8",
    "facing away dual cable curl": "https://www.youtube.com/embed/xrQlkUQCKQY",
    "barbell glute bridge": "https://www.youtube.com/embed/DQv1IMQDbE4",
    "seated banded row": "https://www.youtube.com/embed/Jy-WCFAofBY",
    "prone db reverse fly": "https://www.youtube.com/embed/Z__dp9rhlcw",
    "cable bicep curl": "https://www.youtube.com/embed/dH7xKAXOkJM",
    "standing calf raise": "https://www.youtube.com/embed/LnWEIjIls-M",
    "db bent knee rdl": "https://www.youtube.com/embed/6_F82F5thmE",
    "banded single arm lat pulldown": "https://www.youtube.com/embed/s0MDw2_2Zs8",
    "hip abduction machine": "https://www.youtube.com/embed/pVGCaMmxuEg",
    "low cable lateral raise": "https://www.youtube.com/embed/Z5FA9aq3L6A",
    "plate deltoid plate raise": "https://www.youtube.com/embed/hikbChhbeLI",
    "roman chair back extension for glutes": "https://www.youtube.com/embed/w5QPcMaT_DQ",
    "reverse crunch": "https://www.youtube.com/embed/aIyadD7d7OA",
    "front rack kb march": "https://www.youtube.com/embed/6lE9Q3QUPsQ",
    "neutral grip shoulder press machine": "https://www.youtube.com/embed/LEhz8ZXNWaY",
    "leg extension machine": "https://www.youtube.com/embed/s1JfTvyWdTs",
    "supinated grip body row": "https://www.youtube.com/embed/zbLAEQ3e9gw",
    "smith machine reverse lunge": "https://www.youtube.com/embed/TK-5lUZZUOs",
    "leg press machine press": "https://www.youtube.com/embed/B8KqmwdomoU",
    "quadruped floating shoulder touches": "https://www.youtube.com/embed/h2OEyxPZYLs",
    "leg press machine narrow stance": "https://www.youtube.com/embed/6GT9o4Cp1vA",
    "dumbbell neutral grip bench press": "https://www.youtube.com/embed/Q7omzf7Bt1I",
    "chest supported db y raise": "https://www.youtube.com/embed/wWhG-7CQQmg",
    "dumbbell incline skull crusher": "https://www.youtube.com/embed/G4Vdjr-byjE",
    "incline chest press machine": "https://www.youtube.com/embed/ArMbAy4emuA",
    "cable fly-high to low": "https://www.youtube.com/embed/H4XsZz3JmJ8",
    "dumbbell lateral raise": "https://www.youtube.com/embed/8aUc9snLOxU",
    "smith machine back squat": "https://www.youtube.com/embed/QcmonZUuumg",
    "dumbbell bent over row to hip": "https://www.youtube.com/embed/xUgh5CIlbk8",
    "dumbbell romanian deadlift": "https://www.youtube.com/embed/6USOovx8pYI",
    "seated alternating dumbbell press": "https://www.youtube.com/embed/ZjWq4wTEuSI",
    "dumbbell front foot elevated split squat": "https://www.youtube.com/embed/OFmW8Re5Zos",
    "extended side plank": "https://www.youtube.com/embed/h2TOAz3BJ_Q",
    "smith machine deadlift": "https://www.youtube.com/embed/igHvWuP2MDU",
    "glute bridge dumbbell floor press": "https://www.youtube.com/embed/5bM4JL4Xlio",
    "goblet russian step-up": "https://www.youtube.com/embed/RZsegx5MjMg",
    "cable lat pulldown": "https://www.youtube.com/embed/ShqtJk37UPM",
    "cyclist goblet squat": "https://www.youtube.com/embed/TysYZ7rKhpM",
    "farmer's carry": "https://www.youtube.com/embed/vW81EITekU0",
    "split squat": "https://www.youtube.com/embed/Py2Qeg-D5T0",
    "assisted pull-up machine": "https://www.youtube.com/embed/ZAR5EiNq1rg",
    "dumbbell bench press": "https://www.youtube.com/embed/ZaDlbm8E8Tg",
    "ghd hip extension": "https://www.youtube.com/embed/yNvAeCrTFuk",
    "cable standing pallof press": "https://www.youtube.com/embed/syYBcVbEAFk",
    "hack squat machine": "https://www.youtube.com/embed/sw-5KcVZVk8",
    "cable oblique rotation": "https://www.youtube.com/embed/rB0GwKy8UMg",
    "goblet lateral box step down": "https://www.youtube.com/embed/aeZqZ3sKV8U",
    "single arm farmer's carry": "https://www.youtube.com/embed/28BIZccT5fs",
    "kettlebell romanian deadlift": "https://www.youtube.com/embed/mVSgE9S0G4w",
    "goblet cable front foot elevated split squat": "https://www.youtube.com/embed/adGM191e6Vk",
    "front squat": "https://www.youtube.com/embed/ddJklKFk2yg",
    "bent over barbell row": "https://www.youtube.com/embed/9Gf-Ourup_k",
    "sissy squat": "https://www.youtube.com/embed/_kuzM5gKU8U",
    "goblet squat": "https://www.youtube.com/embed/pEGfGwp6IEA",
    "walking lunge": "https://www.youtube.com/embed/6wZoPedlpok",
    "push-up": "https://www.youtube.com/embed/Ql8PKKsDE70",
    "air squat": "https://www.youtube.com/embed/iiKn5FiVUjI",
    "superman": "https://www.youtube.com/embed/v4nNlF3WDs0",
    "dead bug": "https://www.youtube.com/embed/ciu7aVuqdgM?si=j1s2yVslvvJcCGjS",
    "hip cars": "https://www.youtube.com/embed/2mY_PkJ4Hl4",
    "90/90 hip switch": "https://www.youtube.com/embed/m51AZSXMvEA",
    "front rack dumbbell elevator squat": "https://www.youtube.com/embed/iBupRh7nuPo",
    "dumbbell 3 point row": "https://www.youtube.com/embed/iLhwICt4R9A",
    "dumbbell external rotation": "https://www.youtube.com/embed/t5Ft8OMG_D8",
    "dumbbell split squat": "https://www.youtube.com/embed/Wcmg-3iHwjQ",
    "2 point bird dog": "https://www.youtube.com/embed/FWjz8ozyVq8",
    "seated calf raise machine": "https://www.youtube.com/embed/2Q-HQ3mnePg",
    "db bent knee rdl (glute bias)": "https://www.youtube.com/embed/WIcpu2UkJoY",
    "wide grip upper back pull down": "https://www.youtube.com/embed/g6wTsj0sj5s",
    "weighted ghd hip extension": "https://www.youtube.com/embed/CHRbTdJF_0M",
    "barbell split squat": "https://www.youtube.com/embed/iHkBjcx9CiQ",
    "decline weighted sit-up": "https://www.youtube.com/embed/PhvG-BQgnBU",
    "cable single arm external rotation": "https://www.youtube.com/embed/3DMyOwvPbIE",
    "supinated bent over barbell row": "https://www.youtube.com/embed/ribtD2d8cs4",
    "back squat": "https://www.youtube.com/embed/j-KDHkRMer0",
    "dumbbell pullover": "https://www.youtube.com/embed/CSkSflHdC3A",
    "dumbbell deadlift": "https://www.youtube.com/embed/zfuc5ynsTlc",
    "med ball side plank": "https://www.youtube.com/embed/AjuVhICRSkc",
    "cable cyclist goblet squat": "https://www.youtube.com/embed/3-jDnH1noxI",
    "single arm cable lat pulldown machine": "https://www.youtube.com/embed/HBC5s98wXko",
    "dumbbell floor press": "https://www.youtube.com/embed/jjlekYs1cfQ",
    "bent over dumbbell row": "https://www.youtube.com/embed/aVH_cG4UISc",
    "dumbbell front squat": "https://www.youtube.com/embed/7CuKlSgu1B0",
    "single arm dumbbell bench press": "https://www.youtube.com/embed/q3cXdiyY7-Q",
    "dumbbell reverse lunge": "https://www.youtube.com/embed/Q2k3kYbtOcI",
    "seated dumbbell press": "https://www.youtube.com/embed/RgkzQ008m3I",
    "hack samat machine": "https://www.youtube.com/embed/sw-5KcVZVk8"
}

def main():
    #createTxtFilesFromImages()
    #createRxs()
    loadWarmups()

def createRxs():
    rxs = {}
    prev_date = ''

    # Read in all txt files
    in_folder = './Text-Files/Workouts'
    files = os.listdir(in_folder)
    files.sort()
    for filename in files:
        if filename.endswith(".txt"):
            filepath = os.path.join(in_folder, filename)
            try:
                with open(filepath, 'r') as file:
                    text = file.read()
                    #print(f"Contents of {filename}:\n{text}\n---")
                    prev_date = processOneText(text, rxs, prev_date)
            except Exception as e:
                print(f"Error processing {filename}: {'{}: {}'.format(type(e).__name__, e)}")
    #print(json.dumps(rxs, sort_keys = True, indent = 4))
    with open('./JSON/data.json', 'w', encoding='utf-8') as f:
        json.dump(rxs, f, ensure_ascii=False, indent=4)

def processOneText(text, rxs, prev_date):
    date = getDate(text)
    activity = {}
    activity_name = ''
    if not date:
        if prev_date:
            if prev_date in rxs:
                if 'tasks' in rxs[prev_date]['activities'][-1]:
                    last_task = rxs[prev_date]['activities'][-1]['tasks'][-1]
                    # The task name might span multiple lines so only get the first 26 characters
                    last_task_name = last_task['name'][:26] if len(last_task['name']) > 25 else last_task['name']
                    last_task_index = text.find(last_task_name)
                    if last_task_index != -1:
                        text = text[last_task_index-4:] # remove everything above that we've already seen
                activity = rxs[prev_date]['activities'][-1]
    else:
        activity_name = getActivityName(text)
    text = removeUnrelatedText(text, activity_name)
    if 'RestDay' in activity_name:
        activity_name = 'Rest Day'
    is_existing_task = not date
    if (date and not activity_name) and not (date == '1/16/2025' or date == '1/14/2025'):
        activity_name = 'Systemic'
    getActivityDetails(text, activity, activity_name, is_existing_task)
    #print(json.dumps(activity, sort_keys = True, indent = 4))
    if date:
        prev_date = date
    if prev_date:
        if date and prev_date in rxs and 'activities' in rxs[prev_date]:
            rxs[prev_date]['activities'].append(activity)
        rxs[prev_date] = { 'activities': [activity] } # Use the prev date if we did not get one
    return prev_date

def getActivityDetails(text, activity, activity_name, is_existing_task):
    if activity_name:
        activity['name'] = activity_name
    is_prev_task_name = False
    is_prev_failure = False
    num_tasks = 0
    task_list = text.split('\n')
    prev_line = ''
    for line in task_list:
        if not line.strip() or any(ext in line for ext in ['©', '®', 'tt a @']) or line.strip() in g_garbage_lines:
            is_prev_task_name = False
            continue
        line = line.strip()
        line = cleanUpName(line)
        task_name = getTaskName(line)
        if task_name and not is_prev_task_name: # Start of task name
            if not task_name or any(ext in task_name for ext in ['©']):
                continue
            task_name = fixTaskName(task_name)
            is_prev_task_name = True
            is_prev_failure = False
            num_tasks += 1
            if num_tasks > 1:
                is_existing_task = False
            if is_existing_task: # Already saw this task
                continue
            if 'tasks' not in activity:
                activity['tasks'] = [{ 'name': task_name }]
            else:
                activity['tasks'].append({ 'name': task_name })
            # youtube video
            activity['tasks'][-1]['video'] = getVideo(task_name)
        elif is_prev_task_name and (line[:1].isupper() or ('Split Squat' in line)): # End of task name
            if is_existing_task:
                continue
            activity['tasks'][-1]['name'] += ' ' + line.strip()
            is_prev_task_name = False
            is_prev_failure = False
            # youtube video
            activity['tasks'][-1]['video'] = getVideo(activity['tasks'][-1]['name'])
        else: # Lines of description and comments
            is_prev_task_name = False
            if 'tasks' not in activity:
                    continue
            index = task_list.index(line) if line in task_list else -1
            # Comment
            count = 1
            next_real_line = ''
            while index != -1 and index + count < len(task_list) - 1:
                next_real_line = task_list[index + count]
                if not next_real_line.strip():
                    count += 1
                else:
                    break
            if isComment(line, prev_line) or (is_prev_failure and not isDescription(line)) or (index != -1 and index < len(task_list) - 1 and next_real_line.find(')') != -1 and not isDescription(line)):
                is_prev_failure = False
                if 'comments' not in activity['tasks'][-1]:
                    activity['tasks'][-1]['comments'] = [line.strip()]
                else:
                    if is_existing_task and line.strip() in activity['tasks'][-1]['comments']:
                        continue
                    activity['tasks'][-1]['comments'].append(line.strip())
            else: # Description
                line = cleanUpName(line).strip()
                if 'fail' in line:
                    is_prev_failure = True
                if 'details' not in activity['tasks'][-1]:
                    activity['tasks'][-1]['details'] = [line.strip()]
                else:
                    if is_existing_task and line.strip() in activity['tasks'][-1]['details']:
                        continue
                    activity['tasks'][-1]['details'].append(line.strip())
        prev_line = line

def getTaskName(line):
    task_name_index = line.find(')')
    is_task_name = False
    if 'lbs)' in line:
        return ''
    if '30s' in line or '60s' in line:
        return ''
    rest_index = line.find('rest day')
    if rest_index != -1:
        line = line[:rest_index] + ' ' + line[rest_index:]
        return line
    if isSentenceCase(line):
        if task_name_index != -1:
            line = line[task_name_index+1:].strip()
        is_task_name = True
    elif task_name_index != -1:
        line = line[task_name_index+1:].strip()
        is_task_name = True
    elif any(name in line for name in known_tasks):
        is_task_name = True
    if is_task_name:
        bad_starts = ['_', '\\_']
        for start in bad_starts:
            if line.startswith(start):
                line = line[len(start):].strip()
                break
        return line
    return ''

def fixTaskName(task_name):
    index = task_name.find('Extensionfor')
    if index != -1:
        task_name = task_name[:index + 9] + ' ' + task_name[index + 9:]
    index = task_name.find('BarbellRow')
    if index != -1:
        task_name = task_name[:index + 7] + ' ' + task_name[index + 7:]
    return task_name    

def isDescription(line):
    if len(line) > 10 or line.find('x3 sets') != -1 or line.find('rest 30') != -1 or line.find('3x10 @') != -1 or line.find('3x10') != -1 or line.find('30 bt sets') != -1 or line.find('*Weight optional') != -1 or line.find('record time') != -1 or line.find('log weight') != -1 or line.find('Chest') != -1 or line.find('Min 30min') != -1 or line.find('Log below') != -1:
        return True
    if line.startswith('*'):
        return True
    return False

def isComment(line, prev_line):
    if 'did ' in line.lower() or 'did ' in prev_line.lower():
        return True
    if all(txt.strip().isdigit() for txt in ''.join(''.join(line.split(' ')).split(','))):
        return True
    return False

def isSentenceCase(line):
    line = ' '.join(line.split('-'))
    words_list = line.strip().split(' ')
    if len(words_list) < 2:
        return False
    if any(char.isdigit() for char in line):
        return False
    words = ' '.join(words_list[:3])
    cap_words = string.capwords(words)
    is_sentence = all(word == cap_word or word == word.upper() for word, cap_word in zip(words, cap_words))
    if is_sentence:
        return True
    return False

def getDate(text):
    # Get the current date if there is one
    date = ''
    start_index = 0
    
    while True:
        index = text.find(',', start_index)
        if index == -1:
            break  # Substring not found
        year = text[index+1:index+6].strip()
        day = text[index-2:index].strip()
        if year.isdigit() and day.isdigit():
            dt_name = text[index-6:index+6].strip('\n')
            dt_list = dt_name.split(',')
            dt_list[1] = dt_list[1].strip()
            dt_name = ','.join(dt_list)
            try:
                dt = datetime.datetime.strptime(dt_name, '%b %d,%Y')
            except Exception as e:
                print(f"Error: {'{}: {}'.format(type(e).__name__, e)}")
                start_index = index + 1  # Move past the found substring for the next search
                continue
            date = dt.strftime('%-m/%-d/%Y')
            break # Found the date
        start_index = index + 1  # Move past the found substring for the next search
    return date

def getActivityName(text):
    # Get the activity title if there is one
    activity_name = ''
    index = text.find('YOUR DAILY RX')
    if index != -1:
        text = text[index:]
        line_list = text.split('\n')
        activity_name = line_list[1]
        if not activity_name.strip():
            activity_name = line_list[2]
        if activity_name.find('FLUSH') != -1:
            if line_list[2].find('Lifestyle') != -1:
                activity_name = line_list[2]
    activity_name_list = activity_name.split(' ')
    activity_name_list = [x for x in activity_name_list if x.isalpha() or '-' in x]
    activity_name = ' '.join(activity_name_list)
    activity_name = cleanUpName(activity_name)
    if activity_name in g_garbage_lines:
        activity_name = ''
    return activity_name

def removeUnrelatedText(text, activity_name):
    # Get rid of useless text at start and end
    if activity_name:
        index = text.find(activity_name)
        new_line_index = text.find('\n', index)
        if new_line_index != -1:
            text = text[new_line_index+1:]
    else:
        index = text.find('YOUR DAILY RX')
        if index != -1:
            text = text[index:]
        index = text.find('be constantly consistent')
        if index != -1:
            new_index = text.find('\n', index)
            if new_index != -1:
                text = text[new_index:]
            else:
                text = text[index:]
    index = text.find('COMMENTS')
    if index != -1:
        new_index = text.rfind('\n', 0, index + 1)
        if new_index != -1:
            text = text[:new_index]
        else: 
            text = text[:index]
    index = text.find('Home Notifications')
    if index != -1:
        text = text[:index]
    index = text.find('Notifications')
    if index != -1:
        text = text[:index]
    text = text.strip()
    return text

def cleanUpName(name):
    bad_endings = [' =v', 'Vv', ' v', ' vv', ' x', 'v Bo', 'Bo', '- Bi', 'v Bi', 'Bi', '=', '~', '&', ' -', ' y', 'v Ho', ' BO', ' -v', ' g', ' Al', ' Z']
    for end in bad_endings:
        if name.endswith(end):
            name = name[:len(name) - len(end)].strip()
            break
    return name

def loadWarmups():
    data = {}
    with open('./JSON/data.json') as f:
        data = json.load(f)
    in_folder = './Text-Files/Warmups'
    date_string = '2/10/2025'
    date = datetime.datetime.strptime(date_string, '%m/%d/%Y')
    rest_days = [12, 15, 16, 19, 22, 23, 26, 1, 2]
    files = os.listdir(in_folder)
    files.sort()
    for filename in files:
        if filename.endswith(".txt"):
            filepath = os.path.join(in_folder, filename)
            try:
                with open(filepath, 'r') as file:
                    text = file.read()
                    date_string = date.strftime('%-m/%-d/%Y')
                    addWarmup(data, text, date_string)
                    date += datetime.timedelta(days=1)
                    while date.day in rest_days:
                        date += datetime.timedelta(days=1)
            except Exception as e:
                print(f"Error processing {filename}: {'{}: {}'.format(type(e).__name__, e)}")
    with open('./JSON/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def addWarmup(data, warmups_text, date_string):
    # Cleanup
    top_index = warmups_text.find('Warmup >')
    if top_index != -1:
        new_index = warmups_text.find('\n', top_index)
        if new_index != -1:
            warmups_text = warmups_text[new_index:]
        else:
            warmups_text = warmups_text[top_index:]
    bottom_index = warmups_text.find('COMMENT')
    if bottom_index != -1:
        new_index =warmups_text.rfind('\n', 0, bottom_index)
        if new_index != -1:
            warmups_text = warmups_text[:new_index]
        else:
            warmups_text = warmups_text[:bottom_index]
    # Add Warmup to Data
    warmup_list = warmups_text.split('\n')
    warmup_list = [s.strip() for s in warmup_list]
    warmup_list = [s for s in warmup_list if s]
    data[date_string]['activities'][0]['warmup'] = warmup_list

def getVideo(task_name):
    task_key = task_name.lower()
    if task_key in exercise_videos:
        return exercise_videos[task_key]
    return ''

def createTxtFilesFromImages():
    # Defining paths to tesseract.exe  
    pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
    in_folder = './Photos-001'
    out_folder = './Text-Files/Workouts'
    #in_folder = './Warmups'
    #out_folder = './Text-Files/Warmups'

    dir_list = os.listdir(in_folder)
    dir_list.sort()
    # iterate through the names of contents of the folder
    for image_path in dir_list:
        # Opening the image & storing it in an image object 
        #print(image_path)
        out_filename = out_folder + '/' + image_path.replace('PNG', 'txt')
        if os.path.exists(out_filename):
            print('Error: txt file already exists for ' + image_path)
            continue
        img = Image.open(in_folder + '/' + image_path) 
        # Extract the text from the image 
        text = pytesseract.image_to_string(img) 
        with open(out_filename, 'w') as file:
            file.write(text)

if __name__ == '__main__':
    main()