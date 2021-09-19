import json
from functools import reduce
import os

regionDict={
"South America": ["CL","AR","BR"],
"North America": ["US","CA","CR"],
"Western Europe": ["DE","FR","NL"],
"Northern Europe": ["GB","SE","NO"],
"Southern Europe": ["GR","IT","ES"],
"Eastern Europe": ["RU","HU","PL"],
"Middle East": ["TR","AE","IL"],
"East Asia": ["JP","KR","TW"],
"South East Asia": ["SG","ID","MY"],
"South Asia": ["BD","IN","PK"],
"Central Asia": ["UZ","KZ","KG"],
"West Asia": ["QA","OM","SA"],
"Northern Africa": ["EG","LY","DZ"],
"Sub Saharan Africa": ["ZA","KE","ZW"],
"Oceania": ["NZ","AU"]
}

def regionalOverlap():
	allSites=json.load(open("data/alexaTop500SitesCountries.json"))
	overlapDict={}
	overlapCountDict={}
	for region in regionDict:
		regionalSites=[]
		for country in regionDict[region]:
			regionalSites.append(allSites[country])
		regionalCommonSites=list(reduce(set.intersection, [set(item) for item in regionalSites]))
		overlapDict[region]=regionalCommonSites
		overlapCountDict[region]=len(regionalCommonSites)

	if not os.path.exists("results/sigcommRes"):
		os.mkdir("results/sigcommRes")
		
	with open("results/sigcommRes/overlapDict.json", 'w') as fp:
		json.dump(overlapDict, fp)

def countrySiteOverlap(region,country1,country2):
	allSites=json.load(open("data/alexaTop500SitesCountries.json"))
	file="results/sigcommRes/overlapDict.json"
	allRegionalSites=json.load(open(file))

	regionalSites=[]
	regionalSites.append(allRegionalSites[region])
	regionalSites.append(allSites[country2])
	regionalSites.append(allSites[country1])
	regionalCommonSites=list(reduce(set.intersection, [set(item) for item in regionalSites]))
	print (len(allRegionalSites[region]),allRegionalSites[region])
	
	region=region+"_"+country1+"_"+country2
	print (region,country1,country2,len(regionalCommonSites))
	print (regionalCommonSites)
	allRegionalSites[region]=regionalCommonSites
	with open("results/sigcommRes/overlapDict.json", 'w') as fp:
		json.dump(allRegionalSites, fp)

if __name__ == "__main__":
	# countrySiteOverlap("North America","AR","IN")
	countrySiteOverlap("Western Europe","SE","IN")

	# countrySiteOverlap("North America","IN")





