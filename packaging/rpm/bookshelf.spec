Name:           bookshelf
Version:        1.1.0
Release:        1%{?dist}
Summary:        Personal library manager for GNOME

License:        GPL-3.0-or-later
URL:            https://github.com/farukylmz0550/bookshelf-desktop
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       gtk4 >= 4.10
Requires:       libadwaita >= 1.4
Requires:       python3 >= 3.11
Requires:       python3-gobject
Requires:       python3-cairo
Requires:       python3-matplotlib
Requires:       python3-openpyxl
Requires:       python3-keyring

%description
Book Shelf is a personal library manager for GNOME and Linux, built with
GTK4 + libadwaita. It manages books by ISBN with automatic metadata from
Open Library, tracks lending with borrowers and a trust score, follows
reading with status, dates and goals, and reports statistics with pie
charts. It can import and export Excel spreadsheets and contribute missing
books back to Open Library.

%prep
%autosetup -n %{name}-%{version}

%build

%install
install -d %{buildroot}/usr/lib/%{name} \
           %{buildroot}%{_bindir} \
           %{buildroot}%{_datadir}/applications \
           %{buildroot}%{_metainfodir} \
           %{buildroot}%{_datadir}/icons/hicolor/256x256/apps \
           %{buildroot}%{_datadir}/icons/hicolor/scalable/apps \
           %{buildroot}%{_datadir}/licenses/%{name}
cp -r src %{buildroot}/usr/lib/%{name}/src
cp -r assets %{buildroot}/usr/lib/%{name}/assets
rm -rf %{buildroot}/usr/lib/%{name}/assets/screenshots
install -m 644 VERSION %{buildroot}/usr/lib/%{name}/VERSION
install -m 644 LICENSE %{buildroot}%{_datadir}/licenses/%{name}/LICENSE
install -m 755 packaging/bookshelf-launcher %{buildroot}%{_bindir}/bookshelf
install -m 644 packaging/io.github.farukylmz0550.BookShelfLegacy.desktop \
           %{buildroot}%{_datadir}/applications/
install -m 644 packaging/io.github.farukylmz0550.BookShelfLegacy.metainfo.xml \
           %{buildroot}%{_metainfodir}/
install -m 644 assets/icons/hicolor/256x256/apps/io.github.farukylmz0550.BookShelfLegacy.png \
           %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/
install -m 644 assets/icons/hicolor/scalable/apps/io.github.farukylmz0550.BookShelfLegacy-symbolic.svg \
           %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

%files
/usr/lib/%{name}
%{_bindir}/bookshelf
%{_datadir}/applications/io.github.farukylmz0550.BookShelfLegacy.desktop
%{_metainfodir}/io.github.farukylmz0550.BookShelfLegacy.metainfo.xml
%{_datadir}/icons/hicolor/256x256/apps/io.github.farukylmz0550.BookShelfLegacy.png
%{_datadir}/icons/hicolor/scalable/apps/io.github.farukylmz0550.BookShelfLegacy-symbolic.svg
%{_datadir}/licenses/%{name}/LICENSE

%post
touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache -qtf %{_datadir}/icons/hicolor &>/dev/null || :

%postun
touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
gtk-update-icon-cache -qtf %{_datadir}/icons/hicolor &>/dev/null || :
