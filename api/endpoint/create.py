#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
autocert.create
'''

import os

from pprint import pformat
from attrdict import AttrDict
from datetime import timedelta

from utils.format import fmt
#from utils import tar
from utils import pki
from cert import create_cert_name

from app import app

from endpoint.base import EndpointBase

class UnknownCertificateAuthorityError(Exception):
    def __init__(self, authority):
        msg = fmt('unknown certificate authority: {authority}')
        super(UnknownCertificateAuthorityError, self).__init__(msg)

class CreateEndpoint(EndpointBase):
    def __init__(self, cfg, args):
        super(CreateEndpoint, self).__init__(cfg, args)

    @property
    def authority(self):
        return self.authorities[self.args.authority]

    def execute(self):
        status = 201
        key, csr = pki.create_key_and_csr(self.args.common_name, self.args.sans)
        crt, expiry, authority = self.authority.create_certificate(
            self.args.organization_name,
            self.args.common_name,
            self.timestamp,
            csr,
            self.args.sans,
            self.args.repeat_delta)
        cert = self.tardata.create_cert(
            self.args.common_name,
            self.timestamp,
            key,
            csr,
            crt,
            self.args.sans,
            expiry,
            authority)
        if self.args.destinations:
            for name, dests in self.args.destinations.items():
                cert = self.destinations[name].install_certificates([cert], *dests)[0]
        json = self.transform([cert])
        return json, status
