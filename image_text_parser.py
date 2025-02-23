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
g_garbage_lines = ['oO', 'Hy', 'ft', 'v', 'Did. B', '‘a', 'nt', 'ar', '00', 'c1', 'c2', 'A', 'Al', 'MN', 'x', '-']

def main():
    #createTxtFilesFromImages()
    createRxs()

def createRxs():
    rxs = {}
    prev_date = ''

    # Read in all txt files
    in_folder = './Text-Files'
    files = os.listdir(in_folder)
    files.sort()
    for filename in files:
        # Start with IMG_0506 for now
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
        task_name_index = line.find(')')
        if line.find('lbs)') + 3 == task_name_index:
            task_name_index = -1
        if task_name_index == -1:
            rest_index = line.find('rest day')
            if rest_index != -1:
                task_name_index = 0
                line = ' ' + line[:rest_index] + ' ' + line[rest_index:]
        if task_name_index == -1:
            clean_line = cleanUpName(line)
            if isSentenceCase(clean_line):
                task_name_index = 0
                line = ' ' + line
        if task_name_index != -1: # Start of task name
            task_name = line[task_name_index+1:].strip()
            task_name = cleanUpName(task_name)
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
            index = task_list.index(line)
            # Comment
            count = 1
            next_real_line = ''
            while index + count < len(task_list) - 1:
                next_real_line = task_list[index + count]
                if not next_real_line.strip():
                    count += 1
                else:
                    break
            if index < len(task_list) - 1 and next_real_line.find(')') != -1 and not isDescription(line):
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


def createTxtFilesFromImages():
    # Defining paths to tesseract.exe  
    pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
    in_folder = './Photos-001'
    out_folder = './Text-Files'

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