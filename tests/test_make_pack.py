"""知识包应与仓库所在的绝对路径无关。

运行：python -m unittest discover -s tests -p 'test_*.py'
"""
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MakePackTests(unittest.TestCase):
    def test_pack_is_independent_of_checkout_location(self):
        with tempfile.TemporaryDirectory() as directory:
            builds = []
            for name in ("checkout-a", "nested/checkout with spaces"):
                checkout = Path(directory) / name
                (checkout / "tools").mkdir(parents=True)
                (checkout / "references").mkdir()
                for relative in ("SKILL.md", "sources.md",
                                 "references/00-index.md", "tools/make_pack.py"):
                    shutil.copyfile(ROOT / relative, checkout / relative)
                shutil.copytree(ROOT / "data", checkout / "data")
                module = runpy.run_path(str(checkout / "tools/make_pack.py"))
                content, parts = module["build"]()
                for path, _ in parts:
                    self.assertFalse(Path(path).is_absolute(), path)
                    self.assertNotIn("\\", path)
                    self.assertTrue((checkout / path).is_file(), path)
                self.assertNotIn(str(checkout), content)
                builds.append(content)
            self.assertEqual(builds[0], builds[1])
            self.assertEqual(
                builds[0], (ROOT / "pack/seu-handbook.md").read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
