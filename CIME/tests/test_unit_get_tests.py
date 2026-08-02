#!/usr/bin/env python3

"""Unit tests for CIME/get_tests.py.

Tests cover the share field, which accepts a bool (True/False) or a test name
string that designates which test's build is shared across the group.
"""

import pytest
from unittest import mock

import CIME.get_tests as get_tests_module
from CIME.get_tests import get_test_data, get_build_groups, _short_test_name
from CIME.utils import CIMEError


# ---------------------------------------------------------------------------
# _short_test_name
# ---------------------------------------------------------------------------


class TestShortTestName:
    """Tests for the _short_test_name helper."""

    def test_strips_machine_compiler(self):
        assert _short_test_name("SMS_P2.f19_g16.A.melvin_gnu") == "SMS_P2.f19_g16.A"

    def test_preserves_testmods(self):
        assert (
            _short_test_name("SMS_P2.f19_g16.A.melvin_gnu.testmod")
            == "SMS_P2.f19_g16.A.testmod"
        )

    def test_preserves_multiple_testmods_segments(self):
        assert (
            _short_test_name("ERS.f19_g16.A.melvin_gnu.mod1--mod2")
            == "ERS.f19_g16.A.mod1--mod2"
        )


# ---------------------------------------------------------------------------
# get_test_data – share field
# ---------------------------------------------------------------------------


class TestGetTestDataShare:
    """Tests for the share field returned by get_test_data."""

    def test_share_defaults_to_false_when_absent(self):
        _, _, share, _, _ = get_test_data("cime_tiny")
        assert share is False

    def test_share_bool_true(self):
        _, _, share, _, _ = get_test_data("cime_test_share")
        assert share is True

    def test_share_string(self):
        _, _, share, _, _ = get_test_data("cime_test_share3")
        assert share == "SMS_P8.f45_g37.A"

    def test_share_invalid_type_raises(self):
        with mock.patch.dict(
            get_tests_module._ALL_TESTS,
            {"_invalid_share_suite": {"share": 42, "tests": ("ERS.f19_g16.A",)}},
        ):
            with pytest.raises(CIMEError):
                get_test_data("_invalid_share_suite")


# ---------------------------------------------------------------------------
# get_build_groups – share field behaviour
# ---------------------------------------------------------------------------


class TestGetBuildGroupsShare:
    """Tests for share-related behaviour in get_build_groups."""

    def test_share_true_first_in_order_is_leader(self):
        """share=True: first test in input order is the build leader."""
        tests = [
            "SMS_P2.f19_g16.A.melvin_gnu",
            "SMS_P4.f19_g16.A.melvin_gnu",
        ]
        groups = get_build_groups(tests)
        assert len(groups) == 1
        assert groups[0][0] == "SMS_P2.f19_g16.A.melvin_gnu"
        assert set(groups[0]) == set(tests)

    def test_share_true_reversed_input_keeps_first_as_leader(self):
        """share=True: leader is always the first test encountered, regardless of suite order."""
        tests = [
            "SMS_P4.f19_g16.A.melvin_gnu",
            "SMS_P2.f19_g16.A.melvin_gnu",
        ]
        groups = get_build_groups(tests)
        assert groups[0][0] == "SMS_P4.f19_g16.A.melvin_gnu"

    def test_share_string_designated_leader_becomes_first(self):
        """share=<string>: the named test is placed first in the group."""
        tests = [
            "SMS_P2.f45_g37.A.melvin_gnu",
            "SMS_P4.f45_g37.A.melvin_gnu",
            "SMS_P8.f45_g37.A.melvin_gnu",
            "SMS_P16.f45_g37.A.melvin_gnu",
        ]
        groups = get_build_groups(tests)
        assert len(groups) == 1
        assert groups[0][0] == "SMS_P8.f45_g37.A.melvin_gnu"
        assert set(groups[0]) == set(tests)

    def test_share_string_leader_at_end_of_input(self):
        """Designated leader at end of input is still placed first in the group."""
        tests = [
            "SMS_P16.f45_g37.A.melvin_gnu",
            "SMS_P2.f45_g37.A.melvin_gnu",
            "SMS_P4.f45_g37.A.melvin_gnu",
            "SMS_P8.f45_g37.A.melvin_gnu",
        ]
        groups = get_build_groups(tests)
        assert len(groups) == 1
        assert groups[0][0] == "SMS_P8.f45_g37.A.melvin_gnu"

    def test_share_string_leader_at_start_of_input(self):
        """Designated leader already first in input stays first in the group."""
        tests = [
            "SMS_P8.f45_g37.A.melvin_gnu",
            "SMS_P2.f45_g37.A.melvin_gnu",
            "SMS_P4.f45_g37.A.melvin_gnu",
            "SMS_P16.f45_g37.A.melvin_gnu",
        ]
        groups = get_build_groups(tests)
        assert len(groups) == 1
        assert groups[0][0] == "SMS_P8.f45_g37.A.melvin_gnu"

    def test_no_share_suite_each_test_own_group(self):
        """Tests not in any share suite each form their own singleton group."""
        tests = [
            "TESTRUNSLOWPASS_P1.f19_g16.A.melvin_gnu",
            "TESTRUNSLOWPASS_P1.ne30_g16.A.melvin_gnu",
        ]
        groups = get_build_groups(tests)
        assert len(groups) == 2
        assert all(len(g) == 1 for g in groups)

    def test_share_string_designated_leader_missing_raises(self):
        """If the designated leader is not present in the test list, raise CIMEError."""
        with mock.patch.dict(
            get_tests_module._ALL_TESTS,
            {
                "_missing_leader_suite": {
                    "share": "SMS_P99.f19_g16.A",
                    "tests": ("SMS_P2.f19_g16.A", "SMS_P4.f19_g16.A"),
                }
            },
        ):
            with pytest.raises(CIMEError):
                get_build_groups(
                    [
                        "SMS_P2.f19_g16.A.melvin_gnu",
                        "SMS_P4.f19_g16.A.melvin_gnu",
                    ]
                )

# ---------------------------------------------------------------------------
# get_build_groups – dynamic grouping behaviour
# ---------------------------------------------------------------------------

class TestGetBuildGroupsDynamicGrouping:
    """Tests for dynamic configuration-based grouping in get_build_groups."""

    def test_dynamic_grouping_by_exact_config(self):
        """Independent tests with the exact same configuration are grouped together."""
        tests = [
            "SMS.f19_g16.A.melvin_gnu",
            "ERS.f19_g16.A.melvin_gnu",
            "ERP.f19_g16.A.melvin_gnu",
            "SMS.ne30_g16.A.melvin_gnu",
            "ERS.ne30_g16.A.melvin_gnu"
        ]
        
        # We assume none of these tests are in a share suite for this test case
        with mock.patch("CIME.get_tests.get_test_suites", return_value=[]):
            groups = get_build_groups(tests)
        
        # We expect 2 groups based on the grid/compset/machine/compiler tuple
        assert len(groups) == 2
        
        # Check that the grouping is correct
        group1 = tuple(["SMS.f19_g16.A.melvin_gnu", "ERS.f19_g16.A.melvin_gnu", "ERP.f19_g16.A.melvin_gnu"])
        group2 = tuple(["SMS.ne30_g16.A.melvin_gnu", "ERS.ne30_g16.A.melvin_gnu"])
        
        assert group1 in groups
        assert group2 in groups

    def test_dynamic_grouping_different_caseopts(self):
        """Tests with different caseopts are NOT grouped together."""
        tests = [
            "SMS.f19_g16.A.melvin_gnu",
            "SMS.f19_g16.A.melvin_gnu.O1",
            "SMS.f19_g16.A.melvin_gnu.O2"
        ]
        
        with mock.patch("CIME.get_tests.get_test_suites", return_value=[]):
            groups = get_build_groups(tests)
            
        assert len(groups) == 3
        assert all(len(g) == 1 for g in groups)

    def test_dynamic_grouping_different_testmods(self):
        """Tests with different testmods are NOT grouped together."""
        tests = [
            "SMS.f19_g16.A.melvin_gnu",
            "SMS.f19_g16.A.melvin_gnu-testmod1",
            "SMS.f19_g16.A.melvin_gnu-testmod2"
        ]
        
        with mock.patch("CIME.get_tests.get_test_suites", return_value=[]):
            groups = get_build_groups(tests)
            
        assert len(groups) == 3
        assert all(len(g) == 1 for g in groups)

    def test_combo_shared_and_dynamic(self):
        """Tests that shared suites and dynamic grouping work together correctly."""
        tests = [
            "SMS_P2.f19_g16.A.melvin_gnu",
            "SMS_P4.f19_g16.A.melvin_gnu",
            "ERS.ne30_g16.A.melvin_gnu",
            "ERP.ne30_g16.A.melvin_gnu"
        ]
        
        mock_tests = {
            "MY_SHARE_SUITE": {"share": True, "tests": ("SMS_P2.f19_g16.A", "SMS_P4.f19_g16.A")},
            "ERS": {"share": False, "tests": ("ERS.ne30_g16.A",)},
            "ERP": {"share": False, "tests": ("ERP.ne30_g16.A",)},
        }
        
        with mock.patch.dict(get_tests_module._ALL_TESTS, mock_tests, clear=True):
            groups = get_build_groups(tests)
            
        assert len(groups) == 2
        
        # Verify the shared group (transitive grouping could result in either order)
        shared_group_set = set(["SMS_P2.f19_g16.A.melvin_gnu", "SMS_P4.f19_g16.A.melvin_gnu"])
        assert any(set(g) == shared_group_set for g in groups)
        
        # Verify the dynamic group
        dynamic_group = tuple(["ERS.ne30_g16.A.melvin_gnu", "ERP.ne30_g16.A.melvin_gnu"])
        assert dynamic_group in groups
