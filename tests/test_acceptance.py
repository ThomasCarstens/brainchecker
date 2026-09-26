"""Acceptance on the real repository (form: "testing on my current code will be the check").

Skipped when brainphysio_celia is not checked out at the target path.
"""
import sys
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brainchecker import config, gitutil, stage  # noqa: E402

T = config.load()
HAVE_REPO = (T.root / ".git").exists()


@unittest.skipUnless(HAVE_REPO, "target repo not present")
class Known(unittest.TestCase):
    def test_every_form_decision_points_at_a_real_line(self):
        known = tomllib.loads((T.home / "targets" / T.name / "known.toml").read_text())["decision"]
        self.assertEqual(len(known), 32)
        for k in known:
            for w in k.get("where", []):
                f, ln = w.rsplit(":", 1)
                path = T.root / f
                self.assertTrue(path.is_file(), f"{k['id']}: {f} is gone")
                n = len(path.read_text(errors="replace").splitlines())
                self.assertLessEqual(int(ln), n, f"{k['id']}: {w} is past the end of the file")


@unittest.skipUnless(HAVE_REPO, "target repo not present")
class Replay(unittest.TestCase):
    def test_drive_removal_is_flagged(self):
        """e4341b01 removed the Drive upload: its gates must show up as deleted gates."""
        sha = "e4341b01"
        if gitutil.git(T.root, "cat-file", "-t", sha, check=False).strip() != "commit":
            self.skipTest("commit not in this clone")
        parent = gitutil.git(T.root, "rev-parse", sha + "^").strip()
        ds = stage.analyse(T, gitutil.range_diff(T.root, f"{parent}..{sha}"), sha, None, with_reach=False)
        reasons = [r for d in ds for r in d["reasons"]]
        self.assertTrue(any("deleted gate" in r for r in reasons))
        self.assertTrue(all(stage.level_of(d) == ("unexamined", True) for d in ds))

    def test_hook_never_raises(self):
        self.assertEqual(stage.pre_commit(T), 0)


if __name__ == "__main__":
    unittest.main()
