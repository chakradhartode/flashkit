"""Regression tests for FlashKit's no-root command selection and binary APK manifest validation."""
import os
import struct
import tempfile
import unittest
import zipfile
from unittest import mock

import flashkit_gui as gui
from tools import termux_plugins as plugins


def _utf8_len(n):
    if n < 0x80:
        return bytes([n])
    return bytes([0x80 | (n >> 8), n & 0xff])


def _binary_xml_manifest(package="com.termux.api", min_sdk=23, split=None):
    strings = ["manifest", "package", package, "uses-sdk", "minSdkVersion"]
    if split is not None:
        strings += ["split", split]
    pool_data = bytearray()
    offsets = []
    for value in strings:
        raw = value.encode("utf-8")
        offsets.append(len(pool_data))
        pool_data += _utf8_len(len(value)) + _utf8_len(len(raw)) + raw + b"\0"
    string_count = len(strings)
    strings_start = 28 + string_count * 4
    pool_size = strings_start + len(pool_data)
    pool = struct.pack("<HH6I", 0x0001, 28, pool_size, string_count, 0, 0x100, strings_start, 0)
    pool += b"".join(struct.pack("<I", x) for x in offsets) + pool_data

    idx = {v: i for i, v in enumerate(strings)}

    def start_tag(name, attrs):
        attr_start, attr_size = 20, 20
        size = 36 + len(attrs) * attr_size
        chunk = struct.pack("<HHIII", 0x0102, 16, size, 1, 0xffffffff)
        chunk += struct.pack("<IIHHHHHH", 0xffffffff, idx[name], attr_start, attr_size,
                             len(attrs), 0, 0, 0)
        for attr, raw_idx, data_type, data in attrs:
            chunk += struct.pack("<IIIHBBI", 0xffffffff, idx[attr], raw_idx, 8, 0, data_type, data)
        return chunk

    manifest_attrs = [("package", 0xffffffff, 0x03, idx[package])]
    if split is not None:
        manifest_attrs.append(("split", 0xffffffff, 0x03, idx[split]))
    chunks = pool + start_tag("manifest", manifest_attrs)
    chunks += start_tag("uses-sdk", [("minSdkVersion", 0xffffffff, 0x10, min_sdk)])
    total = 8 + len(chunks)
    return struct.pack("<HHI", 0x0003, 8, total) + chunks


class RootlessBackend(unittest.TestCase):
    def setUp(self):
        self.old_root = gui._ROOT_AVAILABLE
        gui._ROOT_AVAILABLE = False
        self.which = {
            "termux-adb": "/fake/bin/termux-adb",
            "termux-fastboot": "/fake/bin/termux-fastboot",
            "termux-usb": "/fake/bin/termux-usb",
            "adb": None,
            "fastboot": None,
        }
        self.which_patch = mock.patch.object(gui.shutil, "which", side_effect=lambda name: self.which.get(name))
        self.which_patch.start()
        self.addCleanup(self.which_patch.stop)

    def tearDown(self):
        gui._ROOT_AVAILABLE = self.old_root

    def test_selects_rootless_binaries_and_usb_cli(self):
        self.assertEqual(gui.adb_binary(), "/fake/bin/termux-adb")
        self.assertEqual(gui.fastboot_binary(), "/fake/bin/termux-fastboot")
        self.assertEqual(gui.backend_name(), "rootless Termux USB")

    def test_device_commands_run_as_termux_user(self):
        with mock.patch.object(gui, "run_user", return_value=(0, "user")) as user_run, \
             mock.patch.object(gui, "su_run", side_effect=AssertionError("root must not be called")):
            self.assertEqual(gui.device_run("id"), (0, "user"))
            user_run.assert_called_once()

    def test_probe_accepts_rootless_usb_backend_and_detects_fastbootd(self):
        out = ("@@USB\n@@ADB\nList of devices attached\n@@FB\nZX1 fastboot\n"
               "@@FBU\nis-userspace: yes\n@@UINFO\nDEV|1-1|18d1:4ee0|Google|Android\n"
               "IF|ff/42/03\n@@END\n")
        with mock.patch.object(gui, "device_run", return_value=(0, out)):
            status = gui.probe()
        self.assertTrue(status["backend_ok"])
        self.assertEqual(status["backend"], "rootless Termux USB")
        self.assertTrue(status["fastbootd"])
        self.assertGreater(status["usb"], 0)
        self.assertEqual(status["fb"], ["ZX1"])

    def test_missing_termux_usb_disables_rootless_backend(self):
        self.which["termux-usb"] = None
        with mock.patch.object(gui, "device_run", return_value=(0, "@@END\n")):
            status = gui.probe()
        self.assertFalse(status["backend_ok"])


class BinaryManifest(unittest.TestCase):
    def test_binary_manifest_extracts_package_and_min_sdk(self):
        with tempfile.TemporaryDirectory() as d:
            apk = os.path.join(d, "plugin.apk")
            with zipfile.ZipFile(apk, "w") as z:
                z.writestr("AndroidManifest.xml", _binary_xml_manifest())
            info = plugins.apk_manifest_info(apk)
            self.assertEqual(info["package"], "com.termux.api")
            self.assertEqual(info["min_sdk"], 23)
            self.assertEqual(plugins.validate_apk(apk, "com.termux.api")["package"], "com.termux.api")
            with self.assertRaisesRegex(ValueError, "wrong package ID"):
                plugins.validate_apk(apk, "com.termux.gui")

    def test_binary_manifest_detects_split_apk(self):
        with tempfile.TemporaryDirectory() as d:
            apk = os.path.join(d, "split.apk")
            with zipfile.ZipFile(apk, "w") as z:
                z.writestr("AndroidManifest.xml", _binary_xml_manifest(split="config.arm64_v8a"))
            with self.assertRaisesRegex(ValueError, "split APK"):
                plugins.validate_apk(apk, "com.termux.api")


class PluginSourceSelection(unittest.TestCase):
    def test_f_droid_runtime_flag_wins_when_installer_is_hidden(self):
        self.assertEqual(plugins.preferred_sources("", "F_DROID"), ["fdroid", "github"])

    def test_github_runtime_flag_selects_github_first(self):
        self.assertEqual(plugins.preferred_sources("", "GITHUB"), ["github", "fdroid"])

    def test_installer_metadata_is_used_when_runtime_flag_is_absent(self):
        self.assertEqual(plugins.preferred_sources("org.fdroid.fdroid", ""), ["fdroid", "github"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
