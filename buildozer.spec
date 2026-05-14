[app]
# Title of your application
title = PSP Media Suite

# Package name (no spaces)
package.name = pspmediasuite

# Package domain (needed for android packaging)
package.domain = org.vmg

# Source code where the main.py lives
source.dir = .

# Extensions of files to include
source.include_exts = py,png,jpg,kv,atlas

# The version of your application
version = 1.5

# Comma-separated list of requirements
# This is where you tell the builder to grab the Android ffmpeg and your UI libraries
requirements = python3,kivy,kivymd,yt-dlp,ffmpeg

# Path to your icon
icon.filename = Icon.png

# Android permissions necessary for downloading and moving media
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

[buildozer]
# Log level (2 = debug, useful if the GitHub Action fails)
log_level = 2
