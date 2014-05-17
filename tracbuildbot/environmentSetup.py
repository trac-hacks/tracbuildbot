# -*- coding: utf-8 -*-
#

from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, DatabaseManager
from trac.util.text import printout


# Database schema variables
db_version_key = 'tracbuildbot_version'
db_version = 1

table = Table('buildbot_builds', key = 'id') [
            Column('id', type = 'integer', auto_increment = True),
            Column('builder'),
            Column('status'),
            Column('start', type='int64'),
            Column('num', type='int64'),
            Column('finish', type='int64'),
            Column('rev'),
            Column('error'),
            Column('error_log'),
        ]

"""
Extension point interface for components that need to participate in the
creation and upgrading of Trac environments, for example to create
additional database tables."""
class BuildbotParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    """
    Called when a new Trac environment is created."""
    def environment_created(self):
        pass

    """
    Called when Trac checks whether the environment needs to be upgraded.
    Should return `True` if this participant needs an upgrade to be
    performed, `False` otherwise."""
    def environment_needs_upgrade(self, db):
        # Initialise database schema version tracking.
        cursor = db.cursor()
        # Get currently installed database schema version
        db_installed_version = 0
        try:
            sqlGetInstalledVersion = """SELECT value FROM system WHERE name = %s"""
            cursor.execute(sqlGetInstalledVersion, [db_version_key])
            db_installed_version = int(cursor.fetchone()[0])
        except:
            # No version currently, inserting new one.
            db_installed_version = 0

        self.log.debug("tracbuildbot database schema version: %s (should be %s)",
                       db_installed_version, db_version)
        # return boolean for if we need to update or not
        needsUpgrade = (db_installed_version < db_version)
        if needsUpgrade:
            self.log.info("tracbuildbot database schema version is %s, should be %s",
                          db_installed_version, db_version)
        return needsUpgrade


    """
    Actually perform an environment upgrade.
    Implementations of this method should not commit any database
    transactions. This is done implicitly after all participants have
    performed the upgrades they need without an error being raised."""
    def upgrade_environment(self, db):
        printout("Upgrading tracbuildbot database schema")
        cursor = db.cursor()

        db_installed_version = 0
        sqlGetInstalledVersion = """SELECT value FROM system WHERE name = %s"""
        cursor.execute(sqlGetInstalledVersion, [db_version_key])
        for row in cursor:
            db_installed_version = int(row[0])
        printout("tracbuildbot database schema version is %s, should be %s" %
                 (db_installed_version, db_version))

        db_connector, _ = DatabaseManager(self.env)._get_connector()

        if db_installed_version < 1:
            # Create tables
            for statement in db_connector.to_sql(table):
                cursor.execute(statement)
                    
            sqlInsertVersion = """INSERT INTO system (name, value) VALUES (%s,%s)"""
            cursor.execute(sqlInsertVersion, [db_version_key, db_version])
            db_installed_version = 1
            
