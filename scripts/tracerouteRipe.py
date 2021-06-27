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
from bson import ObjectId
from datetime import (
    datetime, 
    timedelta
)
from ripe.atlas.cousteau import (
    Traceroute,
    AtlasSource,
    AtlasCreateRequest
)
from os.path import isfile, join
from copy import deepcopy



def runMeasurements(_type,country,ips,runs):
   
    try:
        measurement_ids=json.load(open("results/traceRouteRipeMsmIds_"+_type+"_"+country+".json"))
    except:
        measurement_ids=[]
    for run in range(runs):     
        print ("Doing run: ",run)
        if run!=0:
            time.sleep(1*60)
        for target_ip in ips:
            traceroute=Traceroute(
                af = 4,  # IPv4
                target = target_ip,
                description = "Traceroute Target %s %s" % (target_ip, str(datetime.now())),
                max_hops = 30,
                timeout = 4000,
                paris = 16,  # use Paris Traceroute to avoid load balancing
                protocol = "ICMP",
                is_public = False,
                resolve_on_probe = True  # use probe's locally assigned DNS
            )

            source = AtlasSource(
                type="country",
                value="US",
                requested=1
            )

            ATLAS_API_KEY = "b7fb25c3-a5fc-4785-8f35-6830a6fdb6a4"

            atlas_request = AtlasCreateRequest(
                start_time=datetime.utcnow(),
                key=ATLAS_API_KEY,
                measurements=[traceroute],
                sources=[source],
                is_oneoff=True
            )

            (is_success, response) = atlas_request.create()
            if is_success:
                _id=response["measurements"]
                print("SUCCESS: measurement created: %s" % response["measurements"],target_ip)
            else:
                print ("failed to create measurement: %s" % response,target_ip)
                raise Exception("failed to create measurement: %s" % response)
            print (str(_id[0]))
            measurement_ids.append((target_ip,str(_id[0])))

            with open("results/traceRouteRipeMsmIds_"+_type+"_"+country+".json", 'w') as fp:
                json.dump(measurement_ids, fp)

def FetchResults(_type,country,cdn):
    try:
        measurement_ids=json.load(open("results/traceRouteRipeMsmIds_"+_type+"_"+country+".json"))
    except:
        return
    try: 
        dict=json.load(open("results/tracerouteRipeResult_"+_type+"_"+country+".json"))
    except:
        dict={} 

    if cdn not in dict:
        dict[cdn]={}

    count=0
    for target_ip,id in measurement_ids:
        if target_ip not in dict[cdn]:
            dict[cdn][target_ip]=[]
        if count%20==0:
            time.sleep(0.2)
        count+=1
        
        kwargs = {
        "msm_id": id
        }
        print("Fetching %s" % id," \% done",100*count/len(measurement_ids))
        is_success, results = AtlasResultsRequest(**kwargs).create()
        operations=[]
        if is_success:
            # print ("results",results)
            for r in results:
                result = deepcopy(r)
                operations.append(result)
            dict[cdn][target_ip].append(operations)   
        else:
            print ("Fetching wasn't successful: ",id, str(e))
            continue
        
        
    with open("results/tracerouteRipeResult_"+_type+"_"+country+".json", 'w') as fp:
        json.dump(dict, fp)

def main(_type,cdns,Prefixes,country):
    for cdn in cdns:
        while 1:
            try:
                measurement_ids=json.load(open("results/traceRouteRipeMsmIds_"+_type+"_"+country+".json"))
            except Exception as e:
                print (str(e))
                measurement_ids={}
            dict={}
            for _ip,id in measurement_ids:
                if str(_ip) not in dict:
                    dict[str(_ip)]=0
                dict[str(_ip)]+=1
            if Prefixes[cdn][0] in dict:    
                runs=5-dict[Prefixes[cdn][0]]
            else:
                runs=5
            if runs<=0:
                print ("Done for the set: ",cdn,Prefixes[cdn])
                break
            print ("Starting to run for: ",runs,cdn)
            try:
                runMeasurements(_type,country,Prefixes[cdn],runs)
            except:
                time.sleep(300)
            FetchResults(_type,country,cdn)
 
if __name__ == "__main__":
    # runMeasurements(_type,"US",domainList,5)
    # country="AR" #set country for resolvers
    # cdns=["Google","Amazon CloudFront","Fastly","Akamai"]
    cdns=["Google","Amazon CloudFront"]
    localCommonPrefixes=json.load(open("results/localCommonPrefixes_AR.json"))
    distantCommonPrefixes_IN=json.load(open("results/distantCommonPrefixes_IN.json"))
    # country="US"
    #do Google and Amazon
    _type="local" 
    main(_type,cdns,localCommonPrefixes,"US")
    # _type="distant" 
    # main(_type,cdns,distantCommonPrefixes_IN,"IN")

        

    