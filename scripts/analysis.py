from collections import Counter
import json
import ipaddress
import dns.resolver
import tldextract




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

def ip_prefix_grouping(approach,file,country,prefix,resultname):
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
	with open("results/"+resultname+approach+"_"+country+".json", 'w') as fp:
		json.dump(dict, fp)

def runCosineSimilarity(domains,local,distant,cdnMapping,filename):
	dict={}
	vec1=[]
	vec2=[]
	for domain in domains:
		try:
			vec1=list(local[domain].keys())
			vec2=list(distant[domain].keys())
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

def runAnalysis(country,domains,local,distant,cdnMapping):
	for domain in domains:
		if domain in distant and domain in local:
			for key in distant[domain].keys():
				if key in local[domain].keys():
					print (domain,key)
					break

	runCosineSimilarity(domains,local,distant,cdnMapping,"cosineSimilarity_"+country)


	ip_prefix_grouping("local",local,country,"/24","ip_24_grouping_")
	ip_prefix_grouping("distant",distant,country,"/24","ip_24_grouping_")

	local_24=json.load(open("results/ip_24_grouping_local_"+country+".json"))
	distant_24=json.load(open("results/ip_24_grouping_distant_"+country+".json"))

	runCosineSimilarity(domains,local_24,distant_24,cdnMapping,"cosSim_24_"+country)


	ip_prefix_grouping("local",local,country,"/20","ip_20_grouping_")
	ip_prefix_grouping("distant",distant,country,"/20","ip_20_grouping_")

	local_20=json.load(open("results/ip_20_grouping_local_"+country+".json"))
	distant_20=json.load(open("results/ip_20_grouping_distant_"+country+".json"))

	runCosineSimilarity(domains,local_20,distant_20,cdnMapping,"cosSim_20_"+country)

if __name__ == "__main__":
	country="US"
	local=json.load(open("results/dnsRipeResult_local_"+country+".json"))
	distant=json.load(open("results/dnsRipeResult_distant_"+country+".json"))
	domains=json.load(open("data/uniqueDomains"+country+".json"))
	cdnMapping=json.load(open("data/cdn_mapping_"+country+".json"))

	cdnMap={}
	file1 = open('data/cdnMap', 'r')
	Lines = file1.readlines()
	for line in Lines:
		cdn=line.split(",")
		cdnMap[cdn[0]]=[]
		sites=cdn[1].split(" ")
		for site in sites:
			if '\n' in site:
				site=site.replace('\n','')
			cdnMap[cdn[0]].append(site)

	# use Aqsa's cdnMap to find cdn
	# findCDNs(domains,cdnMap,country)

	runAnalysis(country,domains,local,distant,cdnMapping)

	
	
	
	
	

# {'youtube.com': 0.06950480468569159, 'www.youtube.com': 0.0}
	