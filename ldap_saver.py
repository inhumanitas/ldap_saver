# coding: utf-8
import sys
from _ldap import LDAPError
import ldap
import yaml

from simpleldap import Connection as LDAPConnection
from savers.postgredb import PostgreSaver

__author__ = 'morose'

# python-ldap do not accepts unicode
ldap_str = lambda x: x.encode('utf-8') if isinstance(x, unicode) else x


def get_ldap_data(ldap_con, ldap_params):
    u"""Retrieves data from ldap"""
    base_dn = 'cn=Users,dc=ad,dc=test'
    base_dn = ldap_params.get('base_dn')
    dn = u"{user}@{dn}".format(
        user=ldap_params.get('un'), dn=ldap_params.get('domain_name'))

    filter_ = ldap_params.get('filter')
    attrs = ldap_params.get('attrs')

    dn = ldap_str(dn)
    try:
        results = ldap_con.search(filter_, base_dn, attrs, ldap.SCOPE_SUBTREE)
    except ldap.INVALID_CREDENTIALS:
        print "Your username or password is incorrect."
        sys.exit(1)

    except LDAPError as e:
        if type(e.message) == dict:
            for (k, v) in e.message.iteritems():
                sys.stderr.write("%s: %sn" % (k, v) )
        else:
            sys.stderr.write(e.message)
        sys.exit(1)

    rows = results
    return rows


def ldap_data_to_db_data(data, saving_cols):
    u"""Convert ldap rows to db format"""
    def row_generate(dct):
        u"""Extract params for each column"""
        row = dict()
        for c in saving_cols:
            row[c] = dct.first(c) if c in dct else ''
        return row

    res = []
    # make list of params dict for each row
    for d in data:
        db_row = row_generate(d)
        # filter empty rows
        if any(db_row.values()):
            res.append(db_row)

    return res


def ldap2postgre(ldap_params, postgre_params):
    u"""Querying ldap rows and saves to postgresql db"""
    def ldap_init_params(d):
        u"""filter options for LDAPConnection"""
        init_args = [
            'hostname', 'port', 'dn', 'password', 'encryption',
            'require_cert', 'debug', 'initialize_kwargs', 'options',
            'search_defaults',
        ]
        return {k: ldap_str(d.get(k)) for k in init_args if k in d}

    dn = u'{user}@{dn}'.format(
        user=ldap_params.get(u'un'),
        dn=ldap_params.get(u'domain_name'),
    )
    ldap_params.update({u'dn': dn})
    cols = postgre_params.get('saving_columns', [])
    ps = PostgreSaver(postgre_params)
    data = None

    with LDAPConnection(**ldap_init_params(ldap_params)) as ldap_con:
        data = get_ldap_data(ldap_con, ldap_params)

    if data:
        ps.write_data(ldap_data_to_db_data(data, cols))


def load_configs(conf_path):
    with open(conf_path, 'r', ) as fh:
        c = yaml.load(fh)
    return c


if __name__ == '__main__':

    configs = load_configs('config.yaml')

    ldap2postgre(configs.get(u'ldap_conf'), configs.get(u'postgre_conf'))
