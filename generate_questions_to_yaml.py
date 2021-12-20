# coding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility

import re
import yaml
regex = r"^(?=.*?[a-zA-Z])(?=.*?[0-9])"

with open('questions.txt') as file:
    content = {}
    answers = ''
    for line in file:
        matches = re.search(regex, line.rstrip())
        # if 'Environmental Justice' in line:
        #     print('')
        if (
            matches
            and len(line.rstrip().split('. ')[1:]) > 0
            and len(line) > 10
            and not line.isspace()
            and line not in '  '
            and line not in '   '
        ):
            if answers != '':
                content[question] = answers
                answers = ''
            question = line.rstrip().split('. ')[1:]
            question = ' '.join(question)
            print(question)
        else:
            answers += line.rstrip().replace('\n', ' ') + '; '
    with open('output.yaml', 'w') as outfile:
        yaml.dump(content, outfile, default_flow_style=False)