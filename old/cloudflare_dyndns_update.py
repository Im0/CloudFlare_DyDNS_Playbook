#!/usr/bin/env python
import requests
import json
import sys
import syslog
import getopt

# ./file domain_name  hostname
# Description:  Update cloudflare CDN DNS entries with the external
#               IP address numerous sites report back.  (Dynamic DNS)
#

headers = {
    'Content-Type':  'application/json',
    'X-Auth-Key':    'API_AUTH_KEY_GOES_HERE',
    'X-Auth-Email':  'CF_ACCOUNT_EMAIL_GOES_HERE'
}
DEBUG = False

def checkZones(zoneName):
    '''Check on CloudFlare to see if the zone we are trying to update actually
    exists.

       args(zone name):
           The zone name we want to check exists.
    '''
    if DEBUG: print("zoneName passsed into checkZones function: " +zoneName+'.')
    urlGetZones = 'https://api.cloudflare.com/client/v4/zones'

    r = requests.get(urlGetZones, headers=headers)
    content = r.json()
    if DEBUG: print("##### checkZones debugging ####")
    if DEBUG: print json.dumps(content, indent=4, sort_keys=True)

    if DEBUG: print 'checkZones: searching for the zone',zoneName
    for zone in content['result']:
        if DEBUG: print 'checkZones: for zone in content comparing ', zoneName, ' with ', zone['name']
        if zoneName == zone['name']:
            syslog.syslog("checkZones - found the zone on CF: " + zoneName + '.')
            if DEBUG: print ("checkZones - found the zone on CF: " + zoneName + '.')
            return True;

    syslog.syslog("checkZones - cannot find the zone on CF: " + zoneName + '.')
    if DEBUG: ("checkZones - cannot find the zone on CF: " + zoneName + '.')
    sys.exit(1)



def getZoneDetails(zoneName):
    urlGetZoneInfo = 'https://api.cloudflare.com/client/v4/zones?name=' + zoneName 

    r = requests.get(urlGetZoneInfo, headers=headers)
    if DEBUG: print("getZoneDetails(): request resonse code: ",  r.status_code)
    content = r.json()

    if DEBUG: print("getZoneDetails: pretty printing r.json data...")
    if DEBUG: print json.dumps(content, indent=4, sort_keys=True)
    if DEBUG: print content['result'][0]['name']
    id = content['result'][0]['id']
    #zoneID = content['result'][0]['zone_id']
    #for nameserver in nses:
        #print 'Name server: ', nameserver
    #nses = content['result'][0]['name_servers']

    if DEBUG: print("id zoneName: " + id + " " + zoneName)
    syslog.syslog("getZoneDetails id zoneName: " + id + " " + zoneName)
    return ( {
            'id': id,
            'zoneName': zoneName
            }
            )

def getDnsRecords( id, FQDN ):   
    if DEBUG: print("getDnsRecords id FQDN = " + id + " " + FQDN)
    url_get_dns = "https://api.cloudflare.com/client/v4/zones/" + detail['id'] + "/dns_records"

    r = requests.get(url_get_dns, headers=headers)
    content = r.json()
    if DEBUG: print json.dumps(content, indent=4, sort_keys=True)
    syslog.syslog("getDnsRecords - getting records for " + FQDN)
    
    for result in content['result']:
        if DEBUG: print("result.name ==" + result['name'])
        if result['name'] == FQDN and result['type'] == 'A':
            if DEBUG: print("Existing IP for " + FQDN + " == " + result['content'])
            return { 'zone_id': result['zone_id'],
                     'record_id': result['id'],
                     'existing_ip': result['content']
                    }

def setDnsRecords( id, FQDN, domain, recordID, ip):
    if DEBUG: print("id FQDN domain zoneID ip" + id + FQDN + domain + recordID + ip)
    url_set_dns = "https://api.cloudflare.com/client/v4/zones/" + id + "/dns_records/" + recordID + "/"
    data = { "id": recordID,
         "type": "A",
         "name": FQDN,
         "content": ip,
         "zone_id": id,
         "zone_name": domain
        }
    r = requests.put(url_set_dns, headers=headers, data=json.dumps(data))
    content3 = r.json()
    if DEBUG: print json.dumps(content3, indent=4, sort_keys=True)
    if content3['success'] == True:
        if DEBUG: print("Successfully update CDN with " + FQDN + "/" + ip)
        syslog.syslog("Successfully update CDN with " + FQDN + "/" + ip)
    else:
        if DEBUG: print("Failed to update CDN with " + FQDN + "/" + ip)
        syslog.syslog("Failed to update CDN with " + FQDN + "/" + ip)

def getIP():
    ip = requests.get('http://api.ipify.org').text
    #print 'My public IP address is:', ip
    r = requests.get('http://ipinfo.io/json')
    content4 = r.json()
    #print 'My public IP address is:', content4['ip']

    if ip == content4['ip']:
        if DEBUG: print("The IP address (" + ip + ") matches on both external GeoIP sources")
        syslog.syslog("My external IP address reported is " + ip)
        return ip
    else:
        if DEBUG: print ("The IP addresses reported did not match. " + ip + " != " + content['4'])
        syslog.syslog("The IP addresses reported did not match. " + ip + " != " + content['4'])
        return False

def checkLast(myip):
    '''Check what the last IP address was.  If myip from geolocation sites
    matches the stored IP address... we can exist gracefully and not talk to
    CloudFlare.

    sys.exit(1) if; 
        The IPs match.  Assuming no update of CDN is required.
    Return False if:
        There was an error, or, the IP addresses didn't match.
    '''
    if DEBUG: print 'checkLast(): file_name is: ', file_name
    try:
        f = open(file_name, 'r+')
    except IOError:
        syslog.syslog("Could not open ipfile")
        if DEBUG: print("Could not open ipfile ")
        return False
    else:
        if DEBUG: print("Reading from ipfile ")
        data = f.read()
        f.close

    if DEBUG: print("The local ip file says: " + data + " the Geo IP is " + myip)
    if data == myip:
        syslog.syslog("The stored IP matched the GEO IP. Assuming no update required, exiting.")
        if DEBUG: print ("Exiting as GEO and stored IP match. Assuming no update required.")
        sys.exit(1)
        return True
    else:
        syslog.syslog("The stored IP (" + data + ") did not match the GEO IP (" + myip + "). Updating file.")
        if DEBUG: print ("The stored IP (" + data + ") did not match the GEO IP (" + myip + "). Updating file.")
        f = open(file_name, 'w')
        f.write(myip)
        f.truncate
        f.close
        return False

def updateLast(myip):
    try:
        f = open(file_name, 'w')
    except IOError:
        syslog.syslog("Could not open ipfile")
        if DEBUG: print 'updateLast: could not open ipfile ', file_name
        return False
    else:
        f.write(myip)
        f.close
        syslog.syslog("Updated the local cached IP")
        if DEBUG: print 'updateLast: updated local cache IP file', file_name
        return True
        


############################
# main
############################

options, remainder = getopt.getopt(sys.argv[1:], 'd:h:f:', ['domain=', 
                                                         'hostname=',
                                                         'file=',
                                                        ])

for opt, arg in options:
    if opt in ('-d', '--domain'):
        domain_name = arg
    elif opt in ('-h', '--hostname'):
        host_name = arg
    elif opt in ('-f', '--file', '--filename'):
        file_name = arg

if DEBUG: print 'ARGV: ', sys.argv[1:]
if DEBUG: print 'Option Domain: ', domain_name
if DEBUG: print 'Option Hostname: ', host_name
if DEBUG: print 'Option Filename: ', file_name

syslog.syslog('Starting processing ' + host_name + ' ' + domain_name)
if DEBUG: print("##############")
myip = getIP()

checkLast(myip)

checkZones(domain_name)

if myip:
    updateLast(myip)
    if DEBUG: print("Getting zone details from CF for " + domain_name)
    detail = getZoneDetails(domain_name)
    FQDN = host_name  + "." + domain_name
    detail2 = getDnsRecords(detail['id'], FQDN)
    if detail2:
        if DEBUG: print("my ip: " + myip)
        if DEBUG: print("id: " + detail['id'])
        if DEBUG: print("zone id: " + detail2['zone_id'])
        if DEBUG: print("record id: " + detail2['record_id'])
        if DEBUG: print("zone: " + domain_name)
        if DEBUG: print("hostname: " + host_name)
        if detail2['existing_ip'] == myip:
            syslog.syslog("External IP matches CDN IP.  Not updating.")
        else:
            setDnsRecords( detail['id'], host_name + "." + domain_name, domain_name, detail2['record_id'], myip)
    else:
        if DEBUG: print("Not updating.  Host/Zone does not exist: " + host_name + "." + domain_name)
        syslog.syslog("Host/zone does not exist: " + host_name + "." + domain_name)
else:
    if DEBUG: print("Not updating")

if DEBUG: print("##############")
