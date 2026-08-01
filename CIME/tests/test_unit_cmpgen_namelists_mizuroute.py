import unittest
import tempfile
import os
import shutil

from CIME.case.case_cmpgen_namelists import _do_full_nl_comp

class DummyCase:
    def __init__(self, caseroot, baseline_root):
        self.caseroot = caseroot
        self.baseline_root = baseline_root

    def get_value(self, key):
        if key == "CASEROOT":
            return self.caseroot
        if key == "BASELINE_ROOT":
            return self.baseline_root
        return None

class TestMizuRouteNamelistCompare(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.caseroot = os.path.join(self.tempdir, "caseroot")
        self.casedocs = os.path.join(self.caseroot, "CaseDocs")
        self.baseline_root = os.path.join(self.tempdir, "baselines")
        
        self.compare_name = "test_cmp"
        self.test_name = "test_case"
        
        self.baseline_dir = os.path.join(self.baseline_root, self.compare_name, self.test_name)
        self.baseline_casedocs = os.path.join(self.baseline_dir, "CaseDocs")
        
        os.makedirs(self.casedocs)
        os.makedirs(self.baseline_casedocs)
        
        self.case = DummyCase(self.caseroot, self.baseline_root)

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_baseline_has_only_control(self):
        # Setup generated CaseDocs with both
        with open(os.path.join(self.casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
        with open(os.path.join(self.casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        # Setup baseline with ONLY .control
        with open(os.path.join(self.baseline_casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
            
        match, comments = _do_full_nl_comp(self.case, self.test_name, self.compare_name)
        
        # We expect this to fail currently because mizuroute.toml is missing from baseline!
        # But we write the test to codify the expectation (it should pass if implemented correctly)
        self.assertTrue(match)

    def test_baseline_has_both(self):
        # Setup generated CaseDocs with both
        with open(os.path.join(self.casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
        with open(os.path.join(self.casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        # Setup baseline with BOTH
        with open(os.path.join(self.baseline_casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
        with open(os.path.join(self.baseline_casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        match, comments = _do_full_nl_comp(self.case, self.test_name, self.compare_name)
        self.assertTrue(match)

    def test_baseline_has_only_toml(self):
        # Setup generated CaseDocs with both
        with open(os.path.join(self.casedocs, "mizuRoute.control"), "w") as f:
            f.write("route_opt 5\n")
        with open(os.path.join(self.casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        # Setup baseline with ONLY .toml
        with open(os.path.join(self.baseline_casedocs, "mizuroute.toml"), "w") as f:
            f.write("[route_opt]\nvalue = 5\n")
            
        match, comments = _do_full_nl_comp(self.case, self.test_name, self.compare_name)
        
        # This will also fail currently because mizuRoute.control is in CaseDocs but not baseline.
        self.assertTrue(match)

if __name__ == '__main__':
    unittest.main()
