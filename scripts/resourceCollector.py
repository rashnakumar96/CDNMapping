from selenium import webdriver
import json
from browsermobproxy import Server
from bs4 import BeautifulSoup
import os, time
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
from os.path import isfile, join
import tldextract
import subprocess
import dns.resolver



project_path=os.path.dirname(os.path.abspath(__file__))

class Har_generator:
	def __init__(self):
		self.hars = []
		self.server = Server(join(project_path, "browsermob-proxy-2.1.4", "bin", "browsermob-proxy"))
		self.server.start()
		self.proxy = self.server.create_proxy(params={"trustAllServers": "true"})
		options = webdriver.ChromeOptions()
		options.add_argument("--proxy-server={}".format(self.proxy.proxy))	
		options.add_argument("--ignore-ssl-errors=yes")
		options.add_argument("--ignore-certificate-errors")
		options.add_argument("--headless")

		self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)

	def __del__(self):
		self.server.stop()
		self.driver.quit()

	# loads up a site
	# takes a site url
	# returns a json har object
	def get_har(self, site):
		
		try:
			name = site
			self.proxy.new_har(name)
			self.driver.get("https://"+site)
			time.sleep(1)
			return self.proxy.har
		except Exception as e:
			print(str(e))
			return None

		
	# calls get_har for each site
	# takes a list of site urls
	# returns a dictionary of site url and json har objects
	def get_hars(self, sites):
		x = 0
		hars = []
		for site in sites:
			print("%d: Working on %s" % (x, site))
			har = self.get_har(site)
			hars.append(har)
			self.hars.append(har)
			x = x + 1
		return hars

class Resource_collector:
	def __init__(self):
		self.resources = []

	def dump(self, fn_prefix,country):
		print(join(fn_prefix,"alexaResources"+country+".json"))	
		# utils.dump_json(self.resources, join(fn_prefix,"alexaResources"+country+".json"))
		with open(join(fn_prefix,"alexaResources"+country+".json"), 'w') as fp:
			json.dump(self.resources, fp)

		# utils.dump_json(self.resources, join(project_path,fn_prefix,"alexaResources"+country+".json"))


	# extracts all the resources from each har object
	# takes a list of har json objects
	# stores in the object resources
	def collect_resources(self, hars,country):
		for har in hars:
			if har and "log" in har.keys() and "entries" in har["log"].keys():
				for entry in har["log"]["entries"]:
					resource = entry["request"]["url"]
					if resource not in self.resources:
						self.resources.append(str(resource))


class Url_processor:
	def __init__(self,country):
		self.cdn_mapping = {}
		# self.resources_mapping = utils.load_json(join(project_path, "analysis", "measurements", country, "alexaResources"+country+".json"))
		self.domains=json.load(open("uniqueDomains"+country+".json"))

		self.options = webdriver.ChromeOptions()
		self.options.add_argument("--ignore-ssl-errors=yes")
		self.options.add_argument("--ignore-certificate-errors")
		# self.options.add_argument("--headless")
		self.country=country

		self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=self.options)

	def __del__(self):
		self.driver.quit()

	def restart_drive(self):
		print("Restarting...")
		self.driver.quit()
		self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=self.options)

	def dump(self, fn_prefix):
		utils.dump_json(self.cdn_mapping, join(fn_prefix,"PopularcdnMapping.json"))



	# Find cdn given a file of the resources
	# Takes a list of unique domains
	# Returns a dictionary containing the found CDNs for each domain
	def find_cdn(self):
		# domains = []
		# for resource in self.resources_mapping:
		# 	if utils.url_to_domain(resource) not in domains:
		# 		domains.append(utils.url_to_domain(resource))
		domains=self.domains
		print (domains)
		i = 0
		self.driver.get("https://www.cdnplanet.com/tools/cdnfinder/")
		total = len(domains)
		for resource in domains:
			if i > 0 and i % 50 == 0:
				self.restart_drive()
				self.driver.get("https://www.cdnplanet.com/tools/cdnfinder/")

			print("%.2f%% completed" % (100 * i / total))

			for _ in range(3):
				try:
					self.driver.find_element_by_xpath("//*[@id=\"tool-form-main\"]").clear()
					self.driver.find_element_by_xpath("//*[@id=\"tool-form-main\"]").send_keys(resource)
					self.driver.find_element_by_xpath("//*[@id=\"hostname-or-url\"]").click()
					self.driver.find_element_by_xpath("//*[@id=\"tool-form\"]/button").click()
					time.sleep(3)

					doc = BeautifulSoup(self.driver.page_source, "html.parser")
					domain=doc.findAll('code', attrs={"class" : "simple"})
					cdn=doc.findAll('strong')
					site=domain[0].text
					cdn=cdn[0].text
					print (site,cdn)
					if cdn not in self.cdn_mapping:
						self.cdn_mapping[cdn]=[]
					self.cdn_mapping[cdn].append(resource)
					break

				except Exception as e:
					print("error: ",str(e))
					time.sleep(2)


			time.sleep(2)
			i += 1
		with open("cdn_mapping_"+self.country+".json", 'w') as fp:
			json.dump(self.cdn_mapping, fp)   

	def collectPopularCDNResources(self,country):
		unique=[]
		with open(join(project_path, "analysis", "measurements", country, "AlexaUniqueResources.txt"),"w") as f:
			for cdn in self.cdn_mapping:
				for domain in self.cdn_mapping[cdn]:
					for resource in self.resources_mapping:
						if domain in resource:
							if resource not in unique:
								f.write(resource+"\n")
								unique.append(resource)
							
			f.close()

def extractResources(region,file):
	hm = Har_generator()
	rc = Resource_collector()

	allRegionalSites=json.load(open(file))
	sites=allRegionalSites[region]
	hars = hm.get_hars(sites)
	rc.collect_resources(hars,region)
	rc.dump(join("results", "sigcommRes",region), region)
	del hm
	del rc

	resources=json.load(open("results/sigcommRes/"+region+"/alexaResources"+region+".json"))
	all_domains=[]	
	for resource in resources:
		domain=url_to_domain(resource)
		if 'www.' in domain:
			domain=domain.replace('www.','')
		if domain not in all_domains:
			all_domains.append(domain)
	with open(join("results/sigcommRes/"+region+"/alexaResourcesDomains"+region+".json"), 'w') as fp:
		json.dump(all_domains, fp)

def url_to_domain(url):
    ext = tldextract.extract(url)
    if ext[0] == '':
        ext = ext[1:]
    return ".".join(ext)

def dump_json(data, fn):
    with open(fn, 'w') as fp:
        json.dump(data, fp)

def populate_cdnMap():
	cdn_map={}
	file1 = open('data/cdnMap', 'r')
	Lines = file1.readlines()

	# Strips the newline character
	for line in Lines:
		cdn=line.split(",")
		# print(cdn[0])
		cdn_map[cdn[0]]=[]
		sites=cdn[1].split(" ")
		for site in sites:
			if '\n' in site:
				site=site.replace('\n','')
			cdn_map[cdn[0]].append(site)
	return cdn_map

def findCDNCDNFinder(domain,domaincdnMap,cnameDomainMap,region):
	print ("running cdnfinder for domain: ",domain)
	try:
		cmd='docker run -it turbobytes/cdnfinder cdnfindercli --phantomjsbin="/bin/phantomjs" --full http://'+domain
		mycmd=subprocess.getoutput(cmd)
		dict_response=str(mycmd).split("phantomjs is already installed")[1]
		ans = json.loads(dict_response)
		for _dict in ans['everything']:
			domaincdnMap[domain]=_dict['cdn']
			cnameDomainMap[domain]=_dict["cnames"]
		dump_json(domaincdnMap,"data/CDNMaps/"+region+"/domainCDNMap.json")
		dump_json(cnameDomainMap,"data/CDNMaps/"+region+"/cnameDomainMap.json")

	except Exception as e:
		print (domain," gives error with cdnfindercli",str(e))	
		domaincdnMap[domain]=None
		cnameDomainMap[domain]=[]
		dump_json(domaincdnMap,"data/CDNMaps/"+region+"/domainCDNMap.json")
		dump_json(cnameDomainMap,"data/CDNMaps/"+region+"/cnameDomainMap.json")	



if __name__ == "__main__":
	
	# region="North America_AR_IN"
	region="Western Europe_SE_IN"
	if not os.path.exists("results/sigcommRes/"+region):
		os.mkdir("results/sigcommRes/"+region)

	if not os.path.exists("data/CDNMaps/"+region):
		os.mkdir("data/CDNMaps/"+region)

	extractResources(region,"results/sigcommRes/overlapDict.json")


	try:
		domainCDNMap=json.load(open("data/CDNMaps/"+region+"/domainCDNMap.json"))
	except:
		domainCDNMap={}
	try:
		cnameDomainMap=json.load(open("data/CDNMaps/"+region+"/cnameDomainMap.json"))
	except:
		cnameDomainMap={}

	all_domains=json.load(open("results/sigcommRes/"+region+"/alexaResourcesDomains"+region+".json"))

	for domain in all_domains:
		if domain in domainCDNMap and domain in cnameDomainMap:
			continue
		findCDNCDNFinder(domain,domainCDNMap,cnameDomainMap,region)

	remainingResources=json.load(open("data/CDNMaps/"+region+"/domainCDNMap.json"))
	_dictcnamemap=json.load(open("data/CDNMaps/"+region+"/cnameDomainMap.json"))
	cdnmap=populate_cdnMap()
	dump_json(cdnmap,'data/cdnMap.json')	
	count=0
	_dict={}
	for domain in remainingResources:
		if remainingResources[domain]!= None:
			continue
		count+=1
		try:
			result = dns.resolver.query(domain, 'CNAME')
			cnames=[]
			_cdn=""
			for cnameval in result:
				try:
					cname=str(cnameval.target)
					cnames.append(cname)
					for cdn in cdnmap:
						for cn in cdnmap[cdn]:
							if cname in cn:
								_cdn=cdn
							if cn in cname:
								_cdn=cdn
					print (domain,cname,_cdn)
					remainingResources[domain]=_cdn
					_dictcnamemap[domain].append(cname)
				except Exception as e:
					print (str(e))
					continue
		except Exception as e:
			continue	
	dump_json(remainingResources,"data/CDNMaps/"+region+"/domainCDNMapUpdated.json")
	dump_json(_dictcnamemap,"data/CDNMaps/"+region+"/cnameDomainMapUpdated.json")

	cnameCDNDict={}
	for domain in remainingResources:
		if remainingResources[domain]== None:
			continue
		cdn=remainingResources[domain]
		if cdn not in cnameCDNDict:
			cnameCDNDict[cdn]=[]
		cnames=_dictcnamemap[domain]
		cnameCDNDict[cdn].append(cnames[-1])
	dump_json(cnameCDNDict,"data/CDNMaps/"+region+"/cnameCDNMap.json")

	cnameCDNDict=json.load(open("data/CDNMaps/"+region+"/cnameCDNMap.json"))
	for cdn in cnameCDNDict:
		if cdn=="Cloudfront":
			cnameCDNDict["Amazon Cloudfront"]+=cnameCDNDict[cdn]
	try:
		del cnameCDNDict["Cloudfront"]
	except Exception as e:
		print (str(e))
	for cdn in cnameCDNDict:
		uniqueCnames=set(cnameCDNDict[cdn])
		uniqueCnames=list(uniqueCnames)
		cnameCDNDict[cdn]=uniqueCnames
	dump_json(cnameCDNDict,"data/CDNMaps/"+region+"/cnameCDNMap.json")








