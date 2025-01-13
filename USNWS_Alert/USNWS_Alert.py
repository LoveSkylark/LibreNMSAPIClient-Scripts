from Libs.LibreNMSAPIClient import LibreNMSAPIClient

'''
This script creates/updates a National Weather service ping device in Libre, and attaches Nagios Service Checks to it for every location in LibreNMS with lat/lng that is within the US.
It utilizes the NWS API https://www.weather.gov/documentation/services-web-api

Alert rules attached to device to capture alerts should be:
services.service_status equal 2
services.service_message contains pattern found

'''

Except_Location=[]  #Locations within US that NWS monitoring isn't wanted.
nws_monitor_name="National Weather Service (NWS) Monitor" #Name of NWS Monitor device
nws_match_params="-r \"\\\"event\\\"[:]\s(\\\".*Warning\\\")\" --invert-regex" #Parameters for NWS Monitoring Checks (Gets all Warnings: "-r \"\\\"event\\\"[:]\s(\\\".*Warning\\\")\" --invert-regex" )
nws_alert_prepend="NWS Warning for" #Text to prepend to NWS Monitoring checks

US_lat_lng_edges=[ #Coarse Lat/Lng of US (Where US NWS services)
    {'north':49,#lat<=#     #Contiguous continental US
     'south':24,#lat>=#
     'east':-66,#lng<=#
     'west':-125,#lng>=#
     },
    {'north':71,    #Alaska
     'south':51,
     'east':-141,
     'west':-168,
     },
    {'north':23,    #Hawaii
     'south':18,
     'east':-154,
     'west':-161,
     }
    ]

libreapi =  LibreNMSAPIClient()
#Find/Create NWS Monitor device to add checks to.
try:
    nws_monitor_id=libreapi.get_device('api.weather.gov')['device_id']
except:
    nws_monitor_id=libreapi.add_device({'hostname':'api.weather.gov',
                             'snmp_disable': True,
                             'display':nws_monitor_name,
                             'sysName':nws_monitor_name,
                             'force_add': True})['device_id']
Valid_Location={}
#Find Valid Locations
for loc in libreapi.list_locations():
    if loc['lat'] != None and loc['lng'] != None and loc['location'] not in Except_Location:
        for edge in US_lat_lng_edges:
            if loc['lat'] <= edge['north'] and loc['lat'] >= edge['south'] and loc['lng'] <= edge['east'] and loc['lng'] >= edge['west']   :
                Valid_Location[f"{nws_alert_prepend} {loc['location']}"]=loc
#Check if NWS monitor for locations already exist
for svc in libreapi.get_service_for_host(nws_monitor_id):
    for svc2 in svc:
        if svc2['service_desc'] in Valid_Location:
            del Valid_Location[svc2['service_desc']]
#Add any missing NWS
for loc_name, loc_data in Valid_Location.items():
    print("Creating:" + loc_name)
    libreapi.add_service_for_host({'type':'http','ip':'api.weather.gov',
                                   'desc': loc_name,
                                   'param': f" -u \"/alerts/active?point={loc_data['lat']},{loc_data['lng']}\" {nws_match_params} -S"},nws_monitor_id)

print("Done updating NWS Locations")


