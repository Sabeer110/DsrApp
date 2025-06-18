[app]
title = Daily Sales Report
package.name = dsrapp
package.domain = org.business
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# Humne Kivy, Pillow, aur reportlab, teeno ka version fix kar diya hai
requirements = python3,kivy==2.1.0,reportlab==3.6.13,Pillow==9.3.0

orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET
android.api = 33
android.minapi = 21

# YEH SABSE ZAROORI HAIN: Hum NDK aur Build Tools ka version khud bata rahe hain
android.ndk = 25b
android.build_tools_version = 33.0.0

android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
