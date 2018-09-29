from __future__ import division

import re
import time
import math
import os
# import sys
from collections import Counter
# import copy
import email
from email import policy
import string
from encodings.aliases import aliases

import email.charset
email.charset.ALIASES.update(dict(aliases))
email.charset.ALIASES.update({
    'iso-8859-8-i': 'iso-8859-8',
    'x-mac-cyrillic': 'mac-cyrillic',
    'macintosh': 'mac-roman',
    'windows-874': 'cp874',
    'default': 'utf-8',
    'x-unknown': 'utf-8',
    '%charset': 'utf-8',
    'latin_1': 'iso-8859-1',
    'latin-1': 'iso-8859-1',
    'latin_2': 'iso-8859-2',
    'latin-2': 'iso-8859-2',
    'latin_3': 'iso-8859-3',
    'latin-3': 'iso-8859-3',
    'latin_4': 'iso-8859-4',
    'latin-4': 'iso-8859-4',
    'latin_5': 'iso-8859-9',
    'latin-5': 'iso-8859-9',
    'latin_6': 'iso-8859-10',
    'latin-6': 'iso-8859-10',
    'latin_7': 'iso-8859-13',
    'latin-7': 'iso-8859-13',
    'latin_8': 'iso-8859-14',
    'latin-8': 'iso-8859-14',
    'latin_9': 'iso-8859-15',
    'latin-9': 'iso-8859-15',
    'latin_10':'iso-8859-16',
    'latin-10':'iso-8859-16',
    'cp949':   'ks_c_5601-1987',
    'euc_jp':  'euc-jp',
    'euc_kr':  'euc-kr',
    'ascii':   'us-ascii',
    '': 'utf-8'    
})

train_range = range(71)
test_range = range(71,127)

train_set = []
test_set = []

punctuations = set(string.punctuation)


def extract_body(msg, depth=0):
    body = []
    if msg.is_multipart():
        main_content = None
        for part in msg.get_payload():
            is_txt = part.get_content_type() == 'text/plain'
            if not main_content or is_txt:
                main_content = extract_body(part)
            if is_txt:
                break
        if main_content:
            body.extend(main_content)
    elif msg.get_content_type().startswith("text/"):
        charset = msg.get_param('charset', 'utf-8').lower()
        charset = email.charset.ALIASES.get(charset, charset)
        msg.set_param('charset', charset)
        try:
            body.append(msg.get_content())
        except AssertionError as e:
            print('Parsing failed.    ')
        except LookupError:
            msg.set_param('charset', 'utf-8')
            body.append('=== UNKOWN ENCODING ===')
    return body

def classify_labels():
  with open('trec06p-cs280/labels', 'r') as label_file:
    for line in label_file:
      line = re.sub('[.]', '', line.strip()).split(" ")
      classificationObj = {}
      classificationObj['class'] = line[0]
      classificationObj['path'] = '/'.join(line[1].split("/")[1:])

      if(int(classificationObj['path'].split("/")[1]) in train_range):
        train_set.append(classificationObj)
      else:
        test_set.append(classificationObj)



def get_likelihood(dictionary):
  d_likelihood_ham = []
  d_likelihood_spam = []
  print("Calulating Likelihood of each word...")
  ham_list = list(filter(lambda x: x["class"] == "ham" , train_set))
  spam_list = list(filter(lambda x: x["class"] == "spam" , train_set))
  p_ham = len(ham_list) / len(train_set)
  p_spam = len(spam_list)  / len(train_set)

  for i in range(len(dictionary)):
    prob_value = 0
    occurences = len(list(filter(lambda x: x["matrix"][i] == 1, ham_list)))
    if occurences == 0:
      prob_value = (occurences + 1)/ (len(ham_list) + len(dictionary))
    else:
      prob_value = occurences/len(ham_list)
    d_likelihood_ham.append(prob_value)
    
  for i in range(len(dictionary)):
    prob_value = 0
    occurences = len(list(filter(lambda x: x["matrix"][i] == 1, spam_list)))
    if occurences == 0:
      prob_value = (occurences + 1)/ (len(spam_list) + len(dictionary))
    else:
      prob_value = occurences/len(spam_list)
    d_likelihood_spam.append(prob_value)

  return p_ham, p_spam, d_likelihood_ham, d_likelihood_spam

def get_likelihood_with_lambda(dictionary,lmb):
  d_likelihood_ham = []
  d_likelihood_spam = []
  print("Calulating Likelihood of each word...")
  ham_list = list(filter(lambda x: x["class"] == "ham" , train_set))
  spam_list = list(filter(lambda x: x["class"] == "spam" , train_set))
  p_ham = len(ham_list) / len(train_set)
  p_spam = len(spam_list)  / len(train_set)

  for i in range(len(dictionary)):
    prob_value = 0
    occurences = len(list(filter(lambda x: x["matrix"][i] == 1, ham_list)))
    prob_value = (occurences + lmb)/ (len(ham_list) + (lmb * len(dictionary)))
    d_likelihood_ham.append(prob_value)
    
  for i in range(len(dictionary)):
    prob_value = 0
    occurences = len(list(filter(lambda x: x["matrix"][i] == 1, spam_list)))
    prob_value = (occurences + 1)/ (len(spam_list) + (lmb * len(dictionary)))
    d_likelihood_spam.append(prob_value)

  return p_ham, p_spam, d_likelihood_ham, d_likelihood_spam


def start_analyze(dictionary):
  print("Analyzing Train Set...")
  for data_set in train_set:
    # print(data_set['path'])
    test_email = data_set
    data_set['matrix'] = []
    for data in dictionary:
      data_set['matrix'].append(1 if data in data_set['words'] else 0)


def create_dictionary():
  print("Creating dictionary...")
  dictionary = []
  for data_set in train_set:
    # print(data_set['path'])
    test_email = data_set
    file_path = re.sub('/',"\\\\",test_email['path'])
    msg = email.message_from_binary_file(open("trec06p-cs280/"+file_path, mode="rb"), policy=policy.default)
    body = '\n\n'.join(extract_body(msg))
    
    word_regex = "[a-zA-Z]+"
    words_per_file = re.findall(word_regex, body)
    for k in range(len(words_per_file)):
      words_per_file[k] = ''.join(ch for ch in words_per_file[k] if ch not in punctuations)
    data_set['words'] = words_per_file
    dictionary += [word for word in words_per_file if len(word) >= 6 and word.isalpha()]

  dictionary = Counter(dictionary).most_common(10000)
  dictionary = [k for k,s in dictionary]
  return dictionary

def start_test(dictionary, p_ham, p_spam,d_likelihood_ham,d_likelihood_spam):
  print("Probability for a Spam document: ", p_spam)
  print("Probability for a Ham document: ", p_ham)
  for data_set in test_set:
    test_email = data_set
    file_path = re.sub('/',"\\\\",test_email['path'])
    msg = email.message_from_binary_file(open("trec06p-cs280/"+file_path, mode="rb"), policy=policy.default)
    body = '\n\n'.join(extract_body(msg))
    word_regex = "[a-zA-Z]+"
    words_per_file = re.findall(word_regex, body)
    for k in range(len(words_per_file)):
      words_per_file[k] = ''.join(ch for ch in words_per_file[k] if ch not in punctuations)

    data_set['matrix'] = []
    for data in dictionary:
      data_set['matrix'].append(1 if data in words_per_file else 0)
    
    #finding the divisor of the equation
    get_all_ham = 1
    get_all_spam = 1
    for index in range(len(data_set['matrix'])):
      #used addition since I used logarithms for the likelihood value
      if d_likelihood_ham[index] != 0 and d_likelihood_ham[index] != 1:
        if data_set['matrix'][index] == 0:
          get_all_ham *= (1 - d_likelihood_ham[index])
        else:
          get_all_ham *= d_likelihood_ham[index]
      else:
        get_all_ham *= 1
      if get_all_ham == 0:
        get_all_ham = 1
        # break

    for index in range(len(data_set['matrix'])):
      #used addition since I used logarithms for the likelihood value
      if d_likelihood_spam[index] != 0 and d_likelihood_spam[index] != 1:
        if data_set['matrix'][index] == 0:
          get_all_spam *= (1 - d_likelihood_spam[index])
        else:
          get_all_spam *= d_likelihood_spam[index] + 1 # with laplace smoothing
      else:
        get_all_spam *= 1
      if get_all_spam == 0:
        get_all_spam = 1
    # print(p_ham, p_spam)
    lower_value = math.log((get_all_ham * p_ham) + (get_all_spam * p_spam))

    get_products_spam = 0
    get_products_ham = 0
    for index in range(len(data_set['matrix'])):
      #used addition since I used logarithms for the likelihood value
      if d_likelihood_spam[index] != 0 and d_likelihood_spam[index] != 1:
        get_products_spam += (math.log(1- d_likelihood_spam[index]) if data_set['matrix'][index] == 0 else math.log(d_likelihood_spam[index]))
      else:
        get_products_spam += 0
    up_value_spam = get_products_spam + math.log(p_spam)
    
    for index in range(len(data_set['matrix'])):
      #used addition since I used logarithms for the likelihood value
      
      if d_likelihood_ham[index] != 0 and d_likelihood_ham[index] != 1:
        get_products_ham += (math.log(1- d_likelihood_ham[index]) if data_set['matrix'][index] == 0 else math.log(d_likelihood_ham[index]))
      else:
        get_products_ham += 0
          
    up_value_ham = get_products_ham + math.log(p_ham)
      
    probability_ham_found = math.exp(up_value_ham - lower_value)
    probability_spam_found = math.exp(up_value_spam - lower_value)

    if probability_ham_found < probability_spam_found:
      data_set['result'] = "spam"
    else:
      data_set['result'] = "ham"

    # print("Classification:",data_set['class'])
    # print("Result: ", data_set['result'])
  
def calculate_precision():
  true_pos = len(list(filter(lambda x: (x["class"] == "spam" and x["result"] == "spam"), test_set)))
  true_neg = len(list(filter(lambda x: (x["class"] == "ham" and x["result"] == "ham"), test_set)))
  false_pos = len(list(filter(lambda x: (x["class"] == "ham" and x["result"] == "spam"), test_set)))
  false_neg = len(list(filter(lambda x: (x["class"] == "spam" and x["result"] == "ham"), test_set)))

  precision = true_pos / (true_pos + false_pos)

  recall = true_pos / (true_pos + false_neg)

  accuracy = (true_neg + true_pos) / (true_pos + true_neg + false_neg + false_pos)

  print("Precision: ", precision)
  print("Recall: ", recall)
  print("Accuracy: ", accuracy)

def start_train():
  d_likelihood_spam = []
  d_likelihood_ham = []
  dictionary = create_dictionary()
  start_analyze(dictionary)
  p_ham, p_spam, d_likelihood_ham, d_likelihood_spam = get_likelihood(dictionary)
  start_test(dictionary,p_ham, p_spam,d_likelihood_ham, d_likelihood_spam)
  calculate_precision()

  print("Test with Lambda smoothing 2.0...")
  p_ham, p_spam, d_likelihood_ham, d_likelihood_spam = get_likelihood_with_lambda(dictionary, 2.0)
  start_test(dictionary,p_ham, p_spam,d_likelihood_ham, d_likelihood_spam)
  calculate_precision()
  

  print("Test with Lambda smoothing 1.0...")
  p_ham, p_spam, d_likelihood_ham, d_likelihood_spam = get_likelihood_with_lambda(dictionary, 1.0)
  start_test(dictionary,p_ham, p_spam,d_likelihood_ham, d_likelihood_spam)
  calculate_precision()

  
  print("Test with Lambda smoothing 0.5...")
  p_ham, p_spam, d_likelihood_ham, d_likelihood_spam = get_likelihood_with_lambda(dictionary, 0.5)
  start_test(dictionary,p_ham, p_spam,d_likelihood_ham, d_likelihood_spam)
  calculate_precision()

  
  print("Test with Lambda smoothing 0.1...")
  p_ham, p_spam, d_likelihood_ham, d_likelihood_spam = get_likelihood_with_lambda(dictionary, 0.1)
  start_test(dictionary,p_ham, p_spam,d_likelihood_ham, d_likelihood_spam)
  calculate_precision()

  
  print("Test with Lambda smoothing 0.005...")
  p_ham, p_spam, d_likelihood_ham, d_likelihood_spam = get_likelihood_with_lambda(dictionary, 0.005)
  start_test(dictionary,p_ham, p_spam,d_likelihood_ham, d_likelihood_spam)
  calculate_precision()

def main():
  classify_labels()
  start_train()

if __name__ == '__main__':
  start_time = time.time()      
  main()
  print("--- %s seconds ---" % (time.time() - start_time))  