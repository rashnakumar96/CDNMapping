from ripe.atlas.cousteau import (
  Dns,
  AtlasSource,
  AtlasCreateRequest
)
from ripe.atlas.cousteau import AtlasSource
from datetime import datetime
from ripe.atlas.cousteau import AtlasResultsRequest
import json
from ripe.atlas.sagan import DnsResult
import time
import dns
import dns.resolver
import tldextract
import requests
from ripe.atlas.sagan import DnsResult
import random

#use public dns country specific resolvers for distant remote ones e.g using probe in US so use ripe's local DNS resolver
# or use Germany's public dns resolver as distant
# using type A query, but hits cname answers and multiple A answers so use the ip of the A records, did 100 runs (got 0.06 and 0 similarity) 
#use domains or cnames to resolve instead of resources? 
# should www.youtube.com and youtube be treated differently, because www.youtube.com gives cname responses

# current cdn approach is use har file, find resources, extract tld of resources find the cdn of tld. Extract cnames of the cdn 
# and then do the comparison of tld of resources and and cnames of cdn to find out if third party or not

# Aqsa's approach:one way to detect a CDN is to look at CNAME redirects for the internal (website- owned) resources of a website 
# and match it against a CNAME-to- CDN map.
# Basically We fetch and render the landing page of the website using phantomJS, a headless browser, and record all hostnames 
# that serve at least one object on the page. 
def cdn_Resources(country,cdn):
    cdnMap=json.load(open("data/cdn_mapping_"+country+".json"))
    # resultFile=json.load(open("results/cosineSimilarity_"+country+".json"))
    # resources=[]
    # for resource in cdnMap[cdn]:
        # if resource not in resultFile:
            # resources.append(resource)
    # return resources
    return cdnMap[cdn]


def uniqueDomains(file,country):
    uniqueDomains=[]
    with open(file,'r') as f:
        for url in f:
            domain=url_to_domain(url)
            # if "www." in domain: 
                # domain=domain.split("www.")[1]
            if domain not in uniqueDomains:
                uniqueDomains.append(domain)
    with open("data/uniqueDomains"+country+".json", 'w') as fp:
        json.dump(uniqueDomains, fp)
    return uniqueDomains

def url_to_domain(url):
    ext = tldextract.extract(url)
    if ext[0] == '':
        ext = ext[1:]
    return ".".join(ext)

def runMeasurements(_type,country,domainList,runs):
    # dnsServers=["182.19.95.34","203.201.60.12","223.31.121.171","182.71.213.139","111.93.163.56"] #resolvers in India
    dnsServers=["190.151.144.21","200.55.54.234","200.110.130.194","157.92.190.15","179.60.235.209"] #resolvers in AR


    tryTimes=0
    try:
        measurement_ids=json.load(open("results/dnsRipeMsmIds_"+_type+"_"+country+".json"))
    except:
        measurement_ids=[]
    for run in range(runs):
        if run!=0 and run%5==0:
            time.sleep(1*60)
        print ("Doing run: ",run)
        for domain in domainList:
            ind=random.randint(0,len(dnsServers)-1)
            target=dnsServers[ind]
            
            dns = Dns(
                af=4,
                # target="182.19.95.34", #resolver in IN
                target=target,
                description="Dns Resolution of CDNized Resources",
                query_class="IN",
                query_type="A",
                query_argument=domain,
                set_rd_bit= True, 
                type= "dns", 
                include_qbuf=True,
                include_Abuf=True
                # use_probe_resolver= True
            )

            source = AtlasSource(
                # type="area",
                # value="WW",
                type="country",
                value="US",
                requested=1,
                tags={"include":["system-ipv4-works"]}
            )

            ATLAS_API_KEY = "b7fb25c3-a5fc-4785-8f35-6830a6fdb6a4"

            atlas_request = AtlasCreateRequest(
                start_time=datetime.utcnow(),
                key=ATLAS_API_KEY,
                measurements=[dns],
                sources=[source],
                is_oneoff=True
            )
            # while (tryTimes<1):
            (is_success, response) = atlas_request.create()
            if is_success:
                _id=response["measurements"]
                print("SUCCESS: measurement created: %s" % response["measurements"],domain,target)
                # break
            else:
                # tryTimes+=1
                print ("failed to create measurement: %s" % response,domain,target)
                # if tryTimes>=2:
                raise Exception("failed to create measurement: %s" % response)
                # time.sleep(10)

            print (str(_id[0]))

            measurement_ids.append((domain,str(_id[0])))

            with open("results/dnsRipeMsmIds_"+_type+"_"+country+".json", 'w') as fp:
                json.dump(measurement_ids, fp)
    # return measurement_ids

def FetchResults(_type,country,domainList,cdn,probeDict):
    print (cdn,domainList) 
    try:
        measurement_ids=json.load(open("results/dnsRipeMsmIds_"+_type+"_"+country+".json"))
    except:
        return
    try: 
        dict=json.load(open("results/dnsRipeResultPerQuery_"+_type+"_"+country+".json"))
    except:
        dict={}  
    if cdn not in dict:
        dict[cdn]={}
    count=0
    for domain,id in measurement_ids:
        # if count%20==0:
        #     time.sleep(0.2)
        count+=1
        if domain not in domainList:
            continue
        if domain not in probeDict:
            probeDict[domain]={}
        kwargs = {
        "msm_id": id
        }
        print(domain,"Fetching %s" % id," \% done",100*count/len(measurement_ids))
        is_success, results = AtlasResultsRequest(**kwargs).create()

        if is_success:
            # print(results,"\n\n")
            try:
                my_result = DnsResult(results[0])
                #comment the next two lines
                print ("print Result: ",str(my_result).split("Probe #")[1])
                probeId=str(my_result).split("Probe #")[1]
                if probeId not in probeDict[domain]:          
                    probeDict[domain][probeId]=[]
                if id not in probeDict[domain][probeId]:
                    probeDict[domain][probeId].append(id)
                    with open("results/probeDict_"+_type+"_"+country+".json", 'w') as fp:
                        json.dump(probeDict, fp)
                continue
            except Exception as e:
                print ("Fetching wasn't successful: ",domain,id, str(e))
                continue
        else:
            continue
        # print (my_result)
        try:
            dnsAnswer=my_result.responses[0].abuf.answers
        except Exception as e:
            print ("Couldn't decode the answer: ",domain,id, str(e))
            continue
        if domain not in dict[cdn]:
            dict[cdn][domain]={}
        if id not in dict[cdn][domain]:
            dict[cdn][domain][id]=[]
        else:
            continue   

        for result in dnsAnswer:
            try:
                ip_addr=result.address
                dict[cdn][domain][id].append(ip_addr)
                # if ip_addr not in dict[domain]:
                #     dict[domain][ip_addr]=0

                # dict[domain][ip_addr]+=1

            except Exception as e:
                # print (domain,id,result, str(e))
                continue
    #uncomment this    
    # with open("results/dnsRipeResultPerQuery_"+_type+"_"+country+".json", 'w') as fp:
    #     json.dump(dict, fp)
        with open("results/probeDict_"+_type+"_"+country+".json", 'w') as fp:
            json.dump(probeDict, fp)

# distant run from 51th index of unique domains.
#local done 
if __name__ == "__main__":
    # runMeasurements(_type,"US",domainList,5)
    country="US" #set country for resolvers
    _type="local" #change probe resolver, value of target and number of resolvers too
    # start=0
    # end=55
    # domainList=domainList[start:end]
    # print (domainList)

    #if want use entire domainList
    # fulldomainList=uniqueDomains("AlexaUniqueResourcesUS.txt",country)

    #if want to use domainList of a cdn
    # cdn="Google"
    # fulldomainList=cdn_Resources("US",cdn)
    # print (len(fulldomainList),fulldomainList)   



    # for x in range(start,len(fulldomainList),3):
    # # for x in range(start,59,3):

    #     # domainList=uniqueDomains("AlexaUniqueResourcesUS.txt",country)
    #     domainList=cdn_Resources("US",cdn)
    #     start=x
    #     end=start+3
    #     print (start,end)
    # #     # exit()
    #     domainList=domainList[start:end]
    #     print (domainList)
    #     while 1: 
    #         try:
    #             measurement_ids=json.load(open("results/dnsRipeMsmIds_"+_type+"_"+country+".json"))
    #         except Exception as e:
    #             print (str(e))
    #             measurement_ids={}
    #         dict={}
    #         breakingCond=0
    #         for domain,id in measurement_ids:
    #             if domain not in dict:
    #                 dict[domain]=0
    #             dict[domain]+=1

    #         if domainList[0] in dict:    
    #             runs=100-dict[domainList[0]]
    #         else:
    #             runs=100
    #         if runs<=0:
    #             print ("Done for the set: ",start,end)
    #             break
    #         print ("Starting to run for: ",runs," domainList indexes",start,end)
    #         try:
    #             runMeasurements(_type,country,domainList,runs)
    #         except:
    #             time.sleep(300)
    #         FetchResults(_type,country,domainList,cdn)
    # FetchResults(_type,"AR",fulldomainList,cdn)

    # fulldomainList=cdn_Resources(country,"Akamai")
    # FetchResults(_type,country,fulldomainList,"Akamai")
    # time.sleep(60)
    # fulldomainList=cdn_Resources(country,"Google")
    # print (fulldomainList)

    # remaining=json.load(open("results/remainingDomains.json"))
    # fulldomainList=remaining["Google"]
    try:
       probeDict=json.load(open("results/probeDict_"+_type+"_"+country+".json"))
    except:
        probeDict={}
    fulldomainList=cdn_Resources(country,"Google")
    FetchResults(_type,country,fulldomainList,"Google",probeDict)
    # time.sleep(60)
    fulldomainList=remaining["Fastly"]
    # fulldomainList=cdn_Resources(country,"Fastly")
    FetchResults(_type,country,fulldomainList,"Fastly",probeDict)
    # time.sleep(60)
    # fulldomainList=cdn_Resources(country,"Amazon CloudFront")
    fulldomainList=remaining["Amazon CloudFront"]
    FetchResults(_type,country,fulldomainList,"Amazon CloudFront",probeDict)

    # fulldomainList=cdn_Resources(country,"Akamai")
    fulldomainList=remaining["Akamai"]
    FetchResults(_type,country,fulldomainList,"Akamai",probeDict)



