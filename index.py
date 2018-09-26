from __future__ import division

import re
import time
import math
import os
import sys
from collections import Counter
import copy

email_labels = dict()
train_spam = []
train_ham = []
test_spam = []
test_ham = []
train_set = []
test_set = []

def toString(string):    
    try:
        return string.decode("utf-8")
    except ValueError:
        return string

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

				if(inTrainRange):
					if(classify == "spam"):
						train_spam.append(path)
					else:
						train_ham.append(path)
				else:
					if(classify == "spam"):
						test_spam.append(path)
					else:
						test_spam.append(path)


				with open(path, "rb") as text_file:
					for line in text_file:
						words = line.split()
						words = [toString(word) for word in words]
						if(inTrainRange):
							all_words += words

	dictionary = Counter(all_words)

	list_to_remove = list(dictionary.keys())
	for item in list_to_remove:
		if item.isalpha() == False:
			del dictionary[item]
		elif len(item) == 1:
			del dictionary[item]

	dictionary = {k:dictionary[k] for k in dictionary if dictionary[k] > 15}
    
    print("Dictionary: "+ str(len(dictionary)))	


	return dictionary, train_spam, train_ham, test_spam, test_ham

def merge_datasets():
	#merge ham and spam trainsets and testsets
	train_set = train_spam + train_ham
	test_set = test_spam + test_ham
	
	#classify 1(spam) and 0(ham) for the trainset
	train_labels = [1] * len(train_spam)
	train_labels.extend([0] * len(test_spam))

	#classify 1(spam) and 0(ham) for the testset
	test_labels = [1] * len(test_spam)
	test_labels.extend([0] * len(test_spam))
	return train_set, test_set, train_labels, test_labels


def getFrequency():
	spam_frequency = len(train_spam)
	ham_frequency = len(train_ham)
	
	spam_probability = spam_frequency / (spam_frequency + ham_frequency)
	ham_probability = ham_frequency / (spam_frequency + ham_frequency)

	print("F(SPAM): " + str(spam_frequency))
	print("F(HAM)" + str(ham_frequency))
	print("P(SPAM)" + str(spam_probability))
	print("P(HAM)" + str(ham_probability))

	return spam_frequency, ham_frequency, spam_probability,ham_probability


def main():
	dictionary, train_spam, train_ham, test_spam, test_ham = read_files()
	train_set, test_set, train_labels, test_labels = merge_datasets()
	spam_frequency, ham_frequency, spam_probability,ham_probability = getFrequency()



if __name__ == '__main__':
	main()