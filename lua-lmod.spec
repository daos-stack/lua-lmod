#
# spec file for package lua-lmod
#
# Copyright (c) 2019 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


%define _buildshell /bin/bash

#
%define ohpc 0

# only defined on SUSE but stub out for rpmlint on Fedora
%{!?lua_version: %define lua_version 5.3}
%define lua_lmod_modulesdir %{_datarootdir}/lmod/modulefiles:%{_datarootdir}/modules
%define lua_lmod_admin_modulesdir %{_datarootdir}/lmod/admin/modulefiles
%define lua_lmod_moduledeps %{_datarootdir}/lmod/moduledeps
%define lua_path ?.lua;?/?.lua;%{lua_noarchdir}/?.lua;%{lua_noarchdir}/?/init.lua
%define lua_cpath ?.so;?/?.so;%{lua_archdir}/?.so

Name:           lua-lmod
Summary:        Lua-based Environment Modules
License:        MIT
Group:          Development/Libraries/Other
Version:        8.2.5
Release:        lp152.1.01
URL:            https://github.com/TACC/Lmod
%if 0%{?ohpc}
BuildRequires:  ohpc
%endif

Source0:        https://github.com/TACC/Lmod/archive/%{version}.tar.gz
Patch1:         Messages-Remove-message-about-creating-a-consulting-ticket.patch
Patch2:         Doc-Ugly-workaround-for-bug-in-Sphinx.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-build

BuildRequires:  lua >= %{lua_version}
BuildRequires:  lua-devel >= %{lua_version}
BuildRequires:  lua-luafilesystem
BuildRequires:  lua-luaposix
BuildRequires:  lua-luaterm
BuildRequires:  procps
BuildRequires:  rsync
BuildRequires:  tcl
Requires:       lua >= %{lua_version}
Requires:       lua-luafilesystem
Requires:       lua-luaposix
Requires:       lua-luaterm
Requires:       tcl
Conflicts:      Modules
BuildRequires:  python-Sphinx
Provides:       lua-lmod-man = %{version}-%{release}

%description
Lmod is an Environment Module System based on Lua, Reads TCL Modules,
Supports a Software Hierarchy.

%package doc
Summary:        Documentation for Lmod
Group:          Documentation/Other
BuildArch:      noarch

%description doc
Documentation (pdf) for the Lmod Environment Modules System.
 
%prep
%setup -q -n Lmod-%{version}
%patch1 -p1
%if 0%{?sle_version:1} && 0%{?sle_version} < 150000
%patch2 -p1
%endif

%build
export LUA_CPATH="%{lua_cpath}"
export LUA_PATH="%{lua_path}"
%configure --prefix=%{_datadir} \
    --with-module-root-path=%{lua_lmod_modulesdir} \
    --libdir=%{lua_archdir} \
    --datadir=%{lua_noarchdir} \
    --with-redirect=yes \
    --with-autoSwap=no \
    --with-fastTCLInterp=no
make
find my_docs/ -name .gitignore -delete
#cd docs; make %{?build_pdf:latexpdf} %{!?build_pdf:man}; cd ..                                                                                                                                

%install
export LUA_CPATH="%{lua_cpath}"
export LUA_PATH="%{lua_path}"
%make_install

mkdir -p %{buildroot}%{_sysconfdir}/rpm
cat <<EOF > %{buildroot}%{_sysconfdir}/rpm/macros.lmod
%%lua_lmod_modulesdir %{lua_lmod_modulesdir}
%%lua_lmod_admin_modulesdir %{lua_lmod_admin_modulesdir}
%%lua_lmod_moduledeps %{lua_lmod_moduledeps}
EOF
mkdir -p %{buildroot}%{lua_lmod_modulesdir}
mkdir -p %{buildroot}%{lua_lmod_admin_modulesdir}
mkdir -p %{buildroot}%{lua_lmod_moduledeps}
mkdir -p %{buildroot}/%{_mandir}/man1                                                       

# Fix file duplicates
rm -f %{buildroot}/%{_datadir}/lmod/%{version}/init/ksh
ln -s %{_datadir}/lmod/%{version}/init/sh  %{buildroot}/%{_datadir}/lmod/%{version}/init/ksh
rm -f %{buildroot}/%{_datadir}/lmod/%{version}/init/zsh
ln -s %{_datadir}/lmod/%{version}/init/bash  %{buildroot}/%{_datadir}/lmod/%{version}/init/zsh
rm -f %{buildroot}/%{_datadir}/lmod/%{version}/init/tcsh
ln -s %{_datadir}/lmod/%{version}/init/csh %{buildroot}/%{_datadir}/lmod/%{version}/init/tcsh
rm -f %{buildroot}/%{_datadir}/lmod/%{version}/settarg/Version.lua 
ln -s %{_datadir}/lmod/%{version}/libexec/Version.lua %{buildroot}/%{_datadir}/lmod/%{version}/settarg/Version.lua

for file in $(find %{buildroot}%{_datadir}/lmod); do
    [ -f "$file" ] || continue
    line=$(head -1 $file)
    if [[ $line =~ \#\!.*bin/env ]]; then
	case $line in
	    *bash) newline="#! /bin/bash" ;;
	    *) newline="#! /usr/bin/${line##*/env* }" ;;
	esac
	sed -i "1s,^.*,${newline}\n," $file
    fi
done
mkdir -p %{buildroot}/%{_sysconfdir}/profile.d
cat <<EOF >%{buildroot}/%{_sysconfdir}/profile.d/lmod.sh
# -*- shell-script -*-
########################################################################
#  This is the system wide source file for setting up
#  modules:
#
########################################################################

# NOOP if running under known resource manager
if [ ! -z "\$SLURM_NODELIST" ];then
     return
fi

export LMOD_SETTARG_CMD=":"
export LMOD_FULL_SETTARG_SUPPORT=no
export LMOD_COLORIZE=no
export LMOD_PREPEND_BLOCK=normal

if [ \$EUID -eq 0 ]; then
    export MODULEPATH=%{?OHPC_MODULES:%{OHPC_ADMIN}/modulefiles:%{OHPC_MODULES}:}%{lua_lmod_admin_modulesdir}:%{lua_lmod_modulesdir}
else
    export MODULEPATH=%{?OHPC_MODULES:%{OHPC_MODULES}:}%{lua_lmod_modulesdir}
fi

export BASH_ENV=%{_datadir}/lmod/%{version}/init/bash

# Initialize modules system
. \${BASH_ENV} >/dev/null

# Load baseline SUSE HPC environment
module try-add suse-hpc

EOF

cat <<EOF >%{buildroot}/%{_sysconfdir}/profile.d/lmod.csh
# -*- shell-script -*-
########################################################################
#  This is the system wide source file for setting up
#  modules:
#
########################################################################

if ( \$?SLURM_NODELIST ) then
    exit 0
endif

setenv LMOD_SETTARG_CMD ":"
setenv LMOD_FULL_SETTARG_SUPPORT "no"
setenv LMOD_COLORIZE "no"
setenv LMOD_PREPEND_BLOCK "normal"

if ( \`id -u\` == "0" ) then
   setenv MODULEPATH "%{?OHPC_MODULES:%{OHPC_ADMIN}/modulefiles:%{OHPC_MODULES}:}%{lua_lmod_admin_modulesdir}:%{lua_lmod_modulesdir}"
else   
   setenv MODULEPATH "%{?OHPC_MODULES:%{OHPC_MODULES}:}%{lua_lmod_modulesdir}"
endif

# Initialize modules system
source %{_datadir}/lmod/%{version}/init/csh >/dev/null

# Load baseline SUSE HPC environment
module try-add suse-hpc 

EOF

mkdir -p %{buildroot}/%{_mandir}/man1

%files
%license License
%doc README.*
%config %{_sysconfdir}/profile.d/lmod.sh
%config %{_sysconfdir}/profile.d/lmod.csh
%config %{_sysconfdir}/rpm/macros.lmod
%dir %{_datadir}/lmod
%dir %{lua_lmod_modulesdir}
%dir %{lua_lmod_admin_modulesdir}
%dir %{lua_lmod_moduledeps}
%{_datadir}/lmod/*

%files doc
%doc my_docs/*.txt my_docs/*.pdf my_docs/*.md

%changelog
* Mon Jun 22 2020 Brian J. Murrell <brian.murrell@intel.com>
- Hacked up from upstream to build more simply
- Added /usr/share/modules to module search path

* Fri Nov 29 2019 Ana Guerrero Lopez <aguerrero@suse.com>
- Update to version 8.2.5:
  * Better support for the fish shell including tab completion
  * New function extensions(): This allows for modules like python
    to report that the extensions numpy and scipy are part of the
    modules. Users can use "module spider numpy" to find which
    modules provide numpy etc.
  * Added a new command "clearLmod" which does a module purge and
    removes all LMOD aliases and environment variables.
  * Remove asking for the absolute path for generating spiderT
    and dbT. It now only use when building the reverseMapT.
  * Lmod now requires "rx" other access when searching for
    modulefiles.
  * settarg correctly handles a power9 processor running linux.
- Refresh patch
  * Messages-Remove-message-about-creating-a-consulting-ticket.patch
* Thu Aug 22 2019 Ana Guerrero Lopez <aguerrero@suse.com>
- Update to version 8.1.14: (jsc#SLE-8512)
  * Extended Default feature added: module load intel/17 will find
    the "best" intel/17.* etc.
  * All hidden files are NOT written to the softwarePage output.
  * Lmod now correctly reports failed to load module "A" in the
    special case where "ml A B" and A is a prereq of B and A
    doesn't exist.
  * A meta module takes precedence over a regular module if the
    meta module occurs in an earlier directory in $MODULEPATH
  * Lmod output only "fills" when the text is more than one line
    or it is wider than the current width.
  * Embed the TCL interpreter in Lmod when a site allows TCL files
  * "module reset" resets $MODULEPATH to be the system $MODULEPATH
  * Improved tracing of module loads/unloads when --trace is given.
  * Allow MODULERCFILE to be a colon separated list.
- Set --with-fastTCLInterp=no, because this option is not supported
  with TCL 8.6
* Mon Mar 11 2019 Ana Guerrero Lopez <aguerrero@suse.com>
- Remove flavor 'doc-man' building a package only with the lmod manpage
  and move the manpage to lua-lmod.
- Remove the Recommends on lua-lmod-man and add a Provides instead.
- Update the Group tag for lua-lmod-doc to Documentation/Other because
  Documentation/PDF doesn't exist and make the package noarch.
* Wed Feb 13 2019 Jan Engelhardt <jengelh@inai.de>
- Declare bash-specific nature of build recipe.
* Fri Jan 25 2019 eich@suse.com
- Update to 7.8.15:
  * issue #379: Extra space required for shell function definitions
    under bash
  * issue #380: Change DependencyCk mode from load to dependencyCk,
    sType and tcl_mode remain load.
  * Fixed problem with unbound variable __lmod_sh_dbg in module shell
    function definition
  * Add unload state to tracing.
  * Define MCP and mcp earlier in lmod main() so that errors/warning
    found in SitePackage work.
  * issue #383: Use LUA_PATH to evaluate Version.lua instead of
    depending on ./?.lua to be LUA_PATH.
  * Added mgrload function and documentation
  * Fixed unbound variable in bash.in.
  * Fixed bug when ~/.lmod.d/cache was read only.
  * Fixed quote rules for Python, R and CMAKE.
  * issue #390: Added a message when find first rules are used to set
    defaults when NVV is found in both avail and tracing.
  * issue #389: Honor newlines and leading spaces in Nag messages.
  * Allow MODULERCFILE to be a colon separated list.
  * issue #391: Only process the family stack when in the modulefile
    that requested it.
  * Allow MODULERCFILE to be a colon separated list with the priority
    be left to right instead of right to left.
  * Added cc test case for issues with choosing the correct module
    when doing reloadAll()
  * issue #394: Only reload modules when the userName has remained the
    same in mt.
  * Add Lmod version report to --trace output.
  * issue #394: use mname = MName:new("load",mt:userName(sn)) to get
    loadable file
    contrib/tracking_module_usage python scripts have been updated to
    support python2 and python3
- Fix shbang line in scripts.
* Fri Aug 17 2018 eich@suse.com
- Update to 7.8.1:
  * Fixed typo in myGlobals.lua about assigning LMOD_DUPLICATE_PATHS
  * Fixed TARG_TITLE_BAR_PAREN to always have a value, needed for tcsh.
  * Added LMOD_SETTARG_TITLE_BAR=yes to turn on the title bar.
  * Changed from sn-version to sn/version in title bar.
  * Changed the initialization of LMOD_SETTARG_CMD in bash.in and csh.in.
    It is defined to be `:' iff it is undefined.  This allows settarg to work
    in sub-shells.
  * Use spider cache for "module --terse avail" when LMOD_CACHED_LOADS=yes
  * Fix bug with LMOD_SETTARG_CMD and csh.
  * Turn off LMOD_REDIRECT for tcsh
    Settarg now supports C/N/V and N/V/V module layouts.
  * Fixed a bug where sometimes a compiler-mpi dependent module wouldn't
    be found when it should.
  * Fixed issue #321 Changed LMOD_TARGPATHLOC to LMOD_SETTARG_TARG_PATH_LOCATION
    changed LMOD_FULL_SETTARG_SUPPORT to LMOD_SETTARG_FULL_SUPPORT. (Lmod supports both)
  * Fixed issue #322 where non-existant directory would cause problems
  * Fix bug in settarg module for csh.
  * Fix bug in Csh.lua where semicolons inside an alias were removed.  Only remove the
    trailing semicolon.
  * Generate an LmodError() if the cachefile is broken.
  * Do not convert /foo/bar/../baz to /foo/baz.  Leave .. in paths. Fixes issue #324
  * The admin.list (aka, nag mesages) supports Lua regex's.  Responds to issue #326
  * The admin.list now supports multiple targets for the same message (issue #326)
  * Use full path_regularize() on all TCL program files.  Having paths like /a/b/../d
    caused problems for some users when interacting with TCL.
  * Do not look for lua_json.  Just use the one that comes with Lmod.
  * Fix sh_to_modulefile correctly handle bad options (issue #332)
  * Allow pushenv("FOO",false) to clear "FOO" (issue #331)
  * Always use ref counting for MODULEPATH.
  * Change the C-shell output to not use quotes and instead use back slashes to
    quote special characters like $.
  * Better filtering for c-shell output testing
  * Fix bug in sh_to_modulefile
  * Remove definition of SHOST from bash.in.  Recompute it in settarg module.
  * Support relative symlink when trying to find cmd_dir
  * Now get modify time correctly from SpiderCache timestamp file.
  * Issue #346: do not use "ls" to get the list of directories when dealing with .modulepath
  * Issue #347: Just skip parsing "whole" if it is not a string (settarg)
  * Issue #348: Do not double the colon when the original was a single colon
  * Change ml so that ml av --terse is an error.
  * Making the settarg and lmod modulefiles be installed versionless.
  * Issue #353: Fix bug in cshrc.in end -> endif
  * Issue #352: Allow sites to control the prefix completely.
  * luaposix 34.0.4-1 wants to use setfenv() which only exists in Lua 5.1 and not in Lua 5.2+
    so Lmod now requires("posix") outside of strict.
  * Build lua-term in the correct location when --with-siteControlPrefix=yes
  * issue #347: Remove ./?.lua, ./?/init.lua from LUA_PATH and ./?.so from LUA_CPATH
  * issue #357: Add missing semicolons in settarg.version.lua
  * Fixed bug with lib directories not being readable.
  * issue #355: Make LMOD_RC support a colon separated list of possible lmodrc.lua files
  * Make bash, zsh and csh form LMOD_PKG to use <prefix>/lmod/lmod instead of
    <prefix>/lmod/<lmod_version> when allowing sites to completely control prefix (issue #352)
  * issue #359: Lmod can now use the internal version of lfs for installation.
  * issue #361: Support make -j install added.
  * issue #362: Trying to fix problem with RPM builds of Lmod at UGENT.
  * issue #358: Improved error msg when there is a syntax error in a modulefile.
  * issue #365, #366: Fix typo in Makefile about pkgs.
  * Modify end2end test to use build-in lua pkgs only.
  * issue #370: Allow for exact match with fn and fullName w/o regex pattern matching
    added %% quoting for '-' in docs.
  * Support for making lmod silence shell debug output (when doing set -xv for bash or zsh)
    The command "make world_update" now marks the latest release as the latest release at
  github.com/TACC/Lmod
  * The new module command now returns the status from the eval of the lmod command
  * Block .version.version and .modulerc.version files from being included in DirTree
  * Bash like shells now output without double quotes.
  * Fix fish shell output for path and infopath. Fix shell function output for zsh/bash
  * issue #374: convert ~ to $HOME internally.  This allows C-shell users to use ~
    inside a modulefile and have it work when unloading.
  * issue #375: Support for is-loaded and is-avail added.
  * Do not convert LMOD_PKG from /opt/apps/lmod/7.7.35 to /opt/apps/lmod/lmod if the link exists.
  * When building reverseMap also take abspath(path) and store it if different.
  * Now make startup scripts (profile.in, cshrc.in, profile.fish.in) use PKGV instead of PKG so
    that the pre-install create $VERSION files. The install target will convert them to PKG.
  * Check for "g" tools like gbasename, gexpr as well as the regular basename, expr etc.
  * General support for the modulerc files to be written in lua. They have a .lua extension.
  * Bug fix for 7.7.38 where it did not work for Lua 5.1
* Fri Aug 17 2018 eich@suse.com
- Change %%license to a %%my_license macro to be able to
  build for the HPC module on SLE-12.
* Fri Aug 17 2018 eich@suse.com
- Move doc and man page building into separate flavors.
* Wed Apr 18 2018 eich@suse.com
- use license macro for License file.
* Wed Apr 18 2018 jengelh@inai.de
- Replace %%__ type macro indirections.
- Update RPM groups, summaries, find|xargs commands.
* Wed Apr 18 2018 eich@suse.com
- Avoid conflicting script snippets from 'Modules' and 'lua-lmod'
  in /etc/profiles.d by making sure that both packages cannot be
  installed simultaneously (boo#1089970).
* Mon Oct 16 2017 eich@suse.com
- Doc-Ugly-workaround-for-bug-in-Sphinx.patch
  On SLE-12 and Leap 42.x Sphinx generates an incorrect tex file.
  This patch adds ugly code to the documentation Makefile to patch
  it up and work around this problem.
* Tue Oct 10 2017 eich@suse.com
- Make lua-lmod Arch-dependent: it hard codes the search path to
  .so plugins used by other Lua packages (boo#1061205).
* Fri Oct  6 2017 eich@suse.com
- Update to 7.6:
    1. Support for disable <collection_name>
    2. A marked default is honored even if it is hidden
    3. Support for depends_on() as a better way to handle module dependencies.
  * Lmod 7.5:
    1. Added -T, --trace option to report restore, load, unloads and spider.
    2. Report both global and version aliases with module --terse
    Add Global Aliases output to module avail if they exist.
    3. Support for isVisibleHook (Thanks @wpoely86!) to control whether
    a module is hidden or not.
    4. Support for "spider -o spider-json" to set the key "hidden"
    to true or false for each module.
    5. Setting LMOD_EXACT_MATCH=yes also turns off the display of (D) with
    avail.
    6. CMake "shell" added.
    7. Added feature that LMOD_TMOD_FIND_FIRST.  A site can decide to force
    FIND_FIRST instead FIND_BEST for NV module layouts.
    Bug Fixes:
    1. Fix bug where Lmod would be unable to load a module where NV and
    NVV module layouts were mixed.
    2. Fix bug where LMOD_CASE_INDEPENDENT_SORTING=yes wasn't case
    independent when using avail hook.
  * Lmod 7.4:
    1. Using built-in luafilesystem if system version doesn't exist or < 1.6.2
    2. Support for setting LMOD_SYSHOST with configure.
    3. Sites or users can use italic instead of dim for hidden modules
    4. Detailed spider output reports all dependencies hidden or not.
    5. Support for fish shell
    6. Move almost all configuration variables from profile.in to bash.in and
    similarly for tcsh.
    Bug Fixes:
    1. Fixed bug that caused LMOD env vars to be lower cased.
    2. Fixed bug where tcsh/csh exit status was not returned.
    3. bash and zsh tab completions works when LMOD_REDIRECT is yes.
    4. Can now conflict with a version.
    5. Fixed bug with addto a:b:c
    6. Fixed bugs in computeHashSum, generating softwarePage.
  * Lmod 7.3:
    1. The isloaded() function has been repaired.
    2. Updated French, German and Spanish translations.
    3. Two error message related to missing modules are now available for
    translations.
  * Lmod 7.2.1:
    1. A test suite for testing the Lmod installation has been added. See
    https://github.com/rtmclay/Lmod_test_suite for details.
    2. Added support for localization of errors and warnings and messages.
    3. Language Translations complete: ES, Partial: FR, ZH, DE
    4. Introduced "errWarnMsgHook" to take advantage of the new message
    handling.
    Bug Fixes:
    1. Several bug fixes related to Spider Cache and LMOD_CACHED_LOADS=1
    2. Repaired zsh tab completion.
    3. Minimize the output of Lmod's BASH_ENV when debugging Bash shell
    scripts.
    4. Allow colons as well as spaces for the path used in the addto command.
    5. Handles module directories that are empty or bad symlink or a .version
    file only.
    6. Fix bug in module describe.
  * Lmod 7.1:
    1. The commands "module --show_hidden avail" and "module --show_hidden"
    list now show "hidden" modules with the (H) property.  Also they are
    displayed as dim.  This works better on black backgrounds.
    2. Added the command "module --config_json" to generate a json output of
    Lmod's configuration.
    3. Add support for env. var. LMOD_SITE_NAME to set a site's name.  This is
    also a configure option.
    Bug Fixes:
    1. Hidden module now will not be marked as default.
    2. Now check permission of a directory before trying to open it.
    3. Lmod now does not pollute the configure time value of LD_LIBRARY_PATH
    and LD_PRELOAD into the users env.
    4. Lmod now handles illegal values of $TERM.
  * Lmod 7.0:
    1. This version support N/V/V. (e.g. fftw/64/3.3.4).  Put a .version file
    in with the "64" directory to tell Lmod where the version starts.
    2. Marking a default in the MODULERC is now supported.
    3. User ~/.modulerc has priority over system MODULERC.
    4. System MODULERC  has priority over marking a default in the module
    tree.
    5. Installed Modules can be hidden by "hide-version foo/3.2.1" in any
    modulerc file.
    6. The system spider cache has changed.  Please update your scripts to
    build spiderT.lua instead of moduleT.lua
  * Lmod 6.6:
    1. Now uses the value of LD_PRELOAD and LD_LIBRARY_PATH found at configure
    time to run all TCL progams.
    2. Now uses a custom _module_dir function for tab completion in bash for
    module use path<TAB>. Thanks to Pieter Neerincx!
    3. Support for LMOD_FAMILY_<name>_VERSION added.
    4. If ~/.lmod.d/.cache/invalidated exists then the user cache file(s) are
    ignored. When generating a user cache file ~/.lmod.d/.cache/invalidated
    is deleted.
    Bug Fixes:
    1. Correctly merges spider cache location where there are multiple
    lmodrc.lua files.
    2. Remove leading and trailing blanks for names in setenv, pushenv,
    prepend_path, etc.
    3. ml now generates error for unknown argument that start with a double
    minus. (e.g. ml --vers)
    4. pushenv("name","") fixed when unloading module.
    5. Make sure to regularize MODULEPATH when ingesting it for the first
    time.
- lmod.consulting.patch replaced by:
  Messages-Remove-message-about-creating-a-consulting-ticket.patch.
- lmod.site.patch:
  Removed: The site name is now provided by the env variable LMOD_SITE_NAME.
  (FATE#324199).
* Thu Oct  5 2017 eich@suse.com
- Fix build for Leap, SLE-12 and SLE-15.
- Remove _service file: the service can be run with
  'osc service run download_files' as well.
* Tue Sep  5 2017 eich@suse.com
- Change group of documentation package to Documentation/Other.
* Mon Aug 14 2017 eich@suse.com
- Fix group of doc package.
- Change BuildRequires from ohpc to ohpc-macros.
* Thu Aug 10 2017 eich@suse.com
- Fix build: add buildrequires for texlive-latexmk, texlive-makeindex and
    texlive-varwidth.
* Thu Aug 10 2017 eich@suse.com
- Prepare for suse default settings (bsc#1053237).
* Mon Jun 26 2017 dmueller@suse.com
- correct buildrequires for building on Leap 42.3 and on SLE15+
* Fri Apr 28 2017 eich@suse.com
- Add profile files for bash and csh (bsc#1048964).
* Fri Apr  7 2017 eich@suse.com
- Build and package man page and other documentation, create a separate
  package for additional documentation (bsc#1032970).
* Thu Feb 16 2017 jengelh@inai.de
- Replace redundant %%__ macro indirections
* Sat Nov 12 2016 eich@suse.com
  * Updated to version 6.5.11:
  - All the Lmod programs now resolve any symlinks to the
  actual program before adding to the Lua's package.path
  and package.cpath.
  - Contrib patch: Extend msgHook to LmodError and LmodWarning
  - Now using travis for CI and testing.
  - Configure time option to have Lmod check for magic TCL string in
  modulefiles (#%%Module)
  - Lmod now uses a regular expression to match user commands
  to internal commands. For example "av", "ava" or "available"
  will match "avail"
  - Lmod now uses the values of LUA_PATH and LUA_CPATH at
  configuration time.  This way Lmod is safe from user changes
  to these important Lua values.
  - Updated documentation at lmod.readthedocs.org
  - Support for generating xalt_rmapT.json used by XALT.
  - Fixed bug with upcase characters in version file.
  - It is now possible to configure Lmod to use the spider cache
  when loading (--with-cachedLoads=yes or
  export LMOD_CACHED_LOADS=1 to activate). This is off by
  default. Sites that use this will have to keep their spider
  caches up-to-date or user will not be able to load modules
  not in the cache.
- It is now possible to configure Lmod to use Legacy Version
  ordering ( --with-legacyOrdering=yes or export
  LMOD_LEGACY_VERSION_ORDERING=1). With legacy ordering 9.0
  is "newer" than 10.0. This is the ordering that Tmod uses.
- Lmod will print admin message (a.k.a nag messages) when
  doing module whatis <foo> or module help <foo>.  In other
  words if a nag message would appear with module load <foo>
  then it will also appear when using whatis or help.
- Many improvement in the generation of the lmod database for
  module tracking.
- Numerous bug fixes.
* Mon Oct 17 2016 eich@suse.com
- Setting 'download_files' service to mode='localonly'
  and adding source tarball. (Required for Factory).
* Wed Oct 12 2016 eich@suse.com
- Initial version of Lmod: 6.0.24
