#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
autocert.update
'''

from pprint import pformat
from attrdict import AttrDict

from utils.format import fmt, pfmt
from utils.output import yaml_format
from utils.exceptions import AutocertError
from utils import blacklist

from app import app

from endpoint.base import EndpointBase

class MissingUpdateArgumentsError(AutocertError):
    def __init__(self, args):
        message = fmt('missing arguments to update; args = {args}')
        super(MissingUpdateArgumentsError, self).__init__(message)

class DeployError(AutocertError):
    def __init__(self):
        message = 'deploy error; deployment didnt happen'
        super(DeployError, self).__init__(message)

class UpdateEndpoint(EndpointBase):
    def __init__(self, cfg, args):
        super(UpdateEndpoint, self).__init__(cfg, args)

    def execute(self, **kwargs):
        app.logger.debug(fmt('Update.execute:\n{locals}'))
        app.logger.debug(fmt('self.args:\n{0}', self.args))
        status = 201
        cert_name_pns = [self.sanitize(cert_name_pn) for cert_name_pn in self.args.cert_name_pns]
        certs = self.tardata.load_certs(*cert_name_pns)
        blacklist.check(certs, self.args.blacklist_overrides)
        authority = self.args.get('authority', None)
        destinations = self.args.get('destinations', None)
        if authority == None and destinations == None:
            raise MissingUpdateArgumentsError(self.args)

        if self.args.command == 'renew':
            certs = self.renew(certs, **kwargs)
        elif self.args.command == 'reissue':
            certs = self.reissue(certs, **kwargs)
        if self.args.get('destinations', None):
            certs = self.deploy(certs, **kwargs)
        json = self.transform(certs)
        return json, status

    def renew(self, certs, **kwargs):
        app.logger.debug(fmt('renew:\n{locals}'))
        csrs, crts, expiries, authorities = self.authority.renew_certificates(
            certs,
            self.args.organization_name,
            self.args.validity_years,
            self.args.bug,
            self.args.sans,
            self.args.repeat_delta,
            self.args.no_whois_check)
        for cert, csr, crt, expiry, authority in zip(certs, csrs, crts, expiries, authorities):
            if cert.csr != csr:
                app.logger.debug('updating csr')
            cert.csr = csr
            if cert.crt != crt:
                app.logger.debug('updating crt')
            cert.crt = crt
            cert.expiry = expiry
            app.logger.debug('UPDATE AUTHORITY:')
            app.logger.debug(fmt('cert.authority = {0}', cert.authority))
            app.logger.debug(fmt('authority = {authority}'))
            cert.authority = authority
            self.tardata.update_cert(cert)
        return certs

    def reissue(self, certs, **kwargs):
        app.logger.debug(fmt('reissue:\n{locals}'))
        csrs, crts, expiries, authorities = self.authority.reissue_certificates(
            certs,
            self.args.organization_name,
            self.args.validity_years,
            self.args.bug,
            self.args.sans,
            self.args.repeat_delta,
            self.args.no_whois_check)
        for cert, csr, crt, expiry, authority in zip(certs, csrs, crts, expiries, authorities):
            if cert.csr != csr:
                app.logger.debug('updating csr')
            cert.csr = csr
            if cert.crt != crt:
                app.logger.debug('updating crt')
            cert.crt = crt
            cert.expiry = expiry
            app.logger.debug('UPDATE AUTHORITY:')
            app.logger.debug(fmt('cert.authority = {0}', cert.authority))
            app.logger.debug(fmt('authority = {authority}'))
            cert.authority = authority
            self.tardata.update_cert(cert)
        return certs

    def deploy(self, certs, **kwargs):
        app.logger.debug(fmt('deploy:\n{locals}'))
        installed_certs = []
        note = 'bug {bug}'.format(**self.args)
        for name, dests in self.args.destinations.items():
            installed_certs += self.destinations[name].install_certificates(note, certs, *dests)
        return installed_certs
