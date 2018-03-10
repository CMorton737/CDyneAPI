import httplib, urllib
from xml.dom import minidom
from datetime import datetime

class CDyneKeysException(Exception):
    pass

class CDyneResponseException(Exception):
    pass

class CDyne(object):

    PNAPI_HOST = "ws.cdyne.com"
    PNAPI_PATH = "/NotifyWS/PhoneNotify.asmx"
    SNAPI_HOST = "sms2.cdyne.com"
    SNAPI_PATH = "/sms.svc"
    
    API_LICENSE = ""
    API_METHODS = {
        "get_queue_id_status": {
            "service": "phone",
            "method": "GetQueueIDStatus",
            "type": "GET",
            "keys":["QueueID"]
        },
        "simple_sms_send": {
            "service": "sms",
            "method": "SimpleSMSsend",
            "type": "GET",
            "keys": ['PhoneNumber', 'Message']
        },
        "simple_sms_send_with_postback": {
            "service": "sms",
            "method": "SimpleSMSsendWithPostback",
            "type": "GET",
            "keys": ['PhoneNumber', 'Message', 'StatusPostBackURL']
        },
        "cancel_message": {
            "service": "sms",
            "method": "CancelMessage",
            "type": "GET",
            "keys": ['MessageID']
        },
        "get_message_status": {
            "service": "sms",
            "method": "GetMessageStatus",
            "type": "GET",
            "keys": ['MessageID']
        },
        "get_message_status_by_reference_id": {
            "service": "sms",
            "method": "GetMessageStatusByReferenceID",
            "type": "GET",
            "keys": ['ReferenceID']
        },
        "get_unread_incoming_messages": {
            "service": "sms",
            "method": "GetUnreadIncomingMessages",
            "type": "GET",
            "keys": []
        }
    }
    CONNECTION_TIMEOUT = 10
    RESPONSE_STATUS_OK = 200

    def __init__(self, license):
        self.API_LICENSE = license

    def __validate_keys(self, params, keys):
        if not sorted(keys) == sorted(params.keys()):
            raise CDyneKeysException("One or more of required parameters is missing: %s" % keys)

    def __get_typed_node_data(self, node):
        boolean_fields = ['Cancelled', 'Queued', 'Sent']
        datetime_fields = ['SentDateTime']

        name = node.parentNode.nodeName
        data = node.data

        if name in boolean_fields:
            return True if data == u"true" else False

        if name in datetime_fields:
            return datetime.strptime(data, "%Y-%m-%dT%H:%M:%S")

        return data

    def __xml_to_dict(self, node):
        response = {}
        if node.hasChildNodes():
            for child in node.childNodes:
                if isinstance(child, minidom.Element):
                    if (len(child.childNodes) == 1) and (isinstance(child.childNodes[0], minidom.Text)):
                        response.update({
                            child.nodeName: self.__get_typed_node_data(child.childNodes[0])
                        })
                    else:
                        response.update({
                            child.nodeName: self.__xml_to_dict(child)
                        })

        return response

    def __send_request(self, method, service, request_type, params):
        params.update({
            'LicenseKey': self.API_LICENSE
        })
        params = urllib.urlencode(params)
        
        if service == 'phone':
            api_host, api_path = self.PNAPI_HOST, self.PNAPI_PATH
        elif service == 'sms':
            api_host, api_path = self.SNAPI_HOST, self.SNAPI_PATH
            
        connection = httplib.HTTPConnection(api_host, timeout=self.CONNECTION_TIMEOUT)
        request_path = "%s/%s" % (api_path, method)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent':'Mozilla/4.0'
        }

        if request_type == "POST":
            connection.request(request_type, request_path, params, headers)

        else:
            connection.request(request_type, "%s?%s" % (request_path, params), "", headers)

        response = connection.getresponse()

        if response.status == self.RESPONSE_STATUS_OK:
            return self.__xml_to_dict(minidom.parse(response))

        raise CDyneResponseException("Invalid server response: %s" % response.read())

    def __getattr__(self, name):
        if self.API_METHODS.has_key(name):
            setattr(self, "CALL_METHOD", name)
            return self.call

        raise AttributeError()

    def call(self, params):

        method = self.API_METHODS.get(self.CALL_METHOD).get("method")
        service = self.API_METHODS.get(self.CALL_METHOD).get("service")
        request_type = self.API_METHODS.get(self.CALL_METHOD).get("type")
        keys = self.API_METHODS.get(self.CALL_METHOD).get("keys")
        delattr(self, "CALL_METHOD")

        self.__validate_keys(params, keys)
        return self.__send_request(method, service, request_type, params)


if __name__ == "__main__":
    client = CDyne("your license id here")
    print client.get_queue_id_status({
        "QueueID": 1234567890
})