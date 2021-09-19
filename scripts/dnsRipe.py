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
import os

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

def runMeasurements(_type,region,domainList,runs):
    # dnsServers=["182.19.95.34","203.201.60.12","223.31.121.171","182.71.213.139","111.93.163.56"] #resolvers in India
    # dnsServers=["190.151.144.21","200.55.54.234","200.110.130.194","157.92.190.15","179.60.235.209"] #resolvers in AR

    # probeId: 53868 (Wisconsin,US)
    # Same Metro: use ripe local resolver
    # target="149.112.112.112" #(same metro)
    # target="209.250.128.6" #(same region)
    # target="190.151.144.21" #(neighboring_region)
    # target="182.19.95.34" #(non-neighboring_region)
    # target="8.8.8.8" #(remote_google)
    target="local"

    tryTimes=0
    try:
        measurement_ids=json.load(open("results/sigcommRes/"+region+"/dnsRipeMsmIds_"+_type+".json"))
    except:
        measurement_ids=[]
    for run in range(runs):
        if run!=0 and run%5==0:
            time.sleep(1*60)
        print ("Doing run: ",run)
        for domain in domainList:    
            dns = Dns(
                af=4,
                # target=target,
                description="Dns Resolution of CDNized Resources",
                query_class="IN",
                query_type="A",
                query_argument=domain,
                set_rd_bit= True, 
                type= "dns", 
                include_qbuf=True,
                include_Abuf=True,
                use_probe_resolver= True
            )

            source = AtlasSource(
                type="probes",
                value=53014,
                # type="country",
                # value="DE",
                requested=1
                # from_probes=[1002694],
                # tags={"include":["system-ipv4-works"]}
            )

            ATLAS_API_KEY = "b7fb25c3-a5fc-4785-8f35-6830a6fdb6a4"

            atlas_request = AtlasCreateRequest(
                start_time=datetime.utcnow(),
                # from_probes=[1002694],
                key=ATLAS_API_KEY,
                measurements=[dns],
                sources=[source],
                is_oneoff=True
            )
            (is_success, response) = atlas_request.create()
            if is_success:
                _id=response["measurements"]
                print("SUCCESS: measurement created: %s" % response["measurements"],domain,target)
            else:
                print ("failed to create measurement: %s" % response,domain,target)
                raise Exception("failed to create measurement: %s" % response)

            print (str(_id[0]))

            measurement_ids.append((domain,str(_id[0])))

            if not os.path.exists("results/sigcommRes/"+region):
                os.mkdir("results/sigcommRes/"+region)
            with open("results/sigcommRes/"+region+"/dnsRipeMsmIds_"+_type+".json", 'w') as fp:
                json.dump(measurement_ids, fp)


def FetchResults(_type,region,domainList,cdn):
    try:
        measurement_ids=json.load(open("results/sigcommRes/"+region+"/dnsRipeMsmIds_"+_type+".json"))
    except:
        return
    try: 
        _dict=json.load(open("results/sigcommRes/"+region+"/dnsRipeResultPerQuery_"+_type+".json"))
    except Exception as e:
        print ("ripeResult File does not exist",str(e))
        _dict={}  
        # _ripedict[cdn]={}
    if cdn not in _dict:
        _dict[cdn]={}
    count=0
    for domain,id in measurement_ids:
        # if count%20==0:
        #     time.sleep(0.2)
        # count+=1
        if domain not in domainList:
            continue
        kwargs = {
        "msm_id": id
        }
        print(domain,"Fetching %s" % id," \% done",100*count/len(measurement_ids))
        is_success, results = AtlasResultsRequest(**kwargs).create()
        # print (results)
        if is_success:
            try:
                my_result = DnsResult(results[0])
                print ("print Result: ",str(my_result).split("Probe #")[1])
                probeId=str(my_result).split("Probe #")[1]
                print (domain,id,probeId)
                # continue
            except Exception as e:
                print ("Fetching wasn't successful: ",domain,id, str(e))
                continue
        else:
            continue
        try:
            dnsAnswer=my_result.responses[0].abuf.answers
        except Exception as e:
            print ("Couldn't decode the answer: ",domain,id, str(e))
            continue
        if domain not in _dict[cdn]:
            _dict[cdn][domain]={}
        if id not in _dict[cdn][domain]:
            _dict[cdn][domain][id]=[]
        # else:
        #     continue   

        for result in dnsAnswer:
            try:
                ip_addr=result.address
                _dict[cdn][domain][id].append(ip_addr)
                # if ip_addr not in _dict[domain]:
                #     _dict[domain][ip_addr]=0

                # _dict[domain][ip_addr]+=1

            except Exception as e:
                # print (domain,id,result, str(e))
                print ("Error in fetching ip from ans: ",str(e))
                continue
    with open("results/sigcommRes/"+region+"/dnsRipeResultPerQuery_"+_type+".json", 'w') as fp:
        json.dump(_dict, fp)
        

#local done 
if __name__ == "__main__":
    # runMeasurements(_type,"US",domainList,5)
    region="Western Europe_SE_IN" #set country for resolvers
    if not os.path.exists("results/sigcommRes/"+region):
        os.mkdir("results/sigcommRes/"+region)
    # types=["local","remote_google","remote_metro","remote_same_region","remote_neighboring_region","remote_non-neighboring_region"]
    country=""
    _type="local"+country #change probe resolver, value of target and number of resolvers too
    # cdn="EdgeCast"
    cnameDomainMap=json.load(open("data/CDNMaps/"+region+"/cnameDomainMapUpdated.json"))
    file=json.load(open("data/CDNMaps/"+region+"/cnameCDNMap.json"))
    # overlappingregion="North America_AR_IN"
    # resources=json.load(open("results/sigcommRes/alexaResourcesDomains"+overlappingregion+".json"))
    resources=json.load(open("results/sigcommRes/"+region+"/alexaResourcesDomains"+region+".json"))
    cdns=["EdgeCast","Google","Fastly","Akamai","Amazon Cloudfront"]

    for cdn in cdns:
        fulldomainList=[]
        for cname in file[cdn]:
            for key in cnameDomainMap:
                if cname in cnameDomainMap[key]:
                    domain=key
                    break
            if domain in resources:
                fulldomainList.append(cname)
        print ("Len of fulldomainList: ",len(fulldomainList),len(file[cdn]))

        ##############################################(test on 3 cnames)
        # domainList=fulldomainList[:3]
        # runMeasurements(_type,region,domainList,1)
        # time.sleep(120)
        # FetchResults(_type,region,domainList,cdn)
        # break
        ###############################################
        
        for x in range(0,len(fulldomainList),3):
            start=x
            end=start+3
            print (start,end)
            domainList=fulldomainList[start:end]
            print (domainList)
            while 1: 
                try:
                    measurement_ids=json.load(open("results/sigcommRes/"+region+"/dnsRipeMsmIds_"+_type+".json"))
                except Exception as e:
                    print (str(e))
                    measurement_ids={}
                dict={}
                breakingCond=0
                for domain,id in measurement_ids:
                    if domain not in dict:
                        dict[domain]=0
                    dict[domain]+=1

                if domainList[0] in dict:    
                    runs=5-dict[domainList[0]]
                else:
                    runs=5
                if runs<=0:
                    print ("Done for the set: ",start,end)
                    break
                print ("Starting to run for: ",runs," domainList indexes",start,end)
                try:
                    runMeasurements(_type,region,domainList,runs)
                except Exception as e:
                    print ("Error in running measurements: ",str(e))
                    time.sleep(300)
                FetchResults(_type,region,domainList,cdn)
        FetchResults(_type,region,fulldomainList,cdn)

    

# US Probe=53868
# AR Probe=15780
# IN Probe=50302
# DE Probe=53014

# FR Probe=
# SE Probe=


