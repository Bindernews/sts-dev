#!/usr/bin/env python3
import argparse
from collections import namedtuple
import os
from pathlib import Path
import shutil
import subprocess as sp
from typing import List
import xml.etree.ElementTree as ET

MvnRepo = namedtuple('MvnRepo', ['id', 'name', 'url'])

GH_BASE = 'https://github.com/'
BASEMOD_REPO = GH_BASE + 'daviscook477/BaseMod'
MTS_REPO = GH_BASE + 'kiooeht/ModTheSpire'
STSLIB_REPO = GH_BASE + 'kiooeht/StSLib'
DEPLOY_REPO = MvnRepo(
    'github',
    'bindernews GitHub Maven Packages',
    os.getenv('GH_MAVEN_REPO'),
)

def shrun(cmd: str, cwd: Path) -> None:
    '''Run `cmd` in the given directory as if from a shell.'''
    sp.run(cmd, cwd=cwd, shell=True).check_returncode()

class LibTask:
    def __init__(self, name: str, repo: str, base_dir: Path, clean_files: List[str] = []):
        self.name = name
        '''Name of the task'''
        self.repo = repo
        '''Git repository containing the source code'''
        self.dir = Path(base_dir, name)
        '''Directory to clone source code into and build in'''
        self.mvn_repo: MvnRepo = None
        '''Maven package repository to deploy into'''
        self.clean_files = clean_files
        '''List of paths which will be removed to clean up this library, may use environment variables.'''

    def download(self):
        if not self.dir.is_dir():
            sp.run(['git', 'clone', self.repo, str(self.dir.absolute())]).check_returncode()
            # Backup original pom XML
            shutil.copyfile(Path(self.dir, 'pom.xml'), Path(self.dir, 'pom.xml.bak'))

    def build(self):
        shrun('mvn package', cwd=self.dir)
        shrun('mvn install', cwd=self.dir)

    def deploy(self):
        '''
        Deploy the library to the Maven repository.

        Must have called build() and set mvn_repo first.
        '''
        tree = ET.parse(Path(self.dir, 'pom.xml.bak'))
        self.edit_pom(tree.getroot())
        tree.write(Path(self.dir, 'pom.xml'))

    def edit_pom(self, pom: ET.Element) -> None:
        '''
        Called by deploy() to modify the pom.xml file, may be overridden
        by subclasses to supplement the default implementation.
        '''
        self.pom_add_mvn_repo(pom)

    def clean(self):
        os.putenv('SRC', self.dir)
        os.putenv('M2', Path('~/.m2/repository').expanduser())
        for pt in self.clean_files:
            pt2 = Path(os.path.expandvars(pt))
            if pt2.is_file() or pt2.is_dir():
                shutil.rmtree(pt2)
    
    def pom_add_mvn_repo(self, pom: ET.Element) -> None:
        rp = self.mvn_repo
        injectElem = ET.XML(f'''
        <distributionManagement>
          <repository>
            <id>{rp.id}</id>
            <name>{rp.name}</name>
            <url>{rp.url}</url>
          </repository>
        </distributionManagement>
        ''')
        pom.append(injectElem)



class Impl:
    def __init__(self, target: Path, desktop_jar: Path, deploy_repo: MvnRepo) -> None:
        self.target = target
        self.desktop_jar: Path = desktop_jar
        '''Path to Slay the Spire desktop-1.0.jar'''
        self.deploy_repo: MvnRepo = deploy_repo
        '''Maven repository where we're going to deploy these libraries to'''
        self.deploy_libs: List[str] = []
        '''List of library names to deploy, subset of libs'''
        self.libs: List[LibTask] = []
        '''
        List of LibTask objects which are libraries to build.
        Libraries will be built in listed order.
        '''

    def parse_deploy_libs(self, v: 'list[str]|str') -> List[str]:
        # Handle all
        if v == '*':
            return [t.name for t in self.libs]
        # Split by comma
        if v is str:
            return v.split(',')
        # Return default
        return v

    def build(self):
        # Copy desktop jar
        Impl.safe_copy(self.desktop_jar, Path(self.target, 'lib/desktop-1.0.jar'))
        # Build and install libraries, ORDER MATTERS
        for lib in self.libs:
            lib.download()
            lib.build()

    def deploy(self):
        '''
        Deploy the libraries as set with deploy_libs
        '''
        tasks = [t for t in self.libs if t.name in self.deploy_libs]
        for task in tasks:
            task.deploy()

    def clean(self):
        for lib in self.libs:
            lib.clean()

    @staticmethod
    def safe_copy(src: Path, dst: Path) -> None:
        os.makedirs(str(dst.parent.absolute()), exist_ok=True)
        shutil.copy(str(src), str(dst))

    def add_default_libs(self) -> None:
        '''Add default LibTask entries'''
        self.libs.extend([
            LibTask('ModTheSpire', MTS_REPO, self.target,
                clean_files=['$SRC/../lib/ModTheSpire.jar', '$M2/com/evacipated/cardcrawl/ModTheSpire/']),
            LibTask('basemod', BASEMOD_REPO, self.target,
                clean_files=['$SRC/../lib/BaseMod.jar', '$M2/basemod/']),
            LibTask('StSLib', STSLIB_REPO, self.target,
                clean_files=['$SRC/../lib/StSLib.jar', '$M2/com/evacipated/cardcrawl/mod/stslib/']),
        ])

def main(args: 'list[str]') -> None:
    parser = argparse.ArgumentParser(args[0])
    parser.add_argument('-t', '--target', type=str, default='.',
        help='Target directory to build everything')
    parser.add_argument('--skip-build', action='store_true',
        help='Skip the build process and only install')
    parser.add_argument('--deploy', type=str, default='*',
        help='Comma-separated list of libraries to deploy, * deploys all, NO deploys nothing')
    parser.add_argument('--desktop-jar', type=Path, default=Path('/host/desktop-1.0.jar'),
        help='Path (in Docker) to desktop-1.0.jar')
    parser.add_argument('--clean', action='store_true',
        help='Remove all built libraries, overrides other actions')
    args = parser.parse_args(args[1:])

    impl = Impl(
        target=Path(args.target),
        desktop_jar=args.desktop_jar,
        deploy_repo=DEPLOY_REPO,
    )
    impl.add_default_libs()
    impl.deploy_libs = impl.parse_deploy_libs(args.deploy)
    if args.clean:
        impl.clean()
    else:
        if not args.skip_build:
            impl.build()
        impl.deploy()

if __name__ == '__main__':
    import sys
    main(sys.argv)