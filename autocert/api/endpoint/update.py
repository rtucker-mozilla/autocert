#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
autocert.update
'''

from pprint import pformat
from attrdict import AttrDict

from endpoint.base import EndpointBase
from exceptions import AutocertError
from utils.yaml import yaml_format
from app import app
import blacklist

from bundle import Bundle

class MissingUpdateArgumentsError(AutocertError):
    def __init__(self, args):
        message = f'missing arguments to update; args = {args}'
        super(MissingUpdateArgumentsError, self).__init__(message)

class DeployError(AutocertError):
    def __init__(self):
        message = 'deploy error; deployment didnt happen'
        super(DeployError, self).__init__(message)

class UpdateEndpoint(EndpointBase):
    def __init__(self, cfg, args):
        super(UpdateEndpoint, self).__init__(cfg, args)

    def execute(self, **kwargs):
        status = 201
        bundle_name_pns = [self.sanitize(bundle_name_pn) for bundle_name_pn in self.args.bundle_name_pns]
        bundles = Bundle.bundles(bundle_name_pns)
        blacklist.check(bundles, self.args.blacklist_overrides)
        authority = self.args.get('authority', None)
        destinations = self.args.get('destinations', None)
        if authority == None and destinations == None:
            raise MissingUpdateArgumentsError(self.args)
        if self.args.get('authority', None):
            bundles = self.renew(bundles, **kwargs)
        if self.args.get('destinations', None):
            bundles = self.deploy(bundles, **kwargs)
        json = self.transform(bundles)
        return json, status

    def renew(self, bundles, **kwargs):
        crts, expiries, authorities = self.authority.renew_certificates(
            bundles,
            self.args.organization_name,
            self.args.validity_years,
            self.args.bug,
            self.args.sans,
            self.args.repeat_delta,
            self.args.whois_check)
        for bundle, crt, expiry, authority in zip(bundles, crts, expiries, authorities):
            bundle.crt = crt
            bundle.expiry = expiry
            bundle.authority = authority
            bundle.to_disk()
        return bundles

    def deploy(self, bundles, **kwargs):
        installed_bundles = []
        note = 'bug {bug}'.format(**self.args)
        for name, dests in self.args.destinations.items():
            installed_bundles += self.destinations[name].install_certificates(note, bundles, dests)
        return installed_bundles
