"""
End-to-end test: hide a few JPEGs in a fake "card" image, run real PhotoRec
through the wrapper, and check they all come back. Skipped if PhotoRec
isn't installed.

    python3 -m unittest discover -s tests -v
"""

import base64
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import device_utils as du  # noqa: E402
import photorec_wrapper as pr  # noqa: E402

# A small, valid 64x48 JPEG.
TINY_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIf"
    "IiEmKzcvJik0KSEiMEExNDk7Pj4+JS5ESUM8SDc9Pjv/2wBDAQoLCw4NDhwQEBw7KCIoOzs7Ozs7"
    "Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozv/wAARCAAwAEADASIA"
    "AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA"
    "AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3"
    "ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm"
    "p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA"
    "AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx"
    "BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK"
    "U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3"
    "uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwCGLyGu"
    "VS92xXEUGLiR4t8kiszKWV5QS5IkVVI3ZDnAUFdtqNriewis5bSCNJZxKytJ5KRO7OYjJ5f3d3Qb"
    "enPfAWI3mrJ/pE2oq8Mylb2Ry9wikNvdQCw8tgu0kYUKvHVSBJp1sLZIZbmExW8hiDbYCiyMJEKh"
    "Wyrop2DaoTcChOB0IBRuBY3GnWLWtm8NpfXaHzVfzSxMzNhVPLOjOAE2kkZyuPmG1pdzYtJOhuRP"
    "qO12EDRcmN5vkZljGCh/dkhcEhV6BipoW+qRzeIFnuLy6uCZT5imFRDLJymTJj737tFHKkklAcMT"
    "TYJZbG2sbhLmV/NKzpLNKSJWjAcuYiu7LMd2VOSMs3zHbQBfkKXxMX2eRZ1t5JWRLaRDcTEH94ZA"
    "oXChcgKpOAeS2FqnqN1qFzHBdSJdWxwz27SxqVEJiYMHRdrIAu5Tt5OcgDy9osQW0GlXXkSx2DyR"
    "u7QiTbDsiDMHYzg7VPm8MnYsMjiqttaXFyuoXii+gb5w6vJJM8m4R7AXVSJQSoAYPkbVAAOdwA+4"
    "0m/ut2+8bVriJW8z7O0cs4LAKoKlAH2kOpz8xMe7IC7RFDrNm+nWVvP5Xli8bzbq2lZkiiAwRuHJ"
    "JPHBAAC42llqRr6SaW4t4ReLb3d24md7YhbvMgKyYRPm3KCQqqGJzgkM22/O7aLcCBryO8uZZJVl"
    "gnuFy0Yyu2MblwSyKTwN2CMsAAoBVlj067kd10+fWJorhnlKykIplKJiUggZCqS2W/5YjdtYkql3"
    "cta2ttFp0kkroTcQb5nZl8vYQCu4lUZ5GztAyAVyAARUk0+SPw0kTjMDnbFOYVHl7FeQArM218li"
    "wIbjDKT8op0bJYW91DPql1ZJaAi4jFus6zNhtjSElc/KrEJtGAqseF3EA09WkvnmNnYSxx2/kif7"
    "MpGyXDbVRQkeBn95tTqX55GSKdvoR1CcwxwW8S+a4hfLIZFO5GJBIDEyb2K43KDgbcbQ+2hubXWr"
    "eznMEgnQMwWKNHL+YAwkMa4QrvdVIbblQG7LVZ7K7ttRjunWcebmOR8L5ryu5zI8KI6u2UKYyQxR"
    "c/eFAFeGexl1JjcaajKWit5IbmYiWEusjBY1ABIyzHYPmZtvC8MyTT2upQ3PlfZrg3cnlrJcqFJk"
    "8sKqNsVtjESMVz/cVc5GxJoJm0i4mtfIis3YR+aCAZ1wQ7hWQnzMkxvkFSFAxjcHqWxmW2tFmZDA"
    "YYGT7XASgMyuQFwirnKOAD82wvgfN94AzDqiSwRWGk2kllO0wluohD9pkkwd4YAoA6ErHg4JzwQR"
    "szrzfZ5bm0S5sYmFyyQxpNK7vB5e5GRRwzEEMpDEZC9cfNVSxj0u4T7VdXawyyNmOe3mdAJFkZGf"
    "nLeXuK4YbgDk5UgqWwtDYPNAbnSrudiPKVfMEcjqGVXdVyAxDooJBAIwDu3YANITxrKtsLiOys4E"
    "wxljaDzc7pCGk3D5GYbyR975MEAjOHaahc6lezXTQSQQXxVXV5gpkCrI5AfblU2KnYABTwQSrdFp"
    "92v2YXf25HhuJv3V2kOLjzGDLG4DBtzOJChBXGMk4LZasiSHT5rG4mWeJIGjhlEBdm2sN4dSditl"
    "o03B8nKHHOVAHFJDIbNTbhiGlmt4RHHMUZSQjxbgidASR/eXGcA1WVLuRZI1g1CSB1SIyw3ckLbm"
    "8tPMLuN2fMCqo2HC5UhQp3TbLfTozdX1vGbiJWRxak7pSNxZiA2wthWPGQVVlw4UBZII/sOnW8kd"
    "yHjELSQyXUkflLlikjLgsqqA6qzYyT82QCdwBnWl5BJZXi2+n3UM1u6x2sTSKx8wNtjyVH8f3c8D"
    "LH5ssBVqaG+R7O1uUeCwjMQMeHXe6yEMC20IcKFL4+UdcqAEMum2iXQsYbJ7mf5Q0kETblAZJUZH"
    "JYbfmWYcNgbxtzkyVQghW2jkikhG69XEUk022KaVpXYoSnO9cyAyOwOE+6RQBOWspI7zKy2zwRnd"
    "DbJvaFdxBMgOfmR5DvxjoNrAx1DcpbWdvbASiaxCNJEsdwUkjkWNTIqyg5aNlwTyDtlBGArlb93d"
    "RyNJP5cEKSzKYYxlBMgDMk7gMclY8ksNp3qFPUinSTRabcXUltCLGaeCTO88RT75AjlAnzkbXOQv"
    "RWGdoKqAf//Z"
)

BINARY = pr.find_photorec_binary()


class TestSafety(unittest.TestCase):
    def test_run_folders_never_collide(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = pr.new_run_folder(Path(tmp))
            b = pr.new_run_folder(Path(tmp))
            self.assertNotEqual(a, b)
            self.assertTrue(a.is_dir() and b.is_dir())

    def test_blocks_saving_onto_the_card(self):
        with tempfile.TemporaryDirectory() as card:
            dev = du.Device(path="/dev/disk9", label="test", mountpoints=[card])
            self.assertTrue(du.destination_is_on_device(Path(card) / "photos", dev))
            self.assertFalse(du.destination_is_on_device(Path.home(), dev))

    def test_command_has_no_shell(self):
        cmd = pr.build_command("photorec", "/dev/disk4; rm -rf ~", Path("/tmp/x"))
        self.assertIn("/dev/disk4; rm -rf ~", cmd)  # passed as one literal argument

    def test_strips_terminal_codes(self):
        self.assertEqual(pr._CONTROL.sub("", pr._ESCAPES.sub("", "\x1b[5dDisk ok\x0f")), "Disk ok")


@unittest.skipUnless(BINARY, "PhotoRec not installed")
class TestRecovery(unittest.TestCase):
    def test_recovers_hidden_jpegs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            image = bytearray(8 * 1024 * 1024)
            offsets = [1 << 20, 3 << 20, 6 << 20]
            for off in offsets:
                image[off:off + len(TINY_JPEG)] = TINY_JPEG
            card = tmp / "card.img"
            card.write_bytes(bytes(image))
            out = tmp / "out"
            out.mkdir()

            done = threading.Event()
            result = {}
            handle = pr.start_run(
                BINARY, str(card), out,
                on_line=lambda _l: None,
                on_done=lambda _h, code: (result.update(code=code), done.set()),
            )
            self.assertTrue(done.wait(120), "PhotoRec timed out")
            self.assertEqual(result["code"], 0)
            self.assertGreaterEqual(pr.count_recovered(handle.run_dir), len(offsets))


if __name__ == "__main__":
    unittest.main()
