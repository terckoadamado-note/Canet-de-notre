[app]
title = Canet de notre
package.name = canetdenotre
package.domain = org.canetdenotre
source.dir = .
source.include_exts = py,png,jpg,jpeg,json,kv,atlas
version = 1.0.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/assets/icon.png
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.private_storage = True
android.allow_backup = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
