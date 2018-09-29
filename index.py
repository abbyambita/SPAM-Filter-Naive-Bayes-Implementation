from __future__ import division

import re
import time
import math
import os
import sys
import copy
import email.charset
from encodings.aliases import aliases

from collections import Counter, OrderedDict
from functools import reduce
from email import message_from_binary_file, policy

email.charset.ALIASES.update(dict(aliases))
email.charset.ALIASES.update({
    'default': 'utf-8',
    'x-unknown': 'utf-8',
    '%charset': 'utf-8',
    '': 'utf-8'
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
    
def removeStopWords(words):
	with open('stop_words.txt') as stop_file:
		stop_words = [line.rstrip() for line in stop_file]
		words = [word for word in words if word not in stop_words]
		return words

def read_files():
	start_time = time.time()
	dir = 'trec06p-cs280\data'
	labelFile = 'trec06p-cs280\labels'	

	with open(labelFile, 'r') as label_file:
		for cnt, line in enumerate(label_file):
			line = line.strip()
			line = re.sub('[.]', '', line).split(" ")
			email_labels["trec06p-cs280"+line[1]] = line[0]

	all_words = []
	spam_words = []
	ham_words = []
	for root, dirs, files in os.walk(dir):
		inTrainRange = 1
		for name in files:
			path = os.path.join(root, name).replace("\\", r"/")
			if os.path.isfile(path):
				print("Reading "+path)
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
				words = [word for word in words_per_file if len(word) >= 6 and word.isalpha()]
				#optional
				words = removeStopWords(words)

				if(inTrainRange):
					if(classify == "spam"):
						train_spam.append(words)
						spam_words += words						
					else:
						train_ham.append(words)
				else:
					if(classify == "spam"):
						test_spam.append(words)
						ham_words += words						
					else:
						test_ham.append(words)


				if(inTrainRange):
					all_words += words

	# spam_dict = Counter(spam_words)
	# spam_dict = OrderedDict(spam_dict.most_common())
	# spam_dict = {k:spam_dict[k] for k in list(spam_dict)[:101]}
	# print(spam_dict)
	# ham_dict = Counter(ham_words)
	# ham_dict = OrderedDict(ham_dict.most_common())
	# ham_dict = {k:ham_dict[k] for k in list(ham_dict)[:101]}	
	# print(ham_dict)
	# dictionary = {**spam_dict, **ham_dict} 

	dictionary = Counter(all_words)
	dictionary = {k:dictionary[k] for k in dictionary if dictionary[k] > 100}
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
	
	spam_prior_probability = spam_frequency / (spam_frequency + ham_frequency)
	ham_prior_probability = ham_frequency / (spam_frequency + ham_frequency)

	print("Number of SPAM Training Documents: " + str(spam_frequency))
	print("Number of HAM Training Documents: " + str(ham_frequency))
	print("SPAM Prior Probability: " + str(spam_prior_probability))
	print("HAM Prior Probability:" + str(ham_prior_probability))

	return spam_frequency, ham_frequency, spam_prior_probability,ham_prior_probability

def getFeatureMatrix(dataset, dictionary):
	print("Creating feature matrix...")

	feature_matrix = []
	for each_file in dataset:
		y = [1 if dicword in each_file else 0 for dicword in dictionary.keys()]
		feature_matrix.append(y)

	return feature_matrix

def getLikelihood(spam_feature_matrix, ham_feature_matrix, spam_frequency, ham_frequency, dictionary, lmb):
	dist = len(dictionary)
	spam_likelihood = [((sum(i)+lmb)/(spam_frequency+(lmb*dist))) for i in zip(*spam_feature_matrix)]
	ham_likelihood = [((sum(i)+lmb)/(ham_frequency+(lmb*dist))) for i in zip(*ham_feature_matrix)]
	return spam_likelihood, ham_likelihood


def testSet(testset_feature_matrix, spam_likelihood, ham_likelihood, dictionary, ham_prior_probability, spam_prior_probability, lmb):
	test_results = []

	for doc in testset_feature_matrix:
		ham_denominator = reduce(lambda x, y: x*y, [ham_likelihood[idx]+1 if val==1 else 1-ham_likelihood[idx] for idx,val in enumerate(doc)])
		spam_denominator = reduce(lambda x, y: x*y, [spam_likelihood[idx]+1 if val==1 else 1-spam_likelihood[idx] for idx,val in enumerate(doc)])
		
		if ham_denominator == 0:
			ham_denominator = 1	
		if spam_denominator == 0:
			spam_denominator = 1 

		denominator = math.log((ham_denominator * ham_prior_probability) + (spam_denominator * spam_prior_probability))

		spam_numerator = sum([math.log(spam_likelihood[idx]) if val==1 else math.log(1-spam_likelihood[idx]) for idx,val in enumerate(doc)])+math.log(spam_prior_probability)
		ham_numerator = sum([math.log(ham_likelihood[idx]) if val==1 else math.log(1-ham_likelihood[idx]) for idx,val in enumerate(doc)])+math.log(ham_prior_probability)

		is_ham = ham_numerator - denominator
		is_spam = spam_numerator - denominator

		test_results.append(1 if is_spam > is_ham else 0)

	return test_results

def getAccuracy(test_labels, test_results):
	results = [''.join([str(i),str(j)]) for i, j in zip(test_labels, test_results)]
	counts = Counter(results)
	
	accuracy = ((counts['11']+counts['00']) / sum(counts.values()))*100
	recall = counts['11']/ (counts['11'] + counts['10'])*100
	precision = counts['11'] / (counts['11'] + counts['01'])*100

	print()
	print("Correctly classified SPAM: " +str(counts['11']))
	print("SPAM but classified as HAM: " +str(counts['10']))
	print("HAM but classified as SPAM: " +str(counts['01']))
	print("Correctly classified HAM: " +str(counts['00']))

	print()
	print("Accuracy: " + str(accuracy))
	print("Recall: " + str(recall))
	print("Precision: " + str(precision))	



def main():
	#parse the emails and extract dictionary
	dictionary, train_spam, train_ham, test_spam, test_ham = read_files()
	train_set, test_set, train_labels, test_labels = merge_datasets()

	spam_frequency, ham_frequency, spam_prior_probability,ham_prior_probability = getFrequency()	
	
	#extract features
	spam_feature_matrix = getFeatureMatrix(train_spam, dictionary)
	ham_feature_matrix = getFeatureMatrix(train_ham, dictionary)
	testset_feature_matrix = getFeatureMatrix(test_set, dictionary)


	#classify emails on the test set, compare the test labels and test results and determine accuracy of the model
	print("\nReading with lambda = 1")
	lmbda = 1
	spam_likelihood, ham_likelihood = getLikelihood(spam_feature_matrix, ham_feature_matrix, spam_frequency, ham_frequency, dictionary, lmbda)	
	test_results = testSet(testset_feature_matrix, spam_likelihood, ham_likelihood, dictionary, ham_prior_probability, spam_prior_probability, lmbda)
	getAccuracy(test_labels, test_results)

 
if __name__ == '__main__':
	start_time = time.time()		
	main()
	print("--- %s seconds ---" % (time.time() - start_time))