#
# spec file for package pcsc-lite
#
# Copyright (c) 2020 SUSE LLC
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


#Compat macro for new _fillupdir macro introduced in Nov 2017
%if ! %{defined _fillupdir}
  %define _fillupdir /var/adm/fillup-templates
%endif

# FIXME: Maybe we should use /usr/lib/pcsc/drivers as others do:
%define ifddir %{_libdir}/readers
%define PKG_USER	scard
%define PKG_GROUP	scard
Name:           pcsc-lite
Version:        1.8.10
Release:        0
Summary:        PC/SC Smart Cards Library
License:        BSD-3-Clause AND GPL-3.0-or-later
Group:          Productivity/Security
URL:            https://pcsclite.apdu.fr/
Source:         %{name}-%{version}.tar.bz2
Source1:        %{name}.sysconfig
Source6:        pcsc-lite-reader-conf
BuildRequires:  gcc
BuildRequires:  libtool
BuildRequires:  pkgconfig
BuildRequires:  readline-devel
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  autoconf
BuildRequires:  autoconf-archive
BuildRequires:  flex
Requires:       libpcsclite1 = %{version}
#Requires(post): %fillup_prereq
#Requires(pre):  shadow
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  polkit-devel
BuildRequires:  polkit
#BuildRequires:  systemd-rpm-macros
BuildRequires:  pkgconfig(libudev)
%{?systemd_requires}

%description
PC/SC Lite provides a Windows SCard interface in a small form factor
for communication with smart cards and readers.

Security aware people should read the SECURITY file for possible
vulnerabilities of pcsclite and how to fix them. For information on how
to install drivers please read the DRIVERS file.

Memory cards will be supported through the MCT specification, which is
an APDU like manner sent normally through the SCardTransmit() function.
This functionality is exercised in the driver.

%package -n libpcsclite1
Summary:        PC/SC Smart Card Library
License:        BSD-3-Clause
Group:          System/Libraries
Recommends:     pcsc-lite >= %{version}

%description -n libpcsclite1
PC/SC Lite provides a Windows SCard interface in a small form factor
for communication with smart cards and readers.

Security aware people should read the SECURITY file for possible
vulnerabilities of pcsclite and how to fix them. For information on how
to install drivers please read the DRIVERS file.

Memory cards will be supported through the MCT specification, which is
an APDU like manner sent normally through the SCardTransmit() function.
This functionality is exercised in the driver.

%package -n libpcscspy0
Summary:        PC/SC Smart Card Library
License:        GPL-3.0-or-later
Group:          System/Libraries

%description -n libpcscspy0
Supporting library for the PC/SC spy tool.

%package devel
Summary:        Development package for the MUSCLE project SmartCards library
License:        BSD-3-Clause AND GPL-3.0-or-later
Group:          Development/Libraries/C and C++
Requires:       %{name} = %{version}
Requires:       glibc-devel
Requires:       libpcsclite1 = %{version}
Requires:       libpcscspy0 = %{version}

%description devel
This package contains the development files for pcsc-lite. It allows to
compile plugins for the pcsc-lite package.

%prep
%setup -q -n %{name}-%{version}/PCSC
#%patch0 -p1
#%patch1 -p1
cp -a %{SOURCE1} %{SOURCE6} .

%build
%reconfigure \
	--disable-silent-rules \
	--docdir=%{_docdir}/%{name} \
	--enable-usbdropdir=%{ifddir} \
	--with-systemdsystemunitdir=%{_unitdir} \
	--enable-polkit \
	--enable-filter \
	--disable-static
%make_build

%install
%make_install
mkdir -p %{buildroot}%{ifddir}
mkdir -p %{buildroot}%{_sysconfdir}/reader.conf.d/
sed s:@ifddir@:%{ifddir}: <pcsc-lite-reader-conf >%{buildroot}%{_sysconfdir}/reader.conf.d/reader.conf
ln -s %{_sbindir}/service %{buildroot}%{_sbindir}/rcpcscd
mkdir -p %{buildroot}%{_fillupdir}
cp %{name}.sysconfig %{buildroot}%{_fillupdir}/sysconfig.pcscd
mkdir -p %{buildroot}%{_docdir}/%{name}
cp -a AUTHORS ChangeLog COPYING HELP NEWS README SECURITY TODO %{buildroot}%{_docdir}/%{name}

# To install service on SFOS
mkdir -p %{buildroot}/%{_unitdir}/multi-user.target.wants/
mkdir -p %{buildroot}/%{_unitdir}/socket.target.wants/

# install -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/pcscd.service
ln -s ../pcscd.service %{buildroot}/%{_unitdir}/multi-user.target.wants/pcscd.service
ln -s ../pcscd.socket %{buildroot}/%{_unitdir}/socket.target.wants/pcscd.socket
# Remove useless la files
find %{buildroot} -type f -name "*.la" -delete -print

%pre
getent group %{PKG_GROUP} >/dev/null || groupadd -r %{PKG_GROUP}
getent passwd %{PKG_USER} >/dev/null || useradd -r -g %{PKG_GROUP} -s %{_sbindir}/nologin -c "Smart Card Reader" -d /run/pcscd %{PKG_USER}
# %service_add_pre pcscd.service pcscd.socket

%preun
if [ "$1" -eq 0 ]; then
systemctl stop pcscd.service || :
fi
%systemd_preun pcscd.socket pcscd.service
#%service_del_preun pcscd.service pcscd.socket

%post
%systemd_post pcscd.service pcscd.socket
#%fillup_only -n pcscd
/sbin/ldconfig
systemctl daemon-reload || :
systemctl reload-or-try-restart pcscd.service || :

%postun
/sbin/ldconfig
systemctl daemon-reload || :
%systemd_postun_with_restart pcscd.socket pcscd.service
#%service_del_postun pcscd.service pcscd.socket

%post -n libpcsclite1 -p /sbin/ldconfig

%postun -n libpcsclite1 -p /sbin/ldconfig

%post -n libpcscspy0 -p /sbin/ldconfig

%postun -n libpcscspy0 -p /sbin/ldconfig

%files
%defattr(-,root,root)
%docdir %{_docdir}/%{name}
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/AUTHORS
%{_docdir}/%{name}/COPYING
%{_docdir}/%{name}/HELP
%{_docdir}/%{name}/NEWS
%{_docdir}/%{name}/README
%{_docdir}/%{name}/README.DAEMON
%{_docdir}/%{name}/SECURITY
%{_docdir}/%{name}/TODO
%doc %{_mandir}/man?/*.*
%{_sbindir}/*
%dir %{_sysconfdir}/reader.conf.d
%config(noreplace) %{_sysconfdir}/reader.conf.d/reader.conf
%{ifddir}
%{_unitdir}/*
%{_fillupdir}/sysconfig.pcscd
# libpcsclite.so should stay in the main package (#732911). Third party packages may need it for dlopen().
%{_libdir}/libpcsclite.so

%files -n libpcsclite1
%defattr(-,root,root)
%{_libdir}/libpcsclite.so.*

%files -n libpcscspy0
%defattr(-,root,root)
%{_libdir}/libpcscspy.so.*

%files devel
%defattr(-,root,root)
%docdir %{_docdir}/%{name}
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/Change*
%{_includedir}/*
%{_libdir}/pkgconfig/*.pc
%{_libdir}/*.so
%{_bindir}/*
# libpcsclite.so should stay in the main package (#732911). Third party packages may need it for dlopen().
%exclude %{_libdir}/libpcsclite.so

%changelog
