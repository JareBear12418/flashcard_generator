import json
import random

most_similar_words = []

def compare_words(u1: str, u2: str):
    '''
    Checks to see how similar the words are.
    It returns how many mistakes have been made in spelling.
    I have set the mininum number of mistakes to be 5.
    
    If the answer is "Theory", and you guessed: "thoery"
    This would still be correct as there is only one mistake.
    
    If the answer is "Population" and you guessed: "pupolation"
    This would still be correct as there are only 2 mistakes.
    
    So a maxinum of 6 mistakes, is pretty close to the real deal...
    '''
    try:
        s1 = unicode(u1)    
        s2 = unicode(u2)
    except:
        s1 = u1
        s2 = u2        
    if len(s1) < len(s2):
        return compare_words(u2, u1)
    if not s1:
        return len(s2)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

with open('flashcards\JSON_DATA\Geography.json') as f:
    d = json.load(f) 
all_topics = list(d.keys())

topic = random.choice(all_topics)


similarity_score = {}
for i in all_topics:
    if i != topic:
        similarity_score.update({i:int(compare_words(topic, i))})
    
similarity_score = dict(sorted(similarity_score.items(), key=lambda item: item[1]))
words_sorted_by_similarity = list(similarity_score.keys())
first_10_similar = words_sorted_by_similarity[:10]
print(first_10_similar)
print(topic)



