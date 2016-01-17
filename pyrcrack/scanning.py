#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Scanning functions
"""
import os
import csv
import time
import psutil
import threading
from . import Air
from io import StringIO
from subprocess import Popen, DEVNULL


class Airodump(Air):
    """
        Please referr to airodump-ng's help
        for this.

        .. TODO::

            Automagically extract this help =)
     """

    _aps = []
    _clients = []
    _stop = False
    _allowed_arguments = (
        ('ivs', False),
        ('gpsd', False),
        ('beacons', False),
        ('manufacturer', False),
        ('uptime', False),
        ('ignore_negative_one ', False),
        ('a', False),
        ('showack', False),
        ('h', False),
        ('f', False),
        ('update', False),
        ('berlin', False),
        ('r', False),
        ('x', False),
        ('encrypt', False),
        ('netmask', False),
        ('bssid', False),
        ('essid', False),
        ('output_format', False),
        ('write', False),
        ('essid_regex', False))

    def __init__(self, interface=False, **kwargs):
        self.interface = interface
        super(self.__class__, self).__init__(**kwargs)

    @property
    def aps(self):
        """
            Returns currently reported aps
        """
        self.update_results()
        return self._aps

    @property
    def clients(self):
        """
            Returns currently reported clients
        """
        self.update_results()
        return self._clients

    def scan(self):
        """
            Get next result: implement in childrens
            Both this and previous one must be
            responsible for duplicates
        """
        self.start()
        while not os.path.exists(self.curr_csv):
            time.sleep(5)

    def watch_process(self):
        """
            Watcher thread.
            This one relaunches airodump eatch time it dies
        """
        psutil.wait_procs([psutil.Process(self._proc.pid)],
                          callback=self.start)

    def start(self, _=False):
        """
            Start process.
            psutil sends an argument (that we don't actually need...)
            interface defaults to monitor interface 0 as started by Airmon
        """
        if not self._stop:
            self._current_execution += 1
            flags = self.flags
            if '--write' not in flags:
                flags.extend(['--write', self.writepath])
            if '--output-format' not in flags:
                flags.extend(['--output-format', 'csv'])
            line = ["airodump-ng"] + flags + self.arguments + [self.interface]
            self._proc = Popen(line, bufsize=0,
                               env={'PATH': os.environ['PATH']},
                               stderr=DEVNULL, stdin=DEVNULL, stdout=DEVNULL)
            os.system('stty sane')

        watcher = threading.Thread(target=self.watch_process)
        watcher.start()

    def stop(self):
        """
            Stop proc.
        """
        self._stop = True
        return self._proc.kill()

    def update_results(self):
        """
            Updates self.clients and self.aps
        """
        clis = []
        aps = []

        with open(self.curr_csv) as fileo:
            file_ = fileo.readlines()
            file_enum = enumerate(file_)
            num = 0
            for num, line in file_enum:
                if line.startswith('BSSID'):
                    continue
                if line.startswith('Station'):
                    num += 1
                    break
                aps.append(line)
            for line in file_[num:]:
                clis.append(line)

        self._aps = [[a.strip() for a in row]
                     for row in csv.reader(StringIO('\n'.join(aps)))
                     if row]
        self._clients = [[a.strip() for a in row]
                         for row in csv.reader(StringIO('\n'.join(clis)))
                         if row]

    def __enter__(self, *args, **kwargs):
        self.start(*args, **kwargs)
        return self

    def __exit__(self, *args, **kwargs):
        self.stop(*args, **kwargs)
        return self
