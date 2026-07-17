# RPM spec for ES-DE Frontend (EmulationStation Desktop Edition)
#
# Pinned upstream release:
#   Tag:     v3.4.1  (released 2026-04-10, latest stable at time of writing)
#   Tarball: https://gitlab.com/es-de/emulationstation-de/-/archive/v3.4.1/emulationstation-de-v3.4.1.tar.gz
#   SHA256:  58a45eb3f400a3b02d5b994407ba8c5f71807de3c2df571b7abdc21bc6e83be8
#            (also recorded in packaging/es-de/sources.sha256; the CI workflow
#            verifies the downloaded tarball against it before building)
#
# Upstream files consulted for the build requirements below (all at tag v3.4.1):
#   - CMakeLists.txt                     find_package() list for desktop Linux:
#                                        CURL, FFmpeg, FreeImage, Freetype, HarfBuzz,
#                                        ICU, Intl, Libgit2, Pugixml, SDL2, ALSA,
#                                        Bluez, OpenGL (GLVND)
#   - CMake/Packages/FindFFmpeg.cmake    pkg-config lookups: libavcodec, libavfilter,
#                                        libavformat, libavutil
#   - CMake/Packages/FindBluez.cmake     libbluetooth + bluetooth/bluetooth.h
#   - CMake/Packages/FindPoppler.cmake   pkg-config poppler + poppler-cpp, core
#                                        libpoppler and poppler-config.h
#   - es-pdf-converter/CMakeLists.txt    find_package(Poppler REQUIRED COMPONENTS cpp)
#   - external/CMakeLists.txt            LunaSVG and rlottie are vendored in the source
#                                        tree and built in-tree as static libraries
#   - locale/CMakeLists.txt              find_program(msgfmt) for message catalogs
#   - es-app/CMakeLists.txt              install layout and binary names (es-de,
#                                        es-pdf-convert, man page, desktop file, icons,
#                                        appdata, /usr/share/es-de data)
#   - INSTALL-DEV.md ("Building on Unix", Fedora section) — upstream's dnf package
#     list. NOTE: upstream suggests RPM Fusion's ffmpeg-devel there. We deliberately
#     deviate and build against stock Fedora's ffmpeg-free devel packages instead;
#     upstream's own FindFFmpeg.cmake only needs pkgconfig(libavcodec/avfilter/
#     avformat/avutil), which ffmpeg-free provides. No RPM Fusion required.
#
# Every BuildRequires below resolves from stock Fedora 42 repos. Verify with:
#   dnf repoquery --whatprovides 'pkgconfig(libavcodec)'   -> libavcodec-free-devel
#   dnf repoquery <name>                                   for the concrete names
#
# The pkgconfig() virtual provides are used for the FFmpeg libraries so the spec
# keeps working if Fedora ever renames the ffmpeg-free devel subpackages.

%global upstream_tag v%{version}

# Upstream's release build links with -s (strip), so there are no debug symbols
# to extract and debuginfo generation would fail with an empty file list.
%global debug_package %{nil}

Name:           es-de
Version:        3.4.1
Release:        1%{?dist}
Summary:        ES-DE Frontend (EmulationStation Desktop Edition), a game browsing frontend

# ES-DE itself is MIT on desktop Linux. Bundled LunaSVG and plutovg are MIT,
# bundled rlottie is MIT (with bundled components noted upstream in licenses/).
License:        MIT
URL:            https://es-de.org
Source0:        https://gitlab.com/es-de/emulationstation-de/-/archive/%{upstream_tag}/emulationstation-de-%{upstream_tag}.tar.gz

# Toolchain and build tools
BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  gettext
BuildRequires:  pkgconf-pkg-config
BuildRequires:  desktop-file-utils

# FFmpeg (stock Fedora ffmpeg-free; see header comment)
BuildRequires:  pkgconfig(libavcodec)
BuildRequires:  pkgconfig(libavfilter)
BuildRequires:  pkgconfig(libavformat)
BuildRequires:  pkgconfig(libavutil)
# Pulled in via libavfilter's pkg-config Requires chain; listed explicitly so
# the headers are guaranteed present.
BuildRequires:  pkgconfig(libswresample)
BuildRequires:  pkgconfig(libswscale)

# Remaining libraries, per the find_package() list in CMakeLists.txt
BuildRequires:  alsa-lib-devel
BuildRequires:  bluez-libs-devel
BuildRequires:  freeimage-devel
BuildRequires:  freetype-devel
BuildRequires:  harfbuzz-devel
BuildRequires:  libcurl-devel
BuildRequires:  libgit2-devel
BuildRequires:  libicu-devel
BuildRequires:  mesa-libGL-devel
BuildRequires:  poppler-cpp-devel
BuildRequires:  poppler-devel
BuildRequires:  pugixml-devel
BuildRequires:  SDL2-devel

# Owns the hicolor icon directory tree
Requires:       hicolor-icon-theme

# Built in-tree as static libraries (see external/CMakeLists.txt)
Provides:       bundled(lunasvg) = 3.5.0
Provides:       bundled(plutovg)
Provides:       bundled(rlottie) = 0.2
# Header-only libraries vendored under external/
Provides:       bundled(glm)
Provides:       bundled(rapidjson)
Provides:       bundled(utfcpp)
Provides:       bundled(cimg)

%description
ES-DE Frontend (formerly EmulationStation Desktop Edition) is a frontend for
browsing and launching games from your multi-platform collection. This package
is built from the pinned upstream release tarball against stock Fedora
libraries, including the ffmpeg-free FFmpeg build.

%prep
%autosetup -n emulationstation-de-%{upstream_tag}

%build
# APPLICATION_UPDATER is disabled because updates are delivered through the OS
# image / dnf, not by the application itself.
%cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DAPPLICATION_UPDATER=OFF
%cmake_build

%install
%cmake_install

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/org.es_de.frontend.desktop
# Sanity check: the binary must report the pinned version.
%{buildroot}%{_bindir}/es-de --version | grep -F 'ES-DE %{version}'

%files
%license LICENSE
%{_bindir}/es-de
%{_bindir}/es-pdf-convert
%{_mandir}/man6/es-de.6*
%{_datadir}/applications/org.es_de.frontend.desktop
%{_datadir}/pixmaps/org.es_de.frontend.svg
%{_datadir}/icons/hicolor/scalable/apps/org.es_de.frontend.svg
%{_datadir}/metainfo/org.es_de.frontend.appdata.xml
%{_datadir}/es-de/

%changelog
* Thu Jul 17 2026 tonttu CI <ci@tonttu> - 3.4.1-1
- Initial package, built from the upstream v3.4.1 release tarball
