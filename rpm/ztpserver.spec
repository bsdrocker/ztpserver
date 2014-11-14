#################################
# Application specific settings #
#################################
%define app_summary         "Arista Zero Touch Provisioning Server for Arista EOS Devices."
%define app_user            ztpserver
%{!?python2_sitelib: %global python2_sitelib /usr/lib/python2.7/site-packages }
%if 0%{?rhel} == 6
%define httpd_dir           /opt/rh/httpd24/root/etc/httpd/conf.d
%define app_virtualenv_dir  /opt/ztpsrv_env
%define ztps_bin            /bin
%define install_dir         /
%global python2_sitelib     /lib/python2.7/site-packages
%global python2_sitearch    /lib64/python2.7/site-packages
%else
%define httpd_dir           /etc/httpd/conf.d
%define app_virtualenv_dir  /
%define ztps_bin            /usr/bin
%define install_dir         $RPM_BUILD_DIR
%endif

Name:    ztpserver
Version: BLANK
Release: 2%{?dist}
Summary: %{app_summary}

Group:    Network
License:  BSD-3
URL:      %{app_url}
Source0:  %{name}.tgz
Source1:  %{name}-wsgi.conf

### Don't allow rpmbuild to modify dependencies 
AutoReqProv: no

BuildRequires: python-pip

%if 0%{?rhel} == 6
BuildRequires: python27
BuildRequires: python-virtualenv
BuildRequires: python27-python-virtualenv
BuildRequires: python27-python-setuptools
%else
BuildRequires: python >= 2.7
BuildRequires: python < 3
BuildRequires: python-setuptools
%endif

%if 0%{?rhel} == 6
Requires: python27
Requires: python-virtualenv
Requires: python27-python-virtualenv
Requires: httpd24
Requires: python27-mod_wsgi
%else
Requires: python >= 2.7
Requires: python < 3
Requires: httpd
Requires: mod_wsgi
%endif

Requires(pre): shadow-utils

BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-%{id -un}

%description
ZTPServer provides a bootstrap environment for Arista EOS based products.
ZTPserver interacts with the ZeroTouch Provisioning (ZTP) mode of Arista EOS.
The default ZTP start up mode triggers an unprovisioned Arista EOS nodes to
enter a bootstrap ready state if a valid configuration file is not already
present on the internal flash storage.

ZTPServer provides a number of configurable bootstrap operation workflows that
extend beyond simply loading an configuration and boot image. It provides the
ability to define the target node through the introduction of definitions and
templates that call pre-built actions and statically defined or dynamically
generated attributes. The attributes and actions can also be extended to provide
custom functionality that are specific to a given implementation. ZTPServer also
provides a topology validation engine with a simple syntax to express LLDP 
neighbor adjacencies. It is written mostly in Python and leverages standard 
protocols like DHCP and DHCP options for boot functions, HTTP for 
bi-directional transport, and XMPP and syslog for logging. Most of the files 
that the user interacts with are YAML based.

%prep
%setup -q -c -n %{name}-%{version}

%build
%if 0%{?rhel} == 6
## Prepare virtualenv w/ python27 for build of ztpserver source
export X_SCLS=python27
source /opt/rh/python27/enable
virtualenv-2.7 -v --system-site-packages $RPM_BUILD_DIR%{app_virtualenv_dir}
source $RPM_BUILD_DIR%{app_virtualenv_dir}/bin/activate
%endif

#pip install setuptools --upgrade

cd ztpserver
python setup.py build

python setup.py install --root=%{install_dir}

# clean-up gitsrc dir after install:
cd ..
rm -rf ztpserver

%install
# Move necessary file from RPM_BUILD_DIR into RPM_BUILD_ROOT:
%if 0%{?rhel} == 6
mkdir -p $RPM_BUILD_ROOT%{app_virtualenv_dir}
cp -rp $RPM_BUILD_DIR%{app_virtualenv_dir}/* $RPM_BUILD_ROOT%{app_virtualenv_dir}
%else
mkdir -p $RPM_BUILD_ROOT%{python2_sitelib}/
cp -rp $RPM_BUILD_DIR%{python2_sitelib}/%{name}-%{version}*.egg* $RPM_BUILD_ROOT%{python2_sitelib}/

mkdir -p $RPM_BUILD_ROOT%{ztps_bin}
cp -rp $RPM_BUILD_DIR%{ztps_bin}/ztps $RPM_BUILD_ROOT%{ztps_bin}/ztps

mkdir -p $RPM_BUILD_ROOT/{etc,usr/share}
cp -rp $RPM_BUILD_DIR/etc $RPM_BUILD_ROOT
cp -rp $RPM_BUILD_DIR/usr/share/ztpserver $RPM_BUILD_ROOT/usr/share/
%endif
mkdir -p $RPM_BUILD_ROOT%{httpd_dir}
cp -rp %{SOURCE1} $RPM_BUILD_ROOT%{httpd_dir}/%{name}-wsgi.conf


%pre
getent group %{app_user} > /dev/null || groupadd -r %{app_user}
%if 0%{?rhel} == 6
getent passwd %{app_user} > /dev/null || \
  useradd -m -g %{app_user} -d /%{app_virtualenv_dir} -s /bin/bash \
  -c "%{name} - Server" %{app_user}
%else
getent passwd %{app_user} > /dev/null || \
  useradd -m -g %{app_user} -d /home/%{app_user} -s /bin/bash \
  -c "%{name} - Server" %{app_user}
%endif
exit 0

%posttrans


%post
%if 0%{?rhel} == 6
ln -s %{app_virtualenv_dir}/usr/share/ztpserver /usr/share/
ln -s %{app_virtualenv_dir}/etc/ztpserver /etc/
%endif
chcon -Rv --type=httpd_sys_content_t %{app_virtualenv_dir}/usr/share/ztpserver

%preun
# $1 --> if 0, then it is a deinstall
# $1 --> if 1, then it is an upgrade


%postun
# $1 --> if 0, then it is a deinstall
# $1 --> if 1, then it is an upgrade
#if [ $1 -eq 0 ]; then
#    userdel -r %{app_user}
#    #groupdel %{app_user}
#fi
# remove symlink relics:
rm /usr/share/ztpserver
rm /etc/ztpserver


%files
# all the files to be included in this RPM:
%defattr(-,root,root,)
%if 0%{?rhel} == 6
%{app_virtualenv_dir}
%else
%{python2_sitelib}/%{name}-%{version}*.egg*
%endif
%{app_virtualenv_dir}%{ztps_bin}/ztps
%config(noreplace) %{app_virtualenv_dir}/etc/ztpserver/ztpserver.conf
%attr(0755,%{app_user},root) %{app_virtualenv_dir}/etc/ztpserver/ztpserver.wsgi
%attr(0755,%{app_user},root) %{app_virtualenv_dir}/usr/share/ztpserver/*
%attr(0755,%{app_user},root) %{httpd_dir}/%{name}-wsgi.conf

%clean
rm -rf $RPM_BUILD_ROOT


%changelog
* Mon Nov 03 2014 Arista Networks <eosplus-dev@arista.com> - 1.2.0-2
- Add logic to work with virtualenv installs versus standard installs
- For virtualenv installs, all python dependencies will be installed
- For standard installs, only ztpserver egg and /usr/share/ztpserver files are included (as well as config in /etc/ztpserver and /usr/bin/ztps)

* Tue Oct 28 2014 Arista Networks <eosplus-dev@arista.com> - 1.2.0-1
- Remove standalone ZTPServer functions from SPEC
- Remove ztpserver.init script
- Add dependencies for Software Collections httpd24 and python27-mod_wsgi
- Add SOURCE ztpserver-wsgi.conf which is placed in httpd24 conf.d directory
- Modify SELinux policy so that httpd can write to /usr/share/ztpserver

* Fri Oct 10 2014 tzhnape1 <peter.najdenik@swisscom.com> - 1.1.0-1
- Release 1 of ZTPserver RPM using virtualenv and python 27 from RH SCL.
TODO:
- sync git source from script and put all sources into tar archive
- source archive via prep
- [done] fix env declaration in ztps script in \install section before cleaning up --> see shebang fixes
- [done] cleanup specfile variables and put definitions for http proxy server in header
- [done] source scl env via enable script instead of declaring/exporting env variables manually
- [done] fix post install and uninstall sections
- [done] write changelog
- refactor spec/rpm part for integration with jenkings & puppet - "init.sh"
- handle selinux if necessary (virtualenv dir, sysconfdir, etc.)

* Wed Oct 8 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Fixed sed script to change environment path in activate script of vritualenv, which caused the rpm not to build anymore
- Some cleanup and recoding of specfile done.

* Mon Oct 6 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Changed the export of env variables for python 2.7 scl env to source the 'enable' script which does the same.
- Fixed shebangs with path variables in ztps set during build in setup/install section (buildroot pfad was used due to the build env being active while building)
- Fixed cleanup missing for symlinks at removal of the package

* Fri Sep 26 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Fixed \install section issue with virtualenv/shell env settings getting lost
- Tweaked packaging files list

* Wed Sep 3 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Fixed build/install section so it properly works with python-virtualenv
- Fixed install paths and files list
- Added symlinks to systemconfdir and usrdir for virtualenv for ease of access
- Fixed/added GitHub source (Gitlab requires authentication)

* Wed Aug 27 2014 tzhnape1 <peter.najdenik@swisscom.com>
- Initial release/build of ztpserver
