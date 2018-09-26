from __future__ import division

import re
import time
import math
import os
import sys
import collections
import copy

email_labels = dict()
train_spam = dict()
train_ham = dict()
test_spam = dict()
test_ham = dict()
train_set = dict()
test_set = dict()


def read_files():
	start_time = time.time()
	dir = 'trec06p-cs280\data'
	labelFile = 'trec06p-cs280\labels'	

	with open(labelFile, 'r') as label_file:
		for cnt, line in enumerate(label_file):
			line = line.strip()
			line = re.sub('[.]', '', line).split(" ")
			email_labels["trec06p-cs280"+line[1]] = line[0]



	spam = 0
	for root, dirs, files in os.walk(dir):
		train_range = (0, 70)
		test_range = (71, 127)
		


		for name in files:
			path = os.path.join(root, name).replace("\\", r"/")
			if os.path.isfile(path):
				folder = root.split("\\")
				classify = ""
				if path in email_labels:
					classify = email_labels[path]

				with open(path, 'rb') as text_file:
					contents = text_file.read()
					if(len(folder)>2):
						if(int(folder[2]) < 71):
							if(classify == "spam"):
								train_spam[path] = {contents, classify}


							else:
								train_ham[path] = {contents, classify}
								spam+=1

						else:
							if(classify == "spam"):
								test_spam[path] = {contents, classify}
								
								
							else:
								test_ham[path] = {contents, classify}

		print("tot" + str(spam))
	#merge two training datasets: spam and ham

	train_set = dict(train_spam, **train_ham)
	test_set = dict(test_spam, **test_ham)
	return train_spam, train_ham, test_spam, test_ham, train_set, test_set

def main():
	train_spam, train_ham, test_spam, test_ham, train_set, test_set = read_files()

	#print(train_set)

if __name__ == '__main__':
	main()