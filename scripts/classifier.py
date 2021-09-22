from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics
import numpy as np
import json
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.tree import export_graphviz
# from IPython.display import Image  
import pydotplus
import six
import sys
sys.modules['sklearn.externals.six'] = six
from sklearn.externals.six import StringIO  
from sklearn import tree



def loadData(region):
	#select resources with no ouliers for all resolvers, find median and use them for classification
	cdnizedIpClusters=json.load(open("results/sigcommRes/"+region+"/cdnizedIpClusters.json"))
	rtt_dict=json.load(open("results/sigcommRes/"+region+"/rtts/rttDict_allCDNs.json"))
	resolvers = ["local","remote_google","remote_metro","remote_same_region","remote_neighboring_region","remote_non-neighboring_region"]
	cdns=["Google","Fastly","Akamai","EdgeCast","Amazon Cloudfront"]
	# cdns=["Google","Fastly","Akamai","EdgeCast"]


	_dict={}
	for cdn in cdns:
		if cdn not in _dict:
			_dict[cdn]={}
		for resource in cdnizedIpClusters[cdn]:
			if resource not in _dict[cdn]:
				_dict[cdn][resource]={}
			for resolver in cdnizedIpClusters[cdn][resource]:
				if resolver not in resolvers:
					continue
				rtts=[]
				for ip in cdnizedIpClusters[cdn][resource][resolver]:
					rtt_per_ip=np.array(rtt_dict[cdn][ip]) 
					# rtts.append(np.median(rtt_per_ip))
				# rtt=np.median(rtts)
				# _dict[cdn][resource][resolver]=rtt
				_dict[cdn][resource][resolver]=rtts

	# print (_dict)
	outlier_dict=findOutliers(_dict,resolvers)
	X=[]
	y=[]
	for cdn in _dict:
		for resource in _dict[cdn]:
			x_values=[]
			if resource in outlier_dict[cdn]:
				continue
			for resolver in _dict[cdn][resource]:
				x_values.append(_dict[cdn][resource][resolver])
			X.append(x_values)
			y.append(return_cdnType(cdn))
	print (len(X),len(y))
	return X,y

def return_cdnType(cdn):
	if cdn=="Google" or cdn=="Fastly":
		_type='dns'
	if cdn=="Akamai" or cdn=="Amazon Cloudfront":
		_type='end-user'
	if cdn=="EdgeCast":
		_type="regional_anycast"
	return _type

def findOutliers(_dict,resolvers):
	outlier_dict={}
	for cdn in _dict:
		if cdn not in outlier_dict:
			outlier_dict[cdn]=[]
		for resolver in resolvers:
			rtts=[]
			for resource in _dict[cdn]:
				try:
					rtts.append(_dict[cdn][resource][resolver])	
				except:
					print (cdn,resource)
					if resource not in outlier_dict[cdn]:
						outlier_dict[cdn].append(resource)

			lowerbound,upperbound=calcOutliers(rtts)
			for resource in _dict[cdn]:
				if resource in outlier_dict[cdn]:
					continue
				rtt=_dict[cdn][resource][resolver]
				if rtt>upperbound or rtt<lowerbound:
				# if rtt>lowerbound:
					if resource not in outlier_dict[cdn]:
						outlier_dict[cdn].append(resource)
	# print (outlier_dict)
	return outlier_dict

def calcOutliers(rtts):
	rtts=np.array(rtts)
	sorted(rtts)
	q1,q3=np.percentile(rtts,[25,75])
	iqr=q3-q1
	upperbound=q3+(1.5*iqr)
	lowerbound=q1-(1.5*iqr)
	return lowerbound,upperbound

if __name__ == "__main__":

	region="North America"
	cdns=["Google","Fastly","Akamai","EdgeCast","Amazon Cloudfront"]


	X,y = loadData(region)

	# X  # Features
	# y  # Target variable
	col_names = ["local","remote_google","remote_metro","remote_same_region","remote_neighboring_region","remote_non-neighboring_region","label"]

	feature_cols = col_names[:-1]

	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1) # 70% training and 30% test

	# Create Decision Tree classifer object
	clf = DecisionTreeClassifier()

	# Train Decision Tree Classifer
	clf = clf.fit(X_train,y_train)

	#Predict the response for test dataset
	y_pred = clf.predict(X_test)

	print (y_test,y_pred)
	print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

	recall = recall_score(y_test, y_pred, average=None)
	print('Recall: ',recall)	

	precision = precision_score(y_test, y_pred, average=None)
	print('Precision: ' , precision)

	# tree.plot_tree(clf) 
	text_representation = tree.export_text(clf)
	print(text_representation)
	print (feature_cols[:-1])



	# dot_data = StringIO()
	# export_graphviz(clf, out_file=dot_data,  
	#                 filled=True, rounded=True,
	#                 special_characters=True,feature_names = feature_cols,class_names=cdns)
	# graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
	# graph.write_png('cdntree.png')
	# Image(graph.create_png())


