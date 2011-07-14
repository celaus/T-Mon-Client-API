##############################################################################
#
# Copyright (c) 2011 Reality Jockey Ltd. and Contributors.
# This file is part of T-Mon Client.
#
# T-Mon Client is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# T-Mon Client is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with T-Mon Client. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# -*- coding: utf-8 -*-

__docformat__ = "reStructuredText"

from django.conf import settings

import unittest, doctest

from django.db.backends.creation import BaseDatabaseCreation

from django.core import management
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.commands.flush import Command as FlushCommand
from django.test import utils
from django.db import connection, transaction

from zope.testing.doctestunit import DocFileSuite

from rjdj.tmon.server.utils.connection import connection as conn

KEEP_DATA = False

## https://bitbucket.org/andrewgodwin/south/changeset/21a635231327
class SkipFlushCommand(FlushCommand):
    def handle_noargs(self, **options):
        return

def patch(f):
    def wrapper(*args, **kwargs):
        # hold onto the original and replace flush command with a no-op
        from django.core.management import get_commands
        get_commands()
        original_flush_command = management._commands['flush']
        try:
            management._commands['flush'] = SkipFlushCommand()
            # run create_test_db
            f(*args, **kwargs)
        finally:
            # unpatch flush back to the original
            management._commands['flush'] = original_flush_command
    return wrapper

class DjangoLayer(object):
    
    saved_state = []

    @classmethod
    def setUp(self):
        utils.setup_test_environment()
        connection.creation.create_test_db = patch(connection.creation.create_test_db)
        connection.creation.create_test_db(verbosity = 0, autoclobber = True)
        
        self.saved_state = [d for d in conn.server]
        
    @classmethod
    def tearDown(self):
        call_command('flush', verbosity = 0, interactive = False)
        
        if not KEEP_DATA and conn.database:
            for db in conn.server:
                if db not in self.saved_state and not db.startswith("_"):
                    del conn.server[db]

    @classmethod
    def testSetUp(self):
        pass

    @classmethod
    def testTearDown(self):
        call_command('flush', verbosity = 0, interactive = False)


def test_suite():
    # Client Tests
    client = DocFileSuite('client/tests/tests.txt',
        optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        )


    suite = unittest.TestSuite((
                                client,
                                ))
    suite.layer = DjangoLayer
    return suite
