import json
import matplotlib as mpl
mpl.use("agg")
import matplotlib.pyplot as plt
import numpy as np
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as colors


def cdnizedFile(filename,cdnMapping):
	file=json.load(open("results/"+filename+"_"+country+".json"))
	dict={}
	for domain in file:
		for cdn in cdnMapping:
			if domain in cdnMapping[cdn]:
				if cdn not in dict:
					dict[cdn]={}
				dict[cdn][domain]=file[domain]

	with open("results/"+filename+"_cdnized"+"_"+country+".json", 'w') as fp:
		json.dump(dict, fp)

def cdfData(file,cdn,self_similarity):
	data=[]
	print (cdn)

	if not self_similarity:
		for value in file[cdn].values():
			data.append(value)
	else:
		for domain in file[cdn]:
			value=max(file[cdn][domain].values())
			print (value)
			data.append(value)

	sortedData=np.sort(data)
	print (sortedData)
	pData=1. * np.arange(len(sortedData))/(len(sortedData)-1)		

	return sortedData,pData

def plot_self_similarity2(dict,dict2,cdn,country,country2):
	local_data=dict[cdn]["local"] #resolver in US
	distant_data=dict[cdn]["distant"] #resolver in IN
	distant_data2=dict2[cdn]["distant"] #resolver in AR

	sortedDataLocal=np.sort(local_data)
	pDataLocal=1. * np.arange(len(sortedDataLocal))/(len(sortedDataLocal)-1)		

	sortedDataDistant=np.sort(distant_data)
	pDataDistant=1. * np.arange(len(sortedDataDistant))/(len(sortedDataDistant)-1)	

	sortedDataDistant2=np.sort(distant_data2)
	pDataDistant2=1. * np.arange(len(sortedDataDistant2))/(len(sortedDataDistant2)-1)	

	plt.plot(sortedDataLocal,pDataLocal,color='c',label="localResolver_US;/24")
	plt.plot(sortedDataDistant,pDataDistant,color='m',label="DistantResolver_IN;/24")
	plt.plot(sortedDataDistant2,pDataDistant2,color='y',label="DistantResolver_"+countryD+";/24")


	plt.legend()
	plt.xlabel("selfcosineSimilarity")
	plt.ylabel("CDF")
	plt.title(cdn)
	plt.margins(0.02)
	if not os.path.exists("graphs/self_similarity"):
		os.mkdir("graphs/self_similarity")
	plt.savefig("graphs/self_similarity/self_cosine_similarityCDF_D"+cdn)
	plt.clf()

def plot_cos_similarity(cosSim_24,cosSim_24_1,cdns):
	###Prefix Cosine Similarity
	for cdn in cdns:
		sortedData24,pData24=cdfData(cosSim_24,cdn,False)
		sortedData24_1,pData24_1=cdfData(cosSim_24_1,cdn,False)

		plt.plot(sortedData24_1,pData24_1,color='c',label="US_local-AR_distant;/24 Prefix")
		plt.plot(sortedData24,pData24,color='m',label="US_local-IN_distant;/24 Prefix")

		plt.legend()
		plt.title(cdn)
		plt.ylabel("CDF")
		plt.xlabel("Cosine Similarity")
		plt.margins(0.02)
		if not os.path.exists("graphs/localvsdistant"):
			os.mkdir("graphs/localvsdistant")
		plt.savefig("graphs/localvsdistant/cosSim_CDF"+cdn)

		plt.clf()

def heatMap(country,cdn,cdnMapping):
	local_24=json.load(open("results/ip_24_grouping_local_"+country+".json"))
	distant_24=json.load(open("results/ip_24_grouping_distant_"+country+".json"))
	uniquePrefixes=[]
	dict={}
	# try:
	# 	remaining=json.load(open("results/remainingDomains.json"))
	# except:
	# 	remaining={}
	for domain in cdnMapping[cdn]:
		# print (domain)
		try:
			for prefix in local_24[domain]:
				if prefix not in dict:
					dict[prefix]={}
				if prefix not in uniquePrefixes:
					uniquePrefixes.append(prefix)
				if "local" in dict[prefix]:
					dict[prefix]["local"]+=local_24[domain][prefix]
				else:
					dict[prefix]["local"]=local_24[domain][prefix]
			for prefix in distant_24[domain]:
				if prefix not in dict:
					dict[prefix]={}
				if prefix not in uniquePrefixes:
					uniquePrefixes.append(prefix)
				if "distant" in dict[prefix]:
					dict[prefix]["distant"]+=distant_24[domain][prefix]
				else:
					dict[prefix]["distant"]=distant_24[domain][prefix]
		except:
			print (cdn,domain)
			# if cdn not in remaining:
			# 	remaining[cdn]=[]
			# remaining[cdn].append(domain)
			# with open("results/remainingDomains.json", 'w') as fp:
			# 	json.dump(remaining, fp)
			continue
	# return

	for prefix in dict:
		if "local" not in dict[prefix]:
			dict[prefix]["local"]=0
		if "distant" not in dict[prefix]:
			dict[prefix]["distant"]=0

	popularPrefixes={}
	popularPrefixes["local"]={}
	popularPrefixes["distant"]={}
	for prefix in dict:
		popularPrefixes["local"][prefix]=dict[prefix]["local"]
		popularPrefixes["distant"][prefix]=dict[prefix]["distant"]

	sortedlocal = sorted(popularPrefixes["local"], key=popularPrefixes["local"].get, reverse=True)
	sorteddistant = sorted(popularPrefixes["distant"], key=popularPrefixes["distant"].get, reverse=True)
	try:
		localCommonPrefixes=json.load(open("results/localCommonPrefixes_"+country+".json"))
		distantCommonPrefixes=json.load(open("results/distantCommonPrefixes_"+country+".json"))
	except:
		localCommonPrefixes={}
		distantCommonPrefixes={}

	localCommonPrefixes[cdn]=[]
	distantCommonPrefixes[cdn]=[]
	index=0
	for key in sortedlocal:
		print (cdn,"local",key,popularPrefixes["local"][key])
		localCommonPrefixes[cdn].append(key.split("/24")[0])
		index+=1
		if index==5:
			break

	index=0
	for key in sorteddistant:
		print (cdn,"distant",key,popularPrefixes["distant"][key])
		distantCommonPrefixes[cdn].append(key.split("/24")[0])

		index+=1
		if index==5:
			break
	with open("results/localCommonPrefixes_"+country+".json", 'w') as fp:
		json.dump(localCommonPrefixes, fp)
	with open("results/distantCommonPrefixes_"+country+".json", 'w') as fp:
		json.dump(distantCommonPrefixes, fp)

	# print (len(uniquePrefixes),len(dict))
	# print (dict)
	return
	index=0
	lists=[]
	for prefix in dict:
		_list=[]
		# _prefix=prefix.split("/20")
		_list.append(index)
		index+=1
		print (index,prefix,dict[prefix]["local"],dict[prefix]["distant"])
		try:
			_list.append(dict[prefix]["local"])
		except:
			_list.append(0)
		try:
			_list.append(dict[prefix]["distant"])
		except:
			_list.append(0)
		lists.append(_list)

	print (lists)
	random_samples=np.array(lists)
	
	df = pd.DataFrame(
	    random_samples,
	    columns=["prefix", "local", "distant"]
	)
	print (random_samples)

	M = df.astype(int).values[:,1:]
	fig, ax = plt.subplots(1, figsize=(6, 18), sharex=True)
	heatmap = ax.pcolor(
	    M,
	    norm=colors.Normalize(
	        vmin=M.min() + 0.0001,
	        vmax=M.max()
	    ),
	    cmap='Greens',
	    edgecolors='#aeaeae',
	    linewidths=1,
	)
	heatmap.cmap.set_under('#aeaeae')
	
	xticks = []
	for name in list(df)[1:]:
	    xticks.append(name)
	ax.set_xticks(np.arange(0, M.shape[1], 1) + 0.5, minor=False)
	ax.set_xticklabels(xticks, rotation=0, minor=False, ha='center', fontsize=15)
	yticks = []
	for name in df.iloc[:,0].values:
	    yticks.append(name)
	ax.set_yticks(np.arange(0, M.shape[0], 1) + 0.5, minor=False)
	ax.set_yticklabels(yticks, rotation=0, minor=False, ha='right', fontsize=10)
	# ax1.tick_params(labelsize=30)
	for i in range(M.shape[1]):
	    for j in range(M.shape[0]):
	        if M[j, i] > 0:
	            ax.annotate(
	            "{:d}".format(M[j, i]),
	                xy=(
	                    i + 0.5,
	                    j + 0.5,
	                ),
	                fontsize=7,
	                color='black',
	                horizontalalignment='center',
	                verticalalignment='center',
	                # weight='bold',
	                rotation=0
	            )
	ax.set_ylabel('Prefixes', fontsize=20)
	ax.set_xlabel('Resolvers', fontsize=20)
	fig.subplots_adjust(hspace=0)
	fig.tight_layout()
	if not os.path.exists("graphs/heatmaps"):
		os.mkdir("graphs/heatmaps")
	fig.savefig("graphs/heatmaps/heatmap_"+cdn+"_AR"+".pdf")
	plt.clf()

if __name__ == "__main__":

	country="US"
	local=json.load(open("results/dnsRipeResult_local_"+country+".json"))
	distant=json.load(open("results/dnsRipeResult_distant_"+country+".json"))
	cdnMapping=json.load(open("data/cdn_mapping_"+country+".json"))

	cosSim_24=json.load(open("results/cosSim_24_"+country+".json"))
	cdns=["Google","Amazon CloudFront","Fastly","Akamai"]
	
	
	countryD="AR"
	cosSim_24_AR=json.load(open("results/cosSim_24_"+countryD+".json"))
	distant_AR=json.load(open("results/dnsRipeResult_distant_"+countryD+".json"))
	# plot_cos_similarity(cosSim_24,cosSim_24_AR,cdns)

	self_similarityDict_AR=json.load(open("results/self_similarityDict_"+countryD+".json"))
	self_similarityDict=json.load(open("results/self_similarityDict_"+country+".json"))

	# for cdn in cdns:
	# 	plot_self_similarity2(self_similarityDict,self_similarityDict_AR,cdn,country,countryD)

	for cdn in cdns:
		heatMap(countryD,cdn,cdnMapping)
	

