# Copyright 2014 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg

from nova import db
from nova import exception
from nova.tests.functional.api_sample_tests import test_servers
from nova.tests.unit.objects import test_network
from nova.tests.unit import utils as test_utils

CONF = cfg.CONF
CONF.import_opt('osapi_compute_extension',
                'nova.api.openstack.compute.legacy_v2.extensions')


class FixedIpTest(test_servers.ServersSampleBase):
    extension_name = "os-fixed-ips"

    request_api_version = None

    def _get_flags(self):
        f = super(FixedIpTest, self)._get_flags()
        f['osapi_compute_extension'] = CONF.osapi_compute_extension[:]
        f['osapi_compute_extension'].append(
            'nova.api.openstack.compute.contrib.fixed_ips.Fixed_ips')
        return f

    def setUp(self):
        super(FixedIpTest, self).setUp()

        instance = dict(test_utils.get_test_instance(),
                        hostname='openstack', host='host')
        fake_fixed_ips = [{'id': 1,
                   'address': '192.168.1.1',
                   'network_id': 1,
                   'virtual_interface_id': 1,
                   'instance_uuid': '1',
                   'allocated': False,
                   'leased': False,
                   'reserved': False,
                   'created_at': None,
                   'deleted_at': None,
                   'updated_at': None,
                   'deleted': None,
                   'instance': instance,
                   'network': test_network.fake_network,
                   'host': None},
                  {'id': 2,
                   'address': '192.168.1.2',
                   'network_id': 1,
                   'virtual_interface_id': 2,
                   'instance_uuid': '2',
                   'allocated': False,
                   'leased': False,
                   'reserved': False,
                   'created_at': None,
                   'deleted_at': None,
                   'updated_at': None,
                   'deleted': None,
                   'instance': instance,
                   'network': test_network.fake_network,
                   'host': None},
                  ]

        def fake_fixed_ip_get_by_address(context, address,
                                         columns_to_join=None):
            for fixed_ip in fake_fixed_ips:
                if fixed_ip['address'] == address:
                    return fixed_ip
            raise exception.FixedIpNotFoundForAddress(address=address)

        def fake_fixed_ip_update(context, address, values):
            fixed_ip = fake_fixed_ip_get_by_address(context, address)
            if fixed_ip is None:
                raise exception.FixedIpNotFoundForAddress(address=address)
            else:
                for key in values:
                    fixed_ip[key] = values[key]

        self.stubs.Set(db, "fixed_ip_get_by_address",
                       fake_fixed_ip_get_by_address)
        self.stubs.Set(db, "fixed_ip_update", fake_fixed_ip_update)

    def test_fixed_ip_reserve(self):
        # Reserve a Fixed IP.
        response = self._do_post('os-fixed-ips/192.168.1.1/action',
                                 'fixedip-post-req', {},
                                 api_version=self.request_api_version)
        self.assertEqual(202, response.status_code)
        self.assertEqual("", response.content)

    def _test_get_fixed_ip(self, **kwargs):
        # Return data about the given fixed ip.
        response = self._do_get('os-fixed-ips/192.168.1.1',
                                api_version=self.request_api_version)
        project = {'cidr': '192.168.1.0/24',
                   'hostname': 'openstack',
                   'host': 'host',
                   'address': '192.168.1.1'}
        project.update(**kwargs)
        self._verify_response('fixedips-get-resp', project, response, 200)

    def test_get_fixed_ip(self):
        self._test_get_fixed_ip()


class FixedIpV24Test(FixedIpTest):
    request_api_version = '2.4'
    # NOTE(gmann): microversion tests do not need to run for v2 API
    # so defining scenarios only for v2.4 which will run the original tests
    # by appending '(v2_4)' in test_id.
    scenarios = [('v2_4', {})]

    def test_get_fixed_ip(self):
        self._test_get_fixed_ip(reserved=False)
