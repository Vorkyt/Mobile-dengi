[app]
title           = Мой Бюджет
package.name    = mybudget
package.domain  = org.expense

source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,json

version         = 1.0.0
requirements    = python3,kivy

orientation     = portrait
fullscreen      = 0

android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.minapi  = 21
android.ndk     = 25b
android.sdk     = 33
android.archs   = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
