from __future__ import division

import re
import time
import math
import os
import sys
from collections import Counter
import copy
from functools import reduce
from email import message_from_binary_file, policy
import email.charset

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
})

email_labels = dict()
train_spam = []
train_ham = []
test_spam = []
test_ham = []
train_set = []
test_set = []

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
            print(e)
        except LookupError:
            msg.set_param('charset', 'utf-8')
            body.append('=== <UNKOWN ENCODING POSSIBLY SPAM> ===')
            body.append(msg.get_content())
    return body

def toString(string):    
    try:
        return string.decode("utf-8")
    except ValueError:
        return string

def removeStopWords(words):
	with open('stop_words.txt') as stop_file:
		stop_words = [line.rstrip() for line in stop_file]
		words = [word for word in words if word not in stop_words]
		return words

def read_files():
	start_time = time.time()
	dir = 'dataset-cut\data'
	labelFile = 'dataset-cut\labels'	

	with open(labelFile, 'r') as label_file:
		for cnt, line in enumerate(label_file):
			line = line.strip()
			line = re.sub('[.]', '', line).split(" ")
			email_labels["dataset-cut"+line[1]] = line[0]

	all_words = []
	for root, dirs, files in os.walk(dir):
		inTrainRange = 1
		for name in files:
			path = os.path.join(root, name).replace("\\", r"/")
			if os.path.isfile(path):
				folder = root.split("\\")
				classify = ""
				if path in email_labels:
					classify = email_labels[path]

				if(len(folder)>2):
					inTrainRange = int(folder[2]) < 71

				msg = message_from_binary_file(open(path, mode="rb"), policy=policy.default)
				body = '\n\n'.join(extract_body(msg))
				word_regex = "[a-zA-Z]+"
				words_per_file = re.findall(word_regex, body)
				for k in range(len(words_per_file)):
					words_per_file[k] = words_per_file[k].lower()
					words_per_file[k] = words_per_file[k].replace("_", "")
					words_per_file[k] = re.sub("[0-9]+", "", words_per_file[k])
				words = [word for word in words_per_file if len(word) >= 4 and word.isalpha()]
				#optional
				words = removeStopWords(words)

				if(inTrainRange):
					if(classify == "spam"):
						train_spam.append(words)
					else:
						train_ham.append(words)
				else:
					if(classify == "spam"):
						test_spam.append(words)
					else:
						test_ham.append(words)


				if(inTrainRange):
					all_words += words

				# with open(path, "rb") as text_file:
				# 	words = []
				# 	for line in text_file:
				# 		word_regex = re.compile(b"[a-zA-Z]+")
				# 		received_regex = re.compile(b"^Received:")
				# 		from_regex = re.compile(b"^From:")
				# 		to_regex = re.compile(b"^To:")
				# 		sender_regex = re.compile(b"^Sender:")
				# 		content_regex = re.compile(b"^Content-\S+")
				# 		x_regex = re.compile(b"^X-\S+:")
				# 		path_regex = re.compile(b"^Path")
				# 		char_regex = re.compile(b"^<")

				# 		line = line.rstrip()
				# 		if re.search(received_regex, line) or re.search(from_regex, line) or re.search(to_regex, line) or re.search(content_regex, line) or re.search(x_regex, line) or re.search(path_regex, line) or re.search(sender_regex, line) or re.search(char_regex, line):
				# 			continue

				# 		words_per_file = re.findall(word_regex, line)
				# 		words_per_file = [toString(word) for word in words_per_file]
				# 		for k in range(len(words_per_file)):
				# 			words_per_file[k] = words_per_file[k].lower()
				# 			words_per_file[k] = words_per_file[k].replace("_", "")
				# 			words_per_file[k] = re.sub("[0-9]+", "", words_per_file[k])
				# 		words += [word for word in words_per_file if len(word) >= 4 and word.isalpha()]
				#		words = removeStopWords(words)
				# 	if(inTrainRange):
				# 		if(classify == "spam"):
				# 			train_spam.append(words)
				# 		else:
				# 			train_ham.append(words)
				# 	else:
				# 		if(classify == "spam"):
				# 			test_spam.append(words)
				# 		else:
				# 			test_spam.append(words)


				# 	if(inTrainRange):
				# 		all_words += words

						

	
	dictionary = Counter(all_words)
	dictionary = {k:dictionary[k] for k in dictionary if dictionary[k] > 15}
	return dictionary, train_spam, train_ham, test_spam, test_ham

def merge_datasets():
	train_set = train_spam + train_ham
	test_set = test_spam + test_ham
	
	train_labels = [1] * len(train_spam)
	train_labels.extend([0] * len(train_ham))

	test_labels = [1] * len(test_spam)
	test_labels.extend([0] * len(test_spam))
	return train_set, test_set, train_labels, test_labels


def getFrequency():
	spam_frequency = len(train_spam)
	ham_frequency = len(train_ham)
	
	spam_probability = spam_frequency / (spam_frequency + ham_frequency)
	ham_probability = ham_frequency / (spam_frequency + ham_frequency)

	print("F(SPAM): " + str(spam_frequency))
	print("F(HAM):" + str(ham_frequency))
	print("P(SPAM):" + str(spam_probability))
	print("P(HAM):" + str(ham_probability))

	return spam_frequency, ham_frequency, spam_probability,ham_probability

def getFeatureMatrix(dataset, dictionary):
	feature_matrix = []
	for each_file in dataset:
		feature_vector = [0] * len(dictionary)
		for each_word in each_file:
			for d,dicword in enumerate(dictionary.keys()):
				if each_word == dicword:
					feature_vector[d] = 1
		feature_matrix.append(feature_vector)
	return feature_matrix


def main():
	dictionary, train_spam, train_ham, test_spam, test_ham = read_files()
	train_set, test_set, train_labels, test_labels = merge_datasets()

	spam_frequency, ham_frequency, spam_probability,ham_probability = getFrequency()	
	
	#extract features
	spam_feature_matrix = getFeatureMatrix(train_spam, dictionary)
	ham_feature_matrix = getFeatureMatrix(train_ham, dictionary)
	testset_feature_matrix = getFeatureMatrix(test_set, dictionary)

	#get probability of each word in the dictionary

	# spam_likelihood = [math.log10(sum(i)/spam_frequency) if sum(i)>0 else sum(i)/spam_frequency for i in zip(*spam_feature_matrix)]
	# ham_likelihood = [math.log10(sum(i)/ham_frequency) if sum(i)>0 else sum(i)/ham_frequency for i in zip(*ham_feature_matrix)]
	spam_likelihood = [math.log10((sum(i)/spam_frequency)+1)  for i in zip(*spam_feature_matrix)]
	ham_likelihood = [math.log10((sum(i)/ham_frequency)+1) for i in zip(*ham_feature_matrix)]

	spam_count = 0
	ham_count = 0
	
	test_results = []
	for doc in testset_feature_matrix:
		email_ham_prob = reduce(lambda x, y: x*y, [ham_likelihood[idx] if val==1 else 1-ham_likelihood[idx] for idx,val in enumerate(doc)])*ham_probability
		email_spam_prob = reduce(lambda x, y: x*y, [spam_likelihood[idx] if val==1 else 1-spam_likelihood[idx] for idx,val in enumerate(doc)])*spam_probability
		
		email_ham = math.log10((email_ham_prob+1)/(email_ham_prob + email_spam_prob + len(dictionary)))
		email_spam = math.log10((email_spam_prob+1)/(email_ham_prob + email_spam_prob + len(dictionary)))

		if email_ham > email_spam:
			test_results.append(0)
		else:
			test_results.append(1)


	results = [''.join([str(i),str(j)]) for i, j in zip(test_labels, test_results)]

	counts = Counter(results)
	
	accuracy = ((counts['11']+counts['00']) / sum(counts.values()))*100
	recall = counts['11']/ (counts['11'] + counts['10'])*100
	precision = counts['11'] / (counts['11'] + counts['01'])*100

	print("Accuracy: " + str(accuracy))
	print("Recall: " + str(recall))
	print("Precision: " + str(precision))

 
if __name__ == '__main__':
	main()