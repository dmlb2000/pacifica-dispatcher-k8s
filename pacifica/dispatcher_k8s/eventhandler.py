#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Event Handler Module.

Contains the event handler classes for the scripts.
"""
import os
import csv
import contextlib
import subprocess
from shutil import rmtree
from json import dumps
from jsonpath2.path import Path
from cloudevents.model import Event
from pacifica.downloader import Downloader
from pacifica.uploader import Uploader
from pacifica.cli.methods import generate_requests_auth
from pacifica.dispatcher.models import File, Transaction, TransactionKeyValue
from pacifica.dispatcher.event_handlers import EventHandler
from pacifica.dispatcher.downloader_runners import DownloaderRunner, RemoteDownloaderRunner
from pacifica.dispatcher.uploader_runners import UploaderRunner, RemoteUploaderRunner
from .config import get_config, get_script_config
from .dispatcher import ROUTER
from .orm import ScriptLog


@contextlib.contextmanager
def _redirect_stdout_stderr(tempdir_name, prefix='', mode='w'):
    with open(os.path.join(tempdir_name, '{}stdout.log'.format(prefix)), mode) as stdout_file:
        with open(os.path.join(tempdir_name, '{}stderr.log'.format(prefix)), mode) as stderr_file:
            with contextlib.redirect_stdout(stdout_file):
                with contextlib.redirect_stderr(stderr_file):
                    yield (stdout_file, stderr_file)


def generate_eventhandler(script_config):
    """Generate and return an event handler for a script."""
    # By definition should only be one method.
    # pylint: disable=too-few-public-methods
    class ScriptEventHandler(EventHandler):
        """Script event handler to download run a script and cleanup/upload."""

        def __init__(self, downloader_runner: DownloaderRunner, uploader_runner: UploaderRunner) -> None:
            """Save the download and upload runner classes for later use."""
            super().__init__()
            self.downloader_runner = downloader_runner
            self.uploader_runner = uploader_runner

        @staticmethod
        def _create_scriptlog(event: Event) -> ScriptLog:
            ret = ScriptLog(
                event=dumps(event.to_dict()),
                script_id=script_config.script_id
            )
            ret.save(force_insert=True)
            return ret

        def _handle_download(self, event: Event) -> None:
            """Handle the download of the data to the download directory."""
            output_path = os.path.join(script_config.data_dir, event.event_id, 'output')
            down_path = os.path.join(script_config.data_dir, event.event_id, 'download')
            if os.path.isdir(down_path):  # pragma: no cover just sanity condition should never happen
                rmtree(down_path)
            os.makedirs(output_path)
            os.makedirs(down_path)
            file_insts = File.from_cloudevents_model(event)
            # just make sure we have everything and the file objs are closed
            with _redirect_stdout_stderr(output_path, 'download-'):
                for file_opener in self.downloader_runner.download(down_path, file_insts):
                    with file_opener():
                        pass

        @staticmethod
        def _handle_script(script_log: ScriptLog, event: Event) -> None:
            exe_log_dir = os.path.join(script_config.data_dir, event.event_id, script_config.output_dirs[0].directory)
            with _redirect_stdout_stderr(exe_log_dir):
                try:
                    status = subprocess.run(
                        [os.path.join(script_config.script_dir, script_config.script)],
                        capture_output=True,
                        cwd=os.path.join(script_config.data_dir, event.event_id),
                        check=True
                    )
                except subprocess.CalledProcessError as ex:
                    script_log.return_code = ex.returncode
                    script_log.stdout = ex.stdout
                    script_log.stderr = ex.stderr
                    script_log.save()

            script_log.return_code = status.returncode
            script_log.stdout = status.stdout
            script_log.stderr = status.stderr
            script_log.save()

        @staticmethod
        def _parse_csv_file(upload_dir, upload_config):
            ret = []
            if os.path.isfile(os.path.join(upload_dir, upload_config.kvfile)):
                with open(os.path.join(upload_dir, upload_config.kvfile)) as csvfile:
                    for row in csv.reader(csvfile):
                        ret.append(
                            TransactionKeyValue(key=row[0], value=row[1]),
                        )
            return ret

        def _handle_uploads(self, event: ScriptLog):
            transaction_inst = Transaction.from_cloudevents_model(event)
            for upload_config in script_config.output_dirs:
                upload_dir = os.path.join(script_config.data_dir, event.event_id, upload_config.directory)
                with _redirect_stdout_stderr(upload_dir):
                    (_bundle, _job_id, _state) = self.uploader_runner.upload(
                        upload_dir,
                        transaction=Transaction(
                            submitter=transaction_inst.submitter,
                            instrument=transaction_inst.instrument,
                            project=transaction_inst.project
                        ),
                        transaction_key_values=self._parse_csv_file(upload_dir, upload_config)
                    )

        def handle(self, event: Event) -> None:
            """
            Example handle event.

            This handler downloads all files in the event.
            Converts the files to uppercase and uploads them back to Pacifica.
            """
            script_log = self._create_scriptlog(event)
            self._handle_download(event)
            self._handle_script(script_log, event)
            self._handle_uploads(event)
    return ScriptEventHandler


def make_routes():
    """Make the routes in the router."""
    auth_obj = generate_requests_auth(get_config())
    for script in get_config().options('dispatcher_k8s_scripts'):
        script_config = get_script_config(get_config(), script)
        ROUTER.add_route(
            # pylint: disable=no-member
            Path.parse_str(script_config.router_jsonpath),
            generate_eventhandler(script_config)(
                RemoteDownloaderRunner(Downloader(**auth_obj)), RemoteUploaderRunner(Uploader(**auth_obj))
            )
        )
