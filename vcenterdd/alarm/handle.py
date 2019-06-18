
import logging
import os
import datetime
import hashlib
import argparse
import dns.resolver
from dns.resolver import NXDOMAIN
from vcenterdd.log.setup import addClassLogger

logger = logging.getLogger(__name__)


@addClassLogger
class VcenterAlarm(object):
    """
    This object is an object mapping of the alarm environment variables when a vCenter alarm is executing a script.
    This object is a dynamically created object in which it will read in the environment variables and
    dynamically create the attributes/properties of this object. This is due to the nature of what environment
    variables are presented from one alarm to the other. Each alarm may have varying data accompanying the alarm.
    VMWARE_ALARM_ID = alarm-7
    VMWARE_ALARM_DECLARINGSUMMARY = ([Yellow metric Is above 61%; Red metric Is above 85%])
    VMWARE_ALARM_ALARMVALUE = Current values for metric/state
    VMWARE_ALARM_TRIGGERINGSUMMARY = Metric Disk Space actually used = 78%
    VMWARE_ALARM_TARGET_ID = datastore-444
    VMWARE_ALARM_EVENTDESCRIPTION = Alarm 'Datastore usage on disk' on CL0990NTNXP002_CTR-RF2 changed from Gray to Yellow
    VMWARE_ALARM_TARGET_NAME = CL0990NTNXP002_CTR-RF2
    VMWARE_ALARM_NEWSTATUS = Yellow
    VMWARE_ALARM_NAME = alarm.DatastoreDiskUsageAlarm
    VMWARE_ALARM_OLDSTATUS = Gray
    """

    def __init__(self, env):
        self.env = env
        self.name = None
        self.datadog_format = {}
        self.alert_type = None
        self.alarm_key_hash = None
        self.date_time = datetime.datetime.now()
        self.__init_object()

    def __init_object(self):
        for k, v in os.environ.items():
            if k.startswith('VMWARE_ALARM'):
                if k == 'VMWARE_ALARM_NAME':
                    setattr(self, 'alarm_name', v)
                else:
                    setattr(self, k.lower().replace('vmware_alarm_', ''), v)
        self.name = self.eventdescription.replace(" changed from {} to {}".format(self.oldstatus, self.newstatus), '')
        _hash = hashlib.sha1("{},{},{}".format(self.name, self.target_name, self.target_id).encode())
        self.alarm_key_hash = _hash.hexdigest()
        self.name = "{} {} [EventID: {}]".format("[Triggered]", self.name, self.alarm_key_hash)

        if self.newstatus.lower() == 'yellow':
            self.alert_type = "warning"
        elif self.newstatus.lower() == "red":
            self.alert_type = "error"
        elif self.newstatus.lower() == "green":
            self.alert_type = "success"
        else:
            self.alert_type = "info"

    def format_datadog_event(self):
        """
        datadog event follows the following format per https://docs.datadoghq.com/api/?lang=bash#events:
            title [required]: The event title. Limited to 100 characters. Use msg_title with the Datadog Ruby library.
            text [required]: The body of the event. Limited to 4000 characters. The text supports markdown.
                             Use msg_text with the Datadog Ruby library
            date_happened [optional, default = now]: POSIX timestamp of the event. Must be sent as an integer
                                                     (i.e. no quotes). Limited to events no older than 1 year,
                                                     24 days (389 days)
            priority [optional, default = normal]: The priority of the event: normal or low.
            host [optional, default=None]: Host name to associate with the event. Any tags associated with
                                           the host are also applied to this event.
            tags [optional, default=None]: A list of tags to apply to the event.
            alert_type [optional, default = info]: If it’s an alert event, set its type between: error,
                                                   warning, info, and success.
            aggregation_key [optional, default=None]: An arbitrary string to use for aggregation. Limited to
                                                      100 characters. If you specify a key, all events using
                                                      that key are grouped together in the Event Stream.
            source_type_name [optional, default=None]: The type of event being posted. Options: nagios, hudson,
                                                       jenkins, my_apps, chef, puppet, git, bitbucket… Complete
                                                       list of source attribute values
            related_event_id [optional, default=None]: ID of the parent event. Must be sent as an
                                                       integer (i.e. no quotes).
            device_name [optional, default=None]: A list of device names to post the event with.
        :return: None
        """

        self.datadog_format.update({
            'title': self.name,
            'text': "{}\n{}\n{}".format(self.eventdescription, self.triggeringsummary, self.declaringsummary),
            'date_happened': self.date_time,
            'priority': 'normal',
            'host': self._get_fqdn(self.target_name),
            'tags': [self.env, "app:vsphere", "team:cig", "inf.vsphere.{}".format(self.alarm_name)],
            'alert_type': self.alert_type,
            'aggregation_key': self.alarm_key_hash,
            'source_type_name': 'Vsphere',
            'device_name': self.target_name
        })

    def _get_fqdn(self, name):
        fqdn = None
        try:
            dns_qry = dns.resolver.query(name)
            fqdn = dns_qry.canonical_name.__str__().strip('.')

        except NXDOMAIN as e:
            self.__log.warning(
                'Unable to locate a DNS record for {}.\nException: {} \n Args: {}'.format(name, e, e.args))

        return fqdn
