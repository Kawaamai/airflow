# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Database sub-commands"""
import os
import subprocess
import textwrap
from tempfile import NamedTemporaryFile

from airflow import AirflowException, settings
from airflow.utils import cli as cli_utils, db


def initdb(args):
    """Initializes the metadata database"""
    print("DB: " + repr(settings.engine.url))
    db.initdb()
    print("Done.")


def resetdb(args):
    """Resets the metadata database"""
    print("DB: " + repr(settings.engine.url))
    if args.yes or input("This will drop existing tables "
                         "if they exist. Proceed? "
                         "(y/n)").upper() == "Y":
        db.resetdb()
    else:
        print("Bail.")


@cli_utils.action_logging
def upgradedb(args):
    """Upgrades the metadata database"""
    print("DB: " + repr(settings.engine.url))
    db.upgradedb()


@cli_utils.action_logging
def shell(args):
    """Run a shell that allows to access metadata database"""
    url = settings.engine.url
    print("DB: " + repr(url))

    if url.get_backend_name() == 'mysql':
        with NamedTemporaryFile(suffix="my.cnf") as f:
            content = textwrap.dedent(f"""
                [client]
                host     = {url.host}
                user     = {url.username}
                password = {url.password or ""}
                port     = {url.port or ""}
                database = {url.database}
                """).strip()
            f.write(content.encode())
            f.flush()
            subprocess.Popen(["mysql", f"--defaults-extra-file={f.name}"]).wait()
    elif url.get_backend_name() == 'sqlite':
        subprocess.Popen(["sqlite3", url.database]).wait()
    elif url.get_backend_name() == 'postgresql':
        env = os.environ.copy()
        env['PGHOST'] = url.host or ""
        env['PGPORT'] = url.port or ""
        env['PGUSER'] = url.username or ""
        # PostgreSQL does not allow the use of PGPASSFILE if the current user is root.
        env["PGPASSWORD"] = url.password or ""
        env['PGDATABASE'] = url.database
        subprocess.Popen(["psql"], env=env).wait()
    else:
        raise AirflowException(f"Unknown driver: {url.drivername}")
