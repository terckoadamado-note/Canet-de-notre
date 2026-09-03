[app]

title = Canet de notre
package.name = canetdenotre
package.domain = org.canetdenotre

source.dir = .
source.include_exts = py,png,jpg,jpeg,json,txt
source.exclude_dirs = .git,.github,.buildozer,bin,__pycache__,tests,reference

version = 1.0

requirements = python3,kivy

orientation = landscape
fullscreen = 0

android.api = 35
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.permissions = INTERNET

[buildozer]

log_level = 2
warn_on_root = 1
