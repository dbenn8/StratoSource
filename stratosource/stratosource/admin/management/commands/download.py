#    Copyright 2010, 2011 Red Hat Inc.
#
#    This file is part of StratoSource.
#
#    StratoSource is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    StratoSource is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with StratoSource.  If not, see <http://www.gnu.org/licenses/>.
#    
from django.core.management.base import BaseCommand, CommandError
import logging
import time
import datetime
import os
from stratosource.admin.models import Branch
import stratosource.admin.management.CSBase # used to initialize logging
from stratosource.admin.management import Utils

__author__="mark"
__date__ ="$Sep 7, 2010 9:02:55 PM$"


class Command(BaseCommand):
    args = ''
    help = 'download assets from Salesforce'

    def handle(self, *args, **options):

        if len(args) < 2: raise CommandError('usage: <repo name> <branch>')

        self.logger = logging.getLogger('download')

        br = Branch.objects.get(repo__name__exact=args[0], name__exact=args[1])
        if not br: raise CommandException("invalid repo/branch")

        downloadOnly = False
        if len(args) > 2 and args[2] == '--download-only': downloadOnly = True

        agent = Utils.getAgentForBranch(br, logger=self.logger)

        path = br.api_store
        types = [aType.strip() for aType in br.api_assets.split(',')]

        stamp = str(int(time.time()))
        filename = os.path.join(path, 'retrieve_{0}.zip'.format(stamp))

        self.logger.info('fetching audit data..')
        chgmap = agent.retrieve_changesaudit(types, br.api_pod)

        self.logger.info('retrieving from %s:%s for %s' % (br.repo.name, br.name, br.api_assets))
        agent.retrieve_meta(types, br.api_pod, filename)
        agent.close()
        self.logger.info('finished download')

        if not downloadOnly:
            from stratosource.admin.management.checkin import perform_checkin, save_objectchanges
            perform_checkin(br.repo.location, filename, br)
            batch_time = datetime.datetime.now()
            self.logger.debug('saving audit...')
            save_objectchanges(br, batch_time, chgmap)
            os.remove(filename)

