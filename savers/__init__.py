# coding: utf-8

__author__ = 'morose'


class IWriter(object):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def write_data(self, row):
        raise NotImplementedError

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError


class Saver(object):
    writer = None

    def __init__(self, writer_params):
        self._conf_params = writer_params

    def write_data(self, data):
        with self.writer(**self._conf_params) as wr:
            wr.write_data(data)
