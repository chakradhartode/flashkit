## g11 - rootless reliability and plugin installer hardening

- Extend the rootless `termux-adb` / `termux-fastboot` backend to the optional text menu as well as the GUI.
- Fix fastbootd detection and improve rootless diagnostics; document that polling uses the selected backend.
- Scope the rootless USB repository signing key to its own APT source and correctly normalize armored key files.
- Reject invalid, wrong-package, split-only, corrupt, or Android-incompatible Termux plugin APKs before opening Android's package installer.

# FlashKit changelog

## g10 - rootless Termux USB support and safer plugin installs
- Root is now optional. Rooted devices keep the stock `adb` / `fastboot` path; non-rooted devices use `termux-adb` / `termux-fastboot` through Termux:API USB permissions.
- Installer configures the rootless USB repository with `curl` and validates its OpenPGP key before adding it.
- Termux:API is installed before Termux:GUI so the rootless USB path is available as early as possible.
- Removed the unnecessary `termux-gui-package` apt install; FlashKit needs the Android Termux:GUI app and its Python binding, not that optional demo bundle.
- Plugin downloads are checked for APK archive integrity, package ID, split-package status, and minimum Android version before the Android installer is opened.
- Doctor, connection repair, device detection, file browsing, console and job execution now follow the selected root/rootless backend.


The app is at **g9**. Work on the repo, the installer and the `flashkit` command since then did not change the app's version, so it is listed together here.

## Since g9 (repo, installer and the `flashkit` command)
- Fixed a CI test that checked the README for its pre-publish placeholder text, so it failed on every repo that had actually been published.
- **Repo look:** new README with banner, badges, icons and a 3-step install; a user guide (`docs/GUIDE.md`); issue templates; a Material 3 Expressive author card with Chakradhar Tode branding.
- **FlashKit menu:** `flashkit` opens a menu - Start FlashKit, Run manually, Update, Check/install plugins, Doctor, autostart, Uninstall. `start flashkit` and `flashkit start` open the app directly, and there is a *FlashKit* entry for the Termux:Widget home-screen widget.
- **Uninstall:** `flashkit uninstall` removes FlashKit and asks what to delete; `-y` removes everything - the commands, settings, app files and the Termux:GUI / Termux:API apps.
- **Plugin installer:** finds installed plugins through root, never overwrites a working one, tries the next source if Android refuses a download, and has a no-root path (Android's own installer opens). With root it also allows "Display over other apps" for you.
- **After a restart:** if Android restarts Termux while a plugin installs, the next session opens the FlashKit menu once by itself.
- **Fixes:** a crash caused by an old root-owned install log; `flashkit check`.

## g9 - GitHub install
- `git clone` + `install.sh` sets up everything; Termux:GUI / Termux:API are chosen to match your Termux's signature.
- `flashkit update`, `flashkit plugins`, `flashkit doctor`, `tools/publish.sh`.
- **App:** one persistent root shell instead of a new `su` every few seconds, calmer device checks (and an off switch), a lighter file manager, **Quit completely**.

## App history
- **g8** - Storage tab: look inside zips/tars, extract all or selected, edit zips in place, compress, copy/move/rename/delete.
- **g7** - Cancel stops the whole job; live install log while sideloading.
- **g6 and earlier** - icon UI, GSI in 3 stages, USB mode detection (BROM / EDL / fastbootd), adb/fastboot repair, recovery black-screen fix, job output screen, file browser and console.
