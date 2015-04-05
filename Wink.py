from urllib2 import Request, urlopen
#import simplejson as json
import json

api_server = "https://winkapi.quirky.com"
api_server = "https://private-0d714-wink.apiary-mock.com"

values = json.dumps({
    "client_id": "9575057b69283d441c17f3618d15d93d",
    "client_secret": "4aaf8ea1c1064166e3df8bae3e109598",
    "username": "joel@joelroberts.net",
    "password": "p@ssw0rd",
    "grant_type": "password"
})
headers = {"Content-Type": "application/json"}
request = Request("{0}/oauth2/token".format(api_server), data=values, headers=headers)
response_body = urlopen(request).read()
oauth2 = json.loads(response_body)
print json.dumps(oauth2, sort_keys=True, indent=4, separators=(',', ': '))

# headers = {"Authorization": "Bearer {0}".format(oauth2["data"]["access_token"])}
# request = Request("{0}/users/me/light_bulbs".format(api_server), headers=headers)
# response_body = urlopen(request).read()
# light_bulbs = json.loads(response_body)
# print json.dumps(light_bulbs, sort_keys=True, indent=4, separators=(',', ': '))

#
# headers = {"Authorization": "Bearer {0}".format(oauth2["data"]["access_token"])}
# request = Request("{0}/users/me/wink_devices".format(api_server), headers=headers)
# response_body = urlopen(request).read()
# wink_devices = json.loads(response_body)
# print json.dumps(wink_devices, sort_keys=True, indent=4, separators=(',', ': '))

# new_group = {
#     "name": "Bedroom",
#     "order": 3,
#     "members": [
#         {
#             "object_id": "467288",
#             "object_type": "light_bulb"
#         },
#         {
#             "object_id": "467290",
#             "object_type": "light_bulb"
#         },
#         {
#             "object_id": "467302",
#             "object_type": "light_bulb"
#         }
#     ]
# }
#
# headers = {"Authorization": "Bearer {0}".format(oauth2["data"]["access_token"])}
# request = Request("{0}/groups".format(api_server), data=json.dumps(new_group), headers=headers)
# response_body = urlopen(request).read()
# new_group_results = json.loads(response_body)
# print json.dumps(new_group_results, sort_keys=True, indent=4, separators=(',', ': '))

#
# new_group_results
#
# {
#     "data": {
#         "automation_mode": null,
#         "group_id": "2895682",
#         "icon_id": null,
#         "members": [],
#         "multicast_ready": false,
#         "name": "Group",
#         "order": 0,
#         "reading_aggregation": {}
#     },
#     "errors": [],
#     "pagination": {}
# }

# false = "false"
# activate_group = {
#     "desired_state": {
#         "powered":false
#     }
# }

# activate_group = '{"desired_state": {"powered":true}}'
#
# headers = {"Authorization": "Bearer {0}".format(oauth2["data"]["access_token"])}
# request = Request("{0}/groups/2895682/activate".format(api_server), data=activate_group, headers=headers)
# response_body = urlopen(request).read()
# print response_body
# activate_group_results = json.loads(response_body)
# print json.dumps(activate_group_results, sort_keys=True, indent=4, separators=(',', ': '))

#activate_bulb = '{"desired_state": {"powered":true,"brightness":100}}'


#
activate_bulb = json.dumps({
    "name":"Living Room Lamp",
    "desired_state": {
        "powered":bool(),
        "brightness":0
    }
})

activate_bulb = json.dumps({
    "name":"My Device"
}, sort_keys=True, indent=4, separators=(',', ': '))

print activate_bulb
headers = {"Content-Type": "application/json", "Authorization": "Bearer {0}".format(oauth2["data"]["access_token"])}
request = Request("{0}/light_bulbs/466989".format(api_server), data=activate_bulb, headers=headers)
request.get_method = lambda: 'PUT'
response_body = urlopen(request).read()
activate_group_results = json.loads(response_body)
print json.dumps(activate_group_results, sort_keys=True, indent=4, separators=(',', ': '))


# Get list of all Groups
# headers = {"Authorization": "Bearer {0}".format(oauth2["data"]["access_token"])}
# request = Request("{0}/users/me/groups".format(api_server), headers=headers)
# response_body = urlopen(request).read()
# activate_group_results = json.loads(response_body)
# print json.dumps(activate_group_results, sort_keys=True, indent=4, separators=(',', ': '))

