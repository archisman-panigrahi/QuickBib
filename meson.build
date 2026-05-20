project('quickbib', 'c', version : '0.8.1')

# Install python source files (copied as-is)
# Install the top-level entrypoint script that bootstraps the app (keeps
# quickbib.py at top-level as desired). The rest of the modules live in the
# `src` package which we install under share/quickbib/src so the launcher can
# add that to sys.path.
# Install the src package directory and LICENSE file into share/quickbib so the
# installed entrypoint `src/quickbib.py` can be executed by the launcher.
install_subdir('quickbib', install_dir: join_paths(get_option('datadir'), 'quickbib'))
install_data('LICENSE', install_dir: join_paths(get_option('datadir'), 'quickbib'))

# Launcher script installed to bindir with executable mode
install_data('bin/quickbib', install_dir: get_option('bindir'), install_mode: 'rwxr-xr-x')

# Desktop file
install_data('io.github.archisman_panigrahi.QuickBib.desktop', install_dir: join_paths(get_option('datadir'), 'applications'))

# AppStream / metainfo file
install_data('io.github.archisman_panigrahi.QuickBib.metainfo.xml',
             install_dir: join_paths(get_option('datadir'), 'metainfo'))

# Icons (hicolor theme layout)
#install_data('assets/icon/16x16/io.github.archisman_panigrahi.QuickBib.png',
#             install_dir: join_paths(get_option('datadir'), 'icons', 'hicolor', '16x16', 'apps'))
#install_data('assets/icon/32x32/io.github.archisman_panigrahi.QuickBib.png',
#             install_dir: join_paths(get_option('datadir'), 'icons', 'hicolor', '32x32', 'apps'))
#install_data('assets/icon/64x64/io.github.archisman_panigrahi.QuickBib.png',
#             install_dir: join_paths(get_option('datadir'), 'icons', 'hicolor', '64x64', 'apps'))
install_data('assets/icon/128x128/io.github.archisman_panigrahi.QuickBib.png',
             install_dir: join_paths(get_option('datadir'), 'icons', 'hicolor', '128x128', 'apps'))
install_data('assets/icon/scalable/io.github.archisman_panigrahi.QuickBib.svg',
             install_dir: join_paths(get_option('datadir'), 'icons', 'hicolor', 'scalable', 'apps'))

# Install README into the package documentation directory
install_data('README.md', install_dir: join_paths(get_option('datadir'), 'doc', 'quickbib'))
