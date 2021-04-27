import json
import matplotlib as mpl
mpl.use("agg")
import matplotlib.pyplot as plt
import numpy as np


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

def plot_self_similarity2(dict,cdn):
	local_data=dict[cdn]["local"]
	distant_data=dict[cdn]["distant"]

	sortedDataLocal=np.sort(local_data)
	pDataLocal=1. * np.arange(len(sortedDataLocal))/(len(sortedDataLocal)-1)		

	sortedDataDistant=np.sort(distant_data)
	pDataDistant=1. * np.arange(len(sortedDataDistant))/(len(sortedDataDistant)-1)	

	plt.plot(sortedDataLocal,pDataLocal,color='c',label="localResolver;/24")
	plt.plot(sortedDataDistant,pDataDistant,color='m',label="DistantResolver;/24")

	plt.legend()
	plt.xlabel("cosineSimilarity")
	plt.ylabel("CDF")
	plt.title(cdn)
	plt.margins(0.02)
	plt.savefig("graphs/self_cosine_similarityCDF"+cdn)
	plt.clf()


if __name__ == "__main__":

	country="US"
	local=json.load(open("results/dnsRipeResult_local_"+country+".json"))
	distant=json.load(open("results/dnsRipeResult_distant_"+country+".json"))
	cdnMapping=json.load(open("data/cdn_mapping_"+country+".json"))


	cosSim_24=json.load(open("results/cosSim_24_"+country+".json"))
	cosSim_20=json.load(open("results/cosSim_20_"+country+".json"))

	#show for Akamai and Fastly as well
	cdns=["Google","Amazon CloudFront","Fastly","Akamai"]
	###Prefix Cosine Similarity
	for cdn in cdns:
		sortedData24,pData24=cdfData(cosSim_24,cdn,False)
		sortedData20,pData20=cdfData(cosSim_20,cdn,False)

		plt.plot(sortedData20,pData20,color='c',label="/20 Prefix")
		plt.plot(sortedData24,pData24,color='m',label="/24 Prefix")

		plt.legend()
		plt.title(cdn)
		plt.ylabel("CDF")
		plt.xlabel("Cosine Similarity")
		plt.margins(0.02)
		plt.savefig("graphs/cosSim_CDF"+cdn)

		plt.clf()

	###self-similarity	
	

	cdnizedFile("ip_20_grouping_local",cdnMapping)
	cdnizedFile("ip_20_grouping_distant",cdnMapping)
	cdnizedFile("ip_24_grouping_local",cdnMapping)
	cdnizedFile("ip_24_grouping_distant",cdnMapping)
	cdnizedFile("dnsRipeResult_local",cdnMapping)
	cdnizedFile("dnsRipeResult_distant",cdnMapping)

	_local=json.load(open("results/dnsRipeResult_local_cdnized_"+country+".json"))
	_distant=json.load(open("results/dnsRipeResult_distant_cdnized_"+country+".json"))	

	local_20=json.load(open("results/ip_20_grouping_local_cdnized_"+country+".json"))
	distant_20=json.load(open("results/ip_20_grouping_distant_cdnized_"+country+".json"))

	local_24=json.load(open("results/ip_24_grouping_local_cdnized_"+country+".json"))
	distant_24=json.load(open("results/ip_24_grouping_distant_cdnized_"+country+".json"))

	for cdn in cdns:

		sortedDatalocal,pDatalocal=cdfData(_local,cdn,True)
		sortedDatadistant,pDatadistant=cdfData(_distant,cdn,True)

		sortedDatalocal20,pDatalocal20=cdfData(local_20,cdn,True)
		sortedDatadistant20,pDatadistant20=cdfData(distant_20,cdn,True)

		sortedDatalocal24,pDatalocal24=cdfData(local_24,cdn,True)
		sortedDatadistant24,pDatadistant24=cdfData(distant_24,cdn,True)

		# plt.plot(sortedDatalocal,pDatalocal,color='c',marker=".",label="localResolver")
		# plt.plot(sortedDatalocal20,pDatalocal20,color='c',marker="*",label="localResolver;/20")
		plt.plot(sortedDatalocal24,pDatalocal24,color='c',label="localResolver;/24")

		# plt.plot(sortedDatadistant,pDatadistant,color='m',marker=".",label="distantResolver")
		# plt.plot(sortedDatadistant20,pDatadistant20,color='m',marker="*",label="distantResolver;/20")
		plt.plot(sortedDatadistant24,pDatadistant24,color='m',label="distantResolver;/24")


		plt.legend()
		plt.xlabel("Total no of times a replica is hit for a domain")
		plt.ylabel("CDF")
		plt.title(cdn)
		plt.margins(0.02)
		plt.savefig("graphs/self-similarityCDF"+cdn)
		plt.clf()

	self_similarityDict=json.load(open("results/self_similarityDict_"+country+".json"))

	for cdn in cdns:
		plot_self_similarity2(self_similarityDict,cdn)

	

