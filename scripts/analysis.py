from collections import Counter
import json
import ipaddress
import dns.resolver
import tldextract
import random
import matplotlib as mpl
mpl.use("agg")
import matplotlib.pyplot as plt
import numpy as np
import os





def cosSimilarity(vec1,vec2):
	# word-lists to compare
	a=vec1
	b=vec2

	# count word occurrences
	a_vals = Counter(a)
	b_vals = Counter(b)

	# convert to word-vectors
	words  = list(a_vals.keys() | b_vals.keys())
	a_vect = [a_vals.get(word, 0) for word in words]       
	b_vect = [b_vals.get(word, 0) for word in words] 

	# find cosine
	len_a  = sum(av*av for av in a_vect) ** 0.5             
	len_b  = sum(bv*bv for bv in b_vect) ** 0.5             
	dot    = sum(av*bv for av,bv in zip(a_vect, b_vect))   
	cosine = dot / (len_a * len_b)    
	return cosine    

# def ip_prefix_grouping(approach,file,country,prefix,resultname):
def ip_prefix_grouping(file,prefix):
	dict={}
	for domain in file:
		uniquePrefixes={}
		for ip in file[domain]:
			host4 = ipaddress.ip_interface(ip+prefix)
			# print (ip,str(host4.network))
			ip_24_prefix=str(host4.network)
			if ip_24_prefix not in uniquePrefixes:
				uniquePrefixes[ip_24_prefix]=file[domain][ip]
			else:
				uniquePrefixes[ip_24_prefix]+=file[domain][ip]
		dict[domain]=uniquePrefixes
	return dict

def self_similarity3(file,approachName,dict,cdns):
	for cdn in file:
		if cdn not in cdns:
			continue
		_dict=file[cdn]
		domainList=[]
		for domain in _dict.keys():
			if domain!="youtube.com":
				continue
			ids=[]
			for id in _dict[domain]:
				ids.append(id)
			random.shuffle(ids)
			half=int(len(ids)/2)
			print (domain,len(ids))
			exit()
			list1=ids[:half]
			list2=ids[half:]
			# print (domain,list1,list2)

			if len(list1)>len(list2):
				list1=list1[:-1]
			elif len(list1)<len(list2):
				list2=list2[:-1]
			vec1=[]
			vec2=[]
			if len(list1)<1 and len(list2)<1:
				continue
			for id in list1:
				for replica in _dict[domain][id]:
					host4 = ipaddress.ip_interface(replica+"/24")
					ip_24_prefix=str(host4.network)
					# if ip_24_prefix not in vec1:
					vec1.append(ip_24_prefix)

			for id in list2:
				for replica in _dict[domain][id]:
					host4 = ipaddress.ip_interface(replica+"/24")
					ip_24_prefix=str(host4.network)
					# if ip_24_prefix not in vec2:
					vec2.append(ip_24_prefix)
			result=cosSimilarity(vec1,vec2)
			# print (result)
			if cdn not in dict:
				dict[cdn]={}
			if approachName not in dict[cdn]:
				dict[cdn][approachName]=[]
			dict[cdn][approachName].append(result)
		
	return dict


def runCosineSimilarity(domains,local,distant,cdnMapping,filename):
	dict={}
	vec1=[]
	vec2=[]
	for domain in domains:
		try:
			vec1=[]
			vec2=[]
			for replica in local[domain]:
				for x in range(local[domain][replica]):
					vec1.append(replica)
			for replica in distant[domain]:
				for x in range(distant[domain][replica]):
					vec2.append(replica)
			# vec1=list(local[domain].keys())
			# vec2=list(distant[domain].keys())
		except:
			continue
		result=cosSimilarity(vec1,vec2)
		for cdn in cdnMapping:
			if domain in cdnMapping[cdn]:
				if cdn not in dict:
					dict[cdn]={}
				dict[cdn][domain]=result
	with open("results/"+filename+".json", 'w') as fp:
		json.dump(dict, fp)

def findCname(domain):
	try:
		result = dns.resolver.query(domain, 'CNAME')
		for cnameval in result:
			cname=cnameval.target
			print (' cname target address:', cnameval.target)

	except Exception as e:
		print (str(e))

def extract_from_cnameToCDNMap(domain,cdnMap):
	for cdn in cdnMap:
		if domain in cdnMap[cdn]:
			return cdn
		else:
			if cdn.lower() in domain:
				return cdn
	return None


def findCDNs(domains,cdnMap,country):
	missing=[]
	domainCDNMap={}
	CnameDict=json.load(open("data/CnameDict_"+country+".json"))

	for domain in domains:
		if "www." in domain:
			_domain=domain
			domain=domain.split("www.")[1]
		cdn=extract_from_cnameToCDNMap(domain,cdnMap)
		if cdn:
			if cdn not in domainCDNMap:
				domainCDNMap[cdn]=[]
			if domain not in domainCDNMap[cdn]:
				domainCDNMap[cdn].append(domain)
		elif domain in CnameDict:
			_CName=CnameDict[domain][0]
			if len(CnameDict[domain])>1:
				print ("Len of CnameDict[domain]: ",len(CnameDict[domain]))
			_tld = tldextract.extract(_CName).domain
			# print (domain,_CName,_tld)
			cdn=extract_from_cnameToCDNMap(_tld,cdnMap)
			if cdn:
				if cdn not in domainCDNMap:
					domainCDNMap[cdn]=[]
				if domain not in domainCDNMap[cdn]:
					domainCDNMap[cdn].append(domain)
		else:
			_domain=str(tldextract.extract(domain).domain)+"."+domain.split(".")[-1]
			cdn=extract_from_cnameToCDNMap(_domain,cdnMap)
			if cdn:
				if cdn not in domainCDNMap:
					domainCDNMap[cdn]=[]
				if domain not in domainCDNMap[cdn]:
					domainCDNMap[cdn].append(domain)
			else:
				if domain not in missing:
					print ("missing: ",domain, _domain)
					missing.append(domain)
				
	print (len(missing))
	with open("data/domainCDNMap_"+country+".json", 'w') as fp:
		json.dump(domainCDNMap, fp)
	with open("data/missingCdnizedDomains_"+country+".json", 'w') as fp:
		json.dump(missing, fp)

def dnsRipeResult(country,_type):
	resultPerQuery=json.load(open("results/dnsRipeResultPerQuery_"+_type+"_"+country+".json"))
	dict={}
	for cdn in resultPerQuery:
		for domain in resultPerQuery[cdn]:
			if domain not in dict:
				dict[domain]={}
			for _id in resultPerQuery[cdn][domain]:
				for replica in resultPerQuery[cdn][domain][_id]:
					if replica not in dict[domain]:
						dict[domain][replica]=1
					else:
						dict[domain][replica]+=1
	with open("results/dnsRipeResult_"+_type+"_"+country+".json", 'w') as fp:
		json.dump(dict, fp)

def calculateLatency(country):
	#results storing for local in US and distant in AR
	ripeResultTracerouteLocal=json.load(open("results/tracerouteRipeResult_local_"+country+".json"))
	localCommonPrefixes=json.load(open("results/localCommonPrefixes_"+country+".json"))
	distantCommonPrefixes=json.load(open("results/distantCommonPrefixes_"+country+".json"))
	
	local={}
	hopsDict={}
	rttDict={}
	for cdn in ripeResultTracerouteLocal:
		if cdn not in hopsDict:
			hopsDict[cdn]={}
			hopsDict[cdn]["local"]=[]
			rttDict[cdn]={}
			rttDict[cdn]["local"]=[]
		if cdn not in local:
			local[cdn]={}
		for prefix in localCommonPrefixes[cdn]:
			if prefix not in local[cdn]:
				local[cdn][prefix]={}
				local[cdn][prefix]["hops"]=[]
				local[cdn][prefix]["rtt"]=[]
			for run in ripeResultTracerouteLocal[cdn][prefix]:
				try:
					hops=len(run[0]["result"])
					local[cdn][prefix]["hops"].append(hops)
				except:
					a=1
					# continue
				try:
					rttStart=run[0]["timestamp"]
					rttEnd=run[0]["endtime"]
					rtt=rttEnd-rttStart
					# print (rttStart,rttEnd,rtt)
					local[cdn][prefix]["rtt"].append(rtt)
					print (local[cdn][prefix]["rtt"],rtt)
				except:
					a=1
			hopsDict[cdn]["local"].append(np.median(local[cdn][prefix]["hops"]))
			rttDict[cdn]["local"].append(np.median(local[cdn][prefix]["rtt"]))

			# if cdn =="Akamai":
			# 	print(prefix,np.median(local[cdn][prefix]))
			# medianLatencies.append(np.median(local[cdn][prefix]))

		# break
	print ("\n\n")
	distant={}
	ripeResultTracerouteDistant=json.load(open("results/tracerouteRipeResult_distant_"+country+".json"))
	for cdn in ripeResultTracerouteDistant:
		if "distant" not in hopsDict[cdn]:
			hopsDict[cdn]["distant"]=[]
			rttDict[cdn]["distant"]=[]
		if cdn not in distant:
			distant[cdn]={}
		for prefix in distantCommonPrefixes[cdn]:
			if prefix not in distant[cdn]:
				distant[cdn][prefix]={}
				distant[cdn][prefix]["hops"]=[]
				distant[cdn][prefix]["rtt"]=[]

			for run in ripeResultTracerouteDistant[cdn][prefix]:
				try:
					hops=len(run[0]["result"])
					distant[cdn][prefix]["hops"].append(hops)
				except:
					a=1
				try:
					rttStart=run[0]["timestamp"]
					rttEnd=run[0]["endtime"]
					rtt=rttEnd-rttStart
					distant[cdn][prefix]["rtt"].append(rtt)
				except:
					a=1
			hopsDict[cdn]["distant"].append(np.median(distant[cdn][prefix]["hops"]))
			rttDict[cdn]["distant"].append(np.median(distant[cdn][prefix]["rtt"]))


			# if cdn =="Akamai":
			# 	print(prefix,np.median(distant[cdn][prefix]))
		# break
	print ("hops",hopsDict["Akamai"])
	print ("rtt",rttDict["Akamai"])

	for cdn in hopsDict:
		sortedDataLocal=np.sort(hopsDict[cdn]["local"])
		pDataLocal=1. * np.arange(len(sortedDataLocal))/(len(sortedDataLocal)-1)

		sortedDataDistant=np.sort(hopsDict[cdn]["distant"])
		pDataDistant=1. * np.arange(len(sortedDataDistant))/(len(sortedDataDistant)-1)

		plt.plot(sortedDataLocal,pDataLocal,color='c',label="AR_local;/24 Prefix")
		plt.plot(sortedDataDistant,pDataDistant,color='m',label="AR_distant;/24 Prefix")

		plt.legend()
		plt.title(cdn)
		plt.ylabel("CDF")
		plt.xlabel("HopCount")
		plt.margins(0.02)
		if not os.path.exists("graphs/localvsdistant"):
			os.mkdir("graphs/localvsdistant")
		plt.savefig("graphs/localvsdistant/tracerouteHops"+cdn)

		plt.clf()

	for cdn in rttDict:
		sortedDataLocal=np.sort(rttDict[cdn]["local"])
		pDataLocal=1. * np.arange(len(sortedDataLocal))/(len(sortedDataLocal)-1)

		sortedDataDistant=np.sort(rttDict[cdn]["distant"])
		pDataDistant=1. * np.arange(len(sortedDataDistant))/(len(sortedDataDistant)-1)

		plt.plot(sortedDataLocal,pDataLocal,color='c',label="AR_local;/24 Prefix")
		plt.plot(sortedDataDistant,pDataDistant,color='m',label="AR_distant;/24 Prefix")

		plt.legend()
		plt.title(cdn)
		plt.ylabel("CDF")
		plt.xlabel("RTTCount")
		plt.margins(0.02)
		if not os.path.exists("graphs/localvsdistant"):
			os.mkdir("graphs/localvsdistant")
		plt.savefig("graphs/localvsdistant/tracerouteRTT"+cdn)

		plt.clf()

	# print (local)		
def commonPrefixes(cdns):
	cdns=["Google","Amazon CloudFront","Fastly","Akamai"]
	cdnMapping=json.load(open("data/cdn_mapping_"+country+".json"))

	local_24=json.load(open("results/ip_24_grouping_local_US.json"))
	distant_24_IN=json.load(open("results/ip_24_grouping_distant_US.json"))
	distant_24_AR=json.load(open("results/ip_24_grouping_distant_AR.json"))

	local_dict={}
	distant_IN={}
	distant_AR={}
	for cdn in cdns:
		if cdn not in local_dict:
			local_dict[cdn]={}
		if cdn not in distant_IN:
			distant_IN[cdn]={}
		if cdn not in distant_AR:
			distant_AR[cdn]={}

		for domain in cdnMapping[cdn]:
			try:
				for prefix in local_24[domain]:
					if prefix.split("/24")[0] in local_dict[cdn]:
						local_dict[cdn][prefix.split("/24")[0]]+=local_24[domain][prefix]
					else:
						local_dict[cdn][prefix.split("/24")[0]]=local_24[domain][prefix]

				for prefix in distant_24_IN[domain]:
					if prefix.split("/24")[0] in distant_IN[cdn]:
						distant_IN[cdn][prefix.split("/24")[0]]+=distant_24_IN[domain][prefix]
					else:
						distant_IN[cdn][prefix.split("/24")[0]]=distant_24_IN[domain][prefix]

				for prefix in distant_24_AR[domain]:
					if prefix.split("/24")[0] in distant_AR[cdn]:
						distant_AR[cdn][prefix.split("/24")[0]]+=distant_24_AR[domain][prefix]
					else:
						distant_AR[cdn][prefix.split("/24")[0]]=distant_24_AR[domain][prefix]
			except:
				print (cdn,domain)
				continue
	popularLocal={}
	popularDistant_IN={}
	popularDistant_AR={}
	for cdn in cdns:
		_min=min([len(local_dict[cdn]),len(distant_IN[cdn]),len(distant_AR[cdn])])
		print (cdn,_min)
		sortedlocal = sorted(local_dict[cdn], key=local_dict[cdn].get, reverse=True)[:_min]
		sorteddistant_IN = sorted(distant_IN[cdn], key=distant_IN[cdn].get, reverse=True)[:_min]
		sorteddistant_AR = sorted(distant_AR[cdn], key=distant_AR[cdn].get, reverse=True)[:_min]
		popularLocal[cdn]=sortedlocal
		popularDistant_IN[cdn]=sorteddistant_IN
		popularDistant_AR[cdn]=sorteddistant_AR

	with open("results/"+"localCommonPrefixes_US.json", 'w') as fp:
		json.dump(popularLocal, fp)
	with open("results/"+"distantCommonPrefixes_IN.json", 'w') as fp:
		json.dump(popularDistant_IN, fp)
	with open("results/"+"distantCommonPrefixes_AR.json", 'w') as fp:
		json.dump(popularDistant_AR, fp)

def runAnalysis(country,domains,local,distant,cdnMapping):
	
	# runCosineSimilarity(d omains,local,distant,cdnMapping,"cosineSimilarity_"+country)

	# _dict=ip_prefix_grouping("local",local,country,"/24","ip_24_grouping_")
	_dict=ip_prefix_grouping(local,"/24")
	with open("results/"+"ip_24_grouping_local"+"_"+country+".json", 'w') as fp:
		json.dump(_dict, fp)

	_dict=ip_prefix_grouping(distant,"/24")
	# _dict=ip_prefix_grouping("distant",distant,country,"/24","ip_24_grouping_")
	with open("results/"+"ip_24_grouping_distant"+"_"+country+".json", 'w') as fp:
		json.dump(_dict, fp)

	local_24=json.load(open("results/ip_24_grouping_local_"+country+".json"))
	distant_24=json.load(open("results/ip_24_grouping_distant_"+country+".json"))

	runCosineSimilarity(domains,local_24,distant_24,cdnMapping,"cosSim_24_"+country)


	# _dict=ip_prefix_grouping("local",local,country,"/20","ip_20_grouping_")
	# _dict=ip_prefix_grouping(local,"/20")
	# with open("results/"+"ip_20_grouping_local"+"_"+country+".json", 'w') as fp:
	# 	json.dump(_dict, fp)

	# # _dict=ip_prefix_grouping("distant",distant,country,"/20","ip_20_grouping_")
	# _dict=ip_prefix_grouping(distant,"/20")
	# with open("results/"+"ip_20_grouping_distant"+"_"+country+".json", 'w') as fp:
	# 	json.dump(_dict, fp)

	# local_20=json.load(open("results/ip_20_grouping_local_"+country+".json"))
	# distant_20=json.load(open("results/ip_20_grouping_distant_"+country+".json"))

	# runCosineSimilarity(domains,local_20,distant_20,cdnMapping,"cosSim_20_"+country)

if __name__ == "__main__":
	country="US"
	# local=json.load(open("results/dnsRipeResult_local_"+country+".json"))
	# distant=json.load(open("results/dnsRipeResult_distant_"+country+".json"))
	domains=json.load(open("data/uniqueDomains"+country+".json"))
	cdnMapping=json.load(open("data/cdn_mapping_"+country+".json"))
	
	local_cdnized=json.load(open("results/dnsRipeResultPerQuery_local_"+country+".json"))
	distant_cdnized=json.load(open("results/dnsRipeResultPerQuery_distant_"+country+".json"))
	# cdnMap={}
	# file1 = open('data/cdnMap', 'r')
	# Lines = file1.readlines()
	# for line in Lines:
	# 	cdn=line.split(",")
	# 	cdnMap[cdn[0]]=[]
	# 	sites=cdn[1].split(" ")
	# 	for site in sites:
	# 		if '\n' in site:
	# 			site=site.replace('\n','')
	# 		cdnMap[cdn[0]].append(site)	

	cdns=["Google","Amazon CloudFront","Fastly","Akamai"]
	#analysis results for cosine similarity
	# dnsRipeResult(country,"distant")
	# dnsRipeResult(country,"local")
	# distant=json.load(open("results/dnsRipeResult_distant_"+country+".json"))
	# local=json.load(open("results/dnsRipeResult_local_"+country+".json"))
	# runAnalysis(country,domains,local,distant,cdnMapping)

	# #analysis results for self similarity
	# probeDict=json.load(open("results/probeDict_local"+"_"+country+".json"))
	# for domain in probeDict:
	# 	ids=[]
	# 	count=0
	# 	for probe in probeDict[domain]:
	# 		count+=1
	# 		for id in probeDict[domain][probe]:
	# 			ids.append(id)
	# 	print ("len of ids: ",len(ids)," probeCount= ",count)
	# len of ids:  101  probeCount=  49 per domain
	# cdns=["Google"]
	# self_similarityDict={}
	# self_similarityDict=self_similarity3(local_cdnized,"local",self_similarityDict,cdns)
	# self_similarityDict=self_similarity3(distant_cdnized,"distant",self_similarityDict,cdns)


	# with open("results/self_similarityDict_"+country+".json", 'w') as fp:
	# 	json.dump(self_similarityDict, fp)
	

	#run for Argentina
	# countryD="AR"
	# #analysis results for self similarity
	# self_similarityDict={}
	# distant_cdnized_AR=json.load(open("results/dnsRipeResultPerQuery_distant_"+countryD+".json"))
	# self_similarityDict=self_similarity3(local_cdnized,"local",self_similarityDict,cdns)
	# self_similarityDict=self_similarity3(distant_cdnized_AR,"distant",self_similarityDict,cdns)
	# with open("results/self_similarityDict_"+countryD+".json", 'w') as fp:
	# 	json.dump(self_similarityDict, fp)

	# #analysis results for cosine similarity
	# dnsRipeResult(countryD,"distant")
	# distant=json.load(open("results/dnsRipeResult_distant_"+countryD+".json"))
	# runAnalysis(countryD,domains,local,distant,cdnMapping)

	# calculateLatency(countryD)
	commonPrefixes(cdns)
		