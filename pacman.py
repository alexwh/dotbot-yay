import sys, os, subprocess, dotbot, time
from enum import Enum

class PkgStatus(Enum):
    # These names will be displayed
    UP_TO_DATE = 'Up to date'
    INSTALLED = 'Installed'
    NOT_FOUND = 'Not found'
    ERROR = "Errors occurred"
    BUILD_FAIL = "Build failure"
    NOT_SURE = 'Could not determine'

class Pacaur(dotbot.Plugin):
    _directive = 'pacaur'

    def __init__(self, context):
        super(Pacaur, self).__init__(self)
        self._context = context
        self._strings = {}
        self._strings[PkgStatus.UP_TO_DATE] = "nothing to do"
        self._strings[PkgStatus.INSTALLED] = "Total Installed Size"
        self._strings[PkgStatus.NOT_FOUND] = "no results found"
        self._strings[PkgStatus.BUILD_FAIL] = "failed to build"
        self._strings[PkgStatus.ERROR] = "Errors occurred"

    def can_handle(self, directive):
        return directive == self._directive

    def handle(self, directive, data):
        if directive != self._directive:
            raise ValueError('Pacaur cannot handle directive %s' % directive)
        return self._process_packages(data)

    def _process_packages(self, packages):
        defaults = self._context.defaults().get('pacaur', {})
        results = {}
        successful = [PkgStatus.UP_TO_DATE, PkgStatus.INSTALLED]

        for pkg in packages:
            result = self._install(pkg)
            results[result] = results.get(result, 0) + 1
            if result not in successful:
                self._log.error("Could not install package '{}'".format(pkg))

        if all([result in successful for result in results.keys()]):
            self._log.info('All packages installed successfully')
            success = True
        else:
            success = False

        for status, amount in results.items():
            log = self._log.info if status in successful else self._log.error
            log('{} {}'.format(amount, status.value))

        return success

    def _install(self, pkg):
        # Make sure we are sudo so we don't have any problems
        subprocess.call('sudo --validate', shell=True)

        cmd = 'pacaur --needed --noconfirm -S {}'.format(pkg)

        self._log.info("Installing \"{}\"".format(pkg))

        process = subprocess.Popen(cmd, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)

        out = []

        while True:
            line = process.stdout.readline().decode('utf-8')
            if not line:
                break
            out.append(line)
            self._log.lowinfo(line.strip())
            sys.stdout.flush()

        process.stdout.close()

        out = ''.join(out)

        for status in self._strings.keys():
            if out.find(self._strings[status]) >= 0:
                return status

        self._log.warn("Could not determine what happened with package {}".format(pkg))
        return PkgStatus.NOT_SURE