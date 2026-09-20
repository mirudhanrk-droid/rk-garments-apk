[app]

# Application name
title = RK Garments Salary Management

# Package name - lowercase, no spaces
package.name = rkgarments

# Package domain
package.domain = org.rkgarments

# Python source directory
source.dir = .

# Python file extensions and data files
source.include_exts = py,json,png,jpg,jpeg,kv

# Version
version = 1.0

# Required Python/Android packages
requirements = python3,kivy

# Screen orientation
orientation = portrait

# Full screen
fullscreen = 0

# Android permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Android API settings
android.api = 35
android.minapi = 21

# Android architecture
android.archs = arm64-v8a

# Android application activity
android.entrypoint = org.kivy.android.PythonActivity

# Don't use a console window
android.add_src =

# Presplash
presplash.filename =

# Icon
icon.filename =

# Log level
log_level = 2


[buildozer]

# Build directory
build_dir = .buildozer

# APK output directory
bin_dir = bin

# Warn if running as root
warn_on_root = 1
