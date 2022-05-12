#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2021-09-15 10:39:34
# @Author  : Your Name (you@example.org)
# @Link    : link
# @Version : 1.0.0

import signal
import subprocess
import sys
import textwrap
import time
from contextlib import suppress
from time import sleep
from typing import List, NoReturn

from loguru import logger

import psutil
from lockfile.pidlockfile import PIDLockFile


class GunicornMonitor():

    def __init__(
        self,
        gunicorn_master_pid: int,
        num_workers_expected: int,
        master_timeout: int,
        worker_refresh_interval: int,
        worker_refresh_batch_size: int,
    ):
        super().__init__()
        self.gunicorn_master_proc: psutil.Process = psutil.Process(gunicorn_master_pid)
        self.num_workers_expected = num_workers_expected
        self.master_timeout = master_timeout
        self.worker_refresh_interval = worker_refresh_interval
        self.worker_refresh_batch_size = worker_refresh_batch_size

        self._num_workers_running = 0
        self._num_ready_workers_running = 0
        self._last_refresh_time = time.monotonic() if worker_refresh_interval > 0 else None
        self._restart_on_next_plugin_check = False

    def _get_num_ready_workers_running(self) -> int:
        """Returns number of ready Gunicorn workers by looking for READY_PREFIX in process name"""
        workers: List[psutil.Process] = psutil.Process(self.gunicorn_master_proc.pid).children()

        def ready_prefix_on_cmdline(proc: psutil.Process):
            try:
                return proc.is_running()
            except psutil.NoSuchProcess as e:
                logger.exception(e)
            return False

        ready_workers = [proc for proc in workers if ready_prefix_on_cmdline(proc)]
        return len(ready_workers)

    def _get_num_workers_running(self) -> int:
        """Returns number of running Gunicorn workers processes"""
        workers = psutil.Process(self.gunicorn_master_proc.pid).children()
        return len(workers)

    def _wait_until_true(self, fn, timeout: int = 0) -> None:
        """Sleeps until fn is true"""
        start_time = time.monotonic()
        while not fn():
            if 0 < timeout <= time.monotonic() - start_time:
                raise Exception(f"No response from gunicorn master within {timeout} seconds")
            sleep(0.1)

    def _spawn_new_workers(self, count: int) -> None:
        """
        Send signal to kill the worker.
        :param count: The number of workers to spawn
        """
        excess = 0
        for _ in range(count):
            # TTIN: Increment the number of processes by one
            self.gunicorn_master_proc.send_signal(signal.SIGTTIN)
            excess += 1
            self._wait_until_true(
                lambda: self.num_workers_expected + excess == self._get_num_workers_running(),
                timeout=self.master_timeout,
            )

    def _kill_old_workers(self, count: int) -> None:
        """
        Send signal to kill the worker.
        :param count: The number of workers to kill
        """
        for _ in range(count):
            count -= 1
            # TTOU: Decrement the number of processes by one
            self.gunicorn_master_proc.send_signal(signal.SIGTTOU)
            self._wait_until_true(
                lambda: self.num_workers_expected + count == self._get_num_workers_running(),
                timeout=self.master_timeout,
            )

    def _reload_gunicorn(self) -> None:
        """
        Send signal to reload the gunicorn configuration. When gunicorn receive signals, it reload the
        configuration, start the new worker processes with a new configuration and gracefully
        shutdown older workers.
        """
        # HUP: Reload the configuration.
        self.gunicorn_master_proc.send_signal(signal.SIGHUP)
        sleep(1)
        self._wait_until_true(
            lambda: self.num_workers_expected == self._get_num_workers_running(), timeout=self.master_timeout
        )

    def start(self) -> NoReturn:
        """Starts monitoring the webserver."""
        try:
            self._wait_until_true(
                lambda: self.num_workers_expected == self._get_num_workers_running(),
                timeout=self.master_timeout,
            )
            while True:
                if not self.gunicorn_master_proc.is_running():
                    sys.exit(1)
                self._check_workers()
                # Throttle loop
                sleep(5)

        except Exception as err:
            logger.exception(err)
            logger.error("Shutting down webserver")
            try:
                self.gunicorn_master_proc.terminate()
                self.gunicorn_master_proc.wait()
            finally:
                sys.exit(1)

    def _check_workers(self) -> None:
        num_workers_running = self._get_num_workers_running()
        num_ready_workers_running = self._get_num_ready_workers_running()

        # Whenever some workers are not ready, wait until all workers are ready
        if num_ready_workers_running < num_workers_running:
            logger.info(
                f'[{num_ready_workers_running} / {num_workers_running}] Some workers are starting up, waiting...')
            sleep(1)
            return

        # If there are too many workers, then kill a worker gracefully by asking gunicorn to reduce
        # number of workers
        if num_workers_running > self.num_workers_expected:
            excess = min(num_workers_running - self.num_workers_expected, self.worker_refresh_batch_size)
            logger.info(
                f'[{num_ready_workers_running} / {num_workers_running}] Killing {excess} workers'
            )
            self._kill_old_workers(excess)
            return

        # If there are too few workers, start a new worker by asking gunicorn
        # to increase number of workers
        if num_workers_running < self.num_workers_expected:
            logger.error(
                f"[{num_ready_workers_running} / {num_workers_running}] Some workers seem to have died and gunicorn did not restart them as expected"
            )
            sleep(10)
            num_workers_running = self._get_num_workers_running()
            if num_workers_running < self.num_workers_expected:
                new_worker_count = min(
                    self.num_workers_expected - num_workers_running, self.worker_refresh_batch_size
                )
                # log at info since we are trying fix an error logged just above
                logger.info(
                    f'[{num_ready_workers_running} / {num_workers_running}] Spawning {new_worker_count} workers'
                )
                self._spawn_new_workers(new_worker_count)
            return

        # Now the number of running and expected worker should be equal

        # If workers should be restarted periodically.
        if self.worker_refresh_interval > 0 and self._last_refresh_time:
            # and we refreshed the workers a long time ago, refresh the workers
            last_refresh_diff = time.monotonic() - self._last_refresh_time
            if self.worker_refresh_interval < last_refresh_diff:
                num_new_workers = self.worker_refresh_batch_size
                logger.debug(
                    f'[{num_ready_workers_running} / {num_workers_running}] Starting doing a refresh. Starting {num_new_workers} workers.')
                self._spawn_new_workers(num_new_workers)
                self._last_refresh_time = time.monotonic()
                return
        # Monitor system load
        # if self._last_refresh_time:
        #     # print system load
        #     last_refresh_diff = time.monotonic() - self._last_refresh_time
        #     if last_refresh_diff > 60:
        #         one_min, five_min, fifteen_min = psutil.getloadavg()
        #         logger.info(f'SYSTEM LOAD 1m: {one_min:.3f} 5m: {five_min:.3f} 15m: {fifteen_min:.3f}')
        #         self._last_refresh_time = time.monotonic()
        #         return


def webserver():

    from resources.gunicorn_conf import log_data

    # Check if webserver is already running if not, remove old pidfile
    check_if_pidfile_process_is_running(pid_file=str(log_data.get('pidfile', None)), process_name="webserver")

    print(
        textwrap.dedent(
            '''\
            Running the Gunicorn Server with:
            Workers: {num_workers} {workerclass}
            Host: {hostname}:{port}
            Timeout: {worker_timeout}
        '''.format(
                num_workers=log_data.get('workers'),
                workerclass=log_data.get('worker_class'),
                hostname=log_data.get('host'),
                port=log_data.get('port'),
                worker_timeout=log_data.get('timeout'),
            )
        )
    )
    run_args = [
        sys.executable,
        '-m',
        'gunicorn',
        '--config',
        'python:resources.gunicorn_conf',
    ]

    run_args += ["src.main:app"]

    gunicorn_master_proc: psutil.Process = None

    def kill_proc(signum, _):
        logger.warning(f"Received signal: {signum}. Closing gunicorn.")
        gunicorn_master_proc.terminate()
        with suppress(TimeoutError):
            gunicorn_master_proc.wait(timeout=60)
        if gunicorn_master_proc.poll() is not None:
            gunicorn_master_proc.kill()
        sys.exit(0)

    def monitor_gunicorn(gunicorn_master_pid: int):
        # Register signal handlers
        signal.signal(signal.SIGINT, kill_proc)
        signal.signal(signal.SIGTERM, kill_proc)

        # These run forever until SIG{INT, TERM, KILL, ...} signal is sent
        GunicornMonitor(
            gunicorn_master_pid=gunicorn_master_pid,
            num_workers_expected=log_data.get('workers'),
            master_timeout=log_data.get('timeout'),
            worker_refresh_interval=1*60*60,
            worker_refresh_batch_size=1,
        ).start()
    with subprocess.Popen(run_args, close_fds=True) as gunicorn_master_proc:
        monitor_gunicorn(gunicorn_master_proc.pid)

def check_if_pidfile_process_is_running(pid_file: str, process_name: str):
    """
    Checks if a pidfile already exists and process is still running.
    If process is dead then pidfile is removed.
    :param pid_file: path to the pidfile
    :param process_name: name used in exception if process is up and
        running
    """
    pid_lock_file = PIDLockFile(path=pid_file)
    # If file exists
    if pid_lock_file.is_locked():
        # Read the pid
        pid = pid_lock_file.read_pid()
        if pid is None:
            return
        try:
            # Check if process is still running
            proc = psutil.Process(pid)
            if proc.is_running():
                raise Exception(f"The {process_name} is already running under PID {pid}.")
        except psutil.NoSuchProcess:
            # If process is dead remove the pidfile
            pid_lock_file.break_lock()