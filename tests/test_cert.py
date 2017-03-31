#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pytest

from subprocess import check_output

from utils.format import fmt, pfmt
from utils.cert import Cert

DIR = os.path.dirname(os.path.realpath(__file__))
KEY = open(DIR+'/key').read()
CSR = open(DIR+'/csr').read()
CRT = open(DIR+'/crt').read()


@pytest.fixture
def cert():
    return Cert(
        'common.name',
        20170209155541 ,
        KEY,
        CSR,
        CRT,
        expiry=20170401000000,
        authority=dict(digicert=dict(order_id=1298368)))

def test_ctor(cert):
    assert isinstance(cert, Cert)

def test_cert_name(cert):
    assert cert.cert_name == '{0}@{1}'.format(cert.common_name, cert.timestamp)

def test_tarfile(cert):
    assert cert.tarfile == cert.cert_name + '.tar.gz'

def test_files(cert):
    assert cert.files == {
        cert.cert_name + '.key': KEY,
        cert.cert_name + '.csr': CSR,
        cert.cert_name + '.crt': CRT,
    }

def test_disk_roundtrip(cert, tmpdir, capsys):
    tarpath = tmpdir.mkdir('tarpath')
    tarfile = cert.save(tarpath)
    cert2 = Cert.load(tarpath, cert.cert_name)
    assert cert == cert2

def test_json_roundtrip(cert):
    json = cert.to_json()
    print('json =', json)
    cert2 = Cert.from_json(json)
    assert cert == cert2