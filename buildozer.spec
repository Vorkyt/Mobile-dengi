[app]
title           = Мой Бюджет
package.name    = mybudget
package.domain  = org.expense

source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,json

version         = 1.0.0
requirements    = python3,kivy==2.3.0,kivymd

orientation     = portrait
fullscreen      = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api     = 33
android.minapi  = 21
android.ndk     = 25b
android.sdk     = 33
android.ndk_api = 21
android.archs   = arm64-v8a

android.allow_backup = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
