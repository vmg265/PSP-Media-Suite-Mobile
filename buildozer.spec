[app]
# ── Identity ──────────────────────────────────────────────────────────────────
title           = PSP Media Suite
package.name    = pspmediasuite
package.domain  = com.vmg265
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas,txt
version         = 1.6

# ── Entry point ───────────────────────────────────────────────────────────────
# Buildozer looks for main.py by default

# ── Orientation ───────────────────────────────────────────────────────────────
orientation = portrait

# ── Requirements ─────────────────────────────────────────────────────────────
# List every Python dep + Kivy/KivyMD versions pinned for reproducibility.
requirements =
    python3,
    kivy==2.3.0,
    kivymd==1.2.0,
    pillow,
    requests,
    mutagen,
    yt-dlp,
    psutil,
    certifi,
    charset-normalizer,
    urllib3,
    idna

# ── Android permissions ───────────────────────────────────────────────────────
android.permissions =
    INTERNET,
    READ_EXTERNAL_STORAGE,
    WRITE_EXTERNAL_STORAGE,
    READ_MEDIA_AUDIO,
    READ_MEDIA_VIDEO,
    MANAGE_EXTERNAL_STORAGE

# ── Android API targets ───────────────────────────────────────────────────────
android.minapi        = 21
android.api           = 33
android.ndk           = 25b
android.ndk_api       = 21
android.archs         = arm64-v8a, armeabi-v7a

# ── Android build extras ──────────────────────────────────────────────────────
android.allow_backup         = False
android.accept_sdk_license   = True
android.gradle_dependencies  = com.google.android.material:material:1.9.0

# Force Material / dark-mode-aware theme in AndroidManifest
android.manifest_placeholders = appTheme:Theme.MaterialComponents.DayNight

# Extra files to bundle (ffmpeg binary must be placed in project root)
# Download a static arm64 ffmpeg binary from https://github.com/eugeneware/ffmpeg-static
# and rename it to "ffmpeg" before building.
source.include_patterns = ffmpeg, Icon.png, troubleshooter_box.txt

# ── Build output ──────────────────────────────────────────────────────────────
android.release_artifact = apk
# To build AAB for Play Store:
# android.release_artifact = aab

# ── Icons / splash ────────────────────────────────────────────────────────────
# Place a 512×512 PNG at ./Icon.png and a 1024×500 PNG at ./presplash.png
icon.filename       = %(source.dir)s/Icon.png
presplash.filename  = %(source.dir)s/presplash.png
presplash.color     = #121212

# ── Buildozer internals ───────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1
