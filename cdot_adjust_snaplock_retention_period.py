#!/usr/bin/python

#
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: cdot_set_snaplock_retention_period
short_description: Set snaplock retention period on volumes that reside on CDOT ONTAP
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Jeroen Kleijer (jeroen.kleijer_2@nxp.com)
description:
- Create or destroy volumes on NetApp cDOT
options:
  volume:
    description:
    - The name of the volume to manage.
    required: true
  vserver:
    description:
    - Name of the vserver to use.
    required: true
    default: None
  retention_period_days:
    description:
    - The retention period to place on the volume (counted in days)
    required: false
    default: 21days
'''

EXAMPLES = """
    - name: Adjust the snaplock retention period of the volume
      cdot_set_snaplock_retention_period
        volume: ansibleVolume
        vserver: ansibleVserver
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp.password }}"
"""

RETURN = """
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_execution
import ansible.module_utils.netapp as netapp_utils
import time

HAS_NETAPP_LTB = netapp_utils.has_netapp_lib()


class NetAppCDOTAdjustSanpLockRetentionPeriod(object):

    def __init__(self):

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            volume=dict(required=True, type='str', aliases=['name']),
            vserver=dict(required=True, type='str', default=None),
            retention_period_days=dict(required=False, type='int', default='21'),

        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=False
        )

        p = self.module.params
        self.params = p

        # set up state variables
        self.volume = p['volume']
        self.vserver = p['vserver']

        # optional state variables
        self.retention_period_days = int( p['retention_period_days'] )

        self.state_vars_opt = []
        #self.state_vars_opt.extend([self.volume_comment])

        self.state_vars_opt.extend([self.retention_period_days])

        if HAS_NETAPP_LTB is False:
            self.module.fail_json(msg="the puthon NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module, vserver=self.vserver)

    def cleanse_name(self, name):
        cleansed_name = name.split('}')[1].replace('-','_')
        return cleansed_name

    def set_retention_period(self):
        api_call = {}

        if self.retention_period_days > 60:
            self.module.fail_json( msg='Trying to set retention period on volume %s but retention_period_days (%s) is too large (max=60)' % (self.volume, self.retention_period_days ) )
        else:
            api_call = {}
            api_call.update( {'volume': self.volume,
                            'minimum-retention-period': str( self.retention_period_days ) + "days",
                            'default-retention-period': str( self.retention_period_days ) + "days",
                            'maximum-retention-period': str( self.retention_period_days ) + "days" })
            volume_set_snaplock_attrs = netapp_utils.zapi.NaElement.create_node_with_children(
                'volume-set-snaplock-attrs', **api_call )

            try:
                self.server.invoke_successfully( volume_set_snaplock_attrs,
                                                enable_tunneling=True )
                changed = True
            except netapp_utils.zapi.NaApiError:
                err=get_exception()
                self.module.fail_json(msg='Error setting snaplock retention periods on volume %s' %self.volume, exception=str( err ))

  def apply(self):
      changed = False

      self.set_retention_period()
      self.moudle.exit_json_json(changed=changed)


def main():
    v = NetAppCDOTAdjustSnapLockRetentionPeriod()
    v.apply()

if __name__ == '__main__':
    main()
