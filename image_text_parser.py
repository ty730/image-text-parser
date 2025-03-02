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
                    'details': ['3x10 reps at 3010, rest 30s', '*Take this to a floor press if you need help']
                    'comments': 'no weight'
                    }
                ]
            }
        ]
    }
}
'''
g_garbage_lines = ['oO', 'Hy', 'ft', 'v', 'Did. B', '‘a', 'nt', 'ar', '00', 'c1', 'c2', 'A', 'Al', 'MN', 'x', '-', '@)']

def main():
    #createTxtFilesFromImages()
    createRxs()
    #loadWarmups()

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
                    last_task_index = text.find(last_task['name'])
                    if last_task_index != -1:
                        text = text[last_task_index-4:] # remove everything above that we've already seen
                activity = rxs[prev_date]['activities'][-1]
    else:
        activity_name = getActivityName(text)
    text = removeUnrelatedText(text, activity_name)
    is_existing_task = not date
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
    num_tasks = 0
    task_list = text.split('\n')
    for line in task_list:
        if not line.strip() or any(ext in line for ext in ['©', '®', 'tt a @']) or line.strip() in g_garbage_lines:
            is_prev_task_name = False
            continue
        line = line.strip()
        line = cleanUpName(line)
        task_name = getTaskName(line)
        if task_name: # Start of task name
            if not task_name or any(ext in task_name for ext in ['©']):
                continue
            is_prev_task_name = True
            num_tasks += 1
            if num_tasks > 1:
                is_existing_task = False
            if is_existing_task: # Already saw this task
                continue
            if 'tasks' not in activity:
                activity['tasks'] = [{ 'name': task_name }]
            else:
                activity['tasks'].append({ 'name': task_name })
        elif is_prev_task_name and line[:1].isupper(): # End of task name
            if is_existing_task:
                continue
            activity['tasks'][-1]['name'] += ' ' + line.strip()
        else: # Lines of description and comments
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
            if index != -1 and index < len(task_list) - 1 and next_real_line.find(')') != -1 and not isDescription(line):
                if 'comments' not in activity['tasks'][-1]:
                    activity['tasks'][-1]['comments'] = [line.strip()]
                else:
                    if is_existing_task and line.strip() in activity['tasks'][-1]['comments']:
                        continue
                    activity['tasks'][-1]['comments'].append(line.strip())
            else: # Description
                line = cleanUpName(line).strip()
                if 'details' not in activity['tasks'][-1]:
                    activity['tasks'][-1]['details'] = [line.strip()]
                else:
                    if is_existing_task and line.strip() in activity['tasks'][-1]['details']:
                        continue
                    activity['tasks'][-1]['details'].append(line.strip())

def getTaskName(line):
    task_name_index = line.find(')')
    if 'lbs)' in line:
        return ''
    if '30s' in line or '60s' in line:
        return ''
    rest_index = line.find('rest day')
    if rest_index != -1:
        line = line[:rest_index] + ' ' + line[rest_index:]
        return line
    if isSentenceCase(line):
        return line
    if task_name_index != -1:
        return line[task_name_index+1:].strip()
    return ''

def isDescription(line):
    if len(line) > 10 or line.find('x3 sets') != -1 or line.find('rest 30') != -1 or line.find('3x10 @') != -1 or line.find('3x10') != -1 or line.find('30 bt sets') != -1 or line.find('*Weight optional') != -1 or line.find('record time') != -1 or line.find('log weight') != -1 or line.find('Chest') != -1 or line.find('Min 30min') != -1 or line.find('Log below') != -1:
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
    if (cap_words == words):
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
    #print('Date: ' + date)
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
    activity_name_list = [x for x in activity_name_list if x.isalpha()]
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
    index = name.find('v')
    if index > len(name) - 2:
        name = name[:index].strip()
    index = name.find('x')
    if index > len(name) - 2:
        name = name[:index].strip()
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