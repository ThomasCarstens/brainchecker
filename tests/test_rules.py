"""Decision signatures on lines taken from brainphysio_celia (python3 -m unittest discover tests)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brainchecker import rules  # noqa: E402


def kinds(line, path="a.jl"):
    return [(s.kind, s.symbol) for s in rules.scan_code_line(path, 1, line, rules.lang(path))]


def is_claim(text):
    sigs = []
    rules._prose(sigs, 1, text)
    return bool(sigs)


class Values(unittest.TestCase):
    def test_parameter_pair(self):
        self.assertIn(("value", "E_v"), kinds(":E_v          => 1.929946003,"))

    def test_registry_colour(self):                       # K19: M1 blue lives in the registry
        self.assertIn(("value", "m1"), kinds(':m1    => _row("m1", false, :none, "M1",  "#2d40bd"),'))

    def test_env_default(self):                           # K03
        self.assertIn(("value", "_M5_LIMIT_CYCLE"),
                      kinds('const LIMIT_CYCLE_SEED = get(ENV, "_M5_LIMIT_CYCLE", "1") in ("1", "true")'))

    def test_tolerance_keyword(self):                     # K02
        sigs = rules.scan_code_line("a.jl", 1, "function solve_to_periodic_steady_state(prob, T; tol = 1.3e-5, max_cycles = 400)", "julia")
        self.assertTrue(any(s.symbol == "tol" and s.tolerance for s in sigs))

    def test_python_constant(self):                       # K10
        self.assertIn(("value", "FS"), kinds("FS = 100.0", "a.py"))

    def test_numeric_vector_with_units(self):             # K08
        self.assertIn(("value", "FIT_START"), kinds("const FIT_START  = [ 0.6 * MMHG, 40.0 * MMHG, 1.12e7, 0.2, 7.0 * MMHG ]"))

    def test_kwarg_symbols(self):                         # the M4 sweep ramp target
        self.assertIn(("value", "ramp_target"), kinds("kind=:pressure, ramp_target=:Pabdo, overrides=Dict{Symbol,Float64}()),"))


class NotDecisions(unittest.TestCase):
    def test_calls_are_not_values(self):
        for line in ['dirty      = _git("status", "--porcelain") != "",', 'g = create_group(file, "dynamic")',
                     'IDX = np.rint((T0 - t[0]) / DT).astype(int)', 'd    = sc["variants"][v][r]',
                     'OUT          = os.path.join(HACK, "data_patients")']:
            self.assertEqual(kinds(line, "a.py" if "np." in line or "os." in line else "a.jl"), [], line)

    def test_comprehension_is_not_a_selection(self):
        self.assertEqual(kinds("u0_ss = [var => getu(sys, var)(u_end_static) for var in vars_to_keep]"), [])

    def test_spine_is_not_pin(self):                      # RE_SEL_NAME used to match "sPINe"
        self.assertEqual(kinds("Ro_spine_expr = (1 - β_v) * Ro_tot_v"), [])

    def test_cosmetic(self):
        self.assertEqual(kinds('xlabel="Time (s)", ylabel="Pressure (mmHg)"'), [])
        self.assertEqual(kinds("plot_titlefontsize=13),"), [])

    def test_tuple_of_variables(self):
        self.assertEqual(kinds("clims=(tlo, thi),"), [])


class Selections(unittest.TestCase):
    def test_models(self):
        self.assertIn(("selection", "MODELS"), kinds("MODELS = (:m1, :m4)"))

    def test_letter_map(self):
        self.assertIn(("selection", "LETTER"), kinds('LETTER = {"081": "A", "137": "B", "083": "C", "150": "D"}', "a.py"))

    def test_shell_patient_loop(self):                    # K14
        self.assertEqual(kinds("for p in 081 083 137 150; do", "a.sh")[0][0], "selection")


class Equations(unittest.TestCase):
    def test_mtk(self):
        self.assertEqual(kinds("in.p - ext.p ~ k * ((A/A0)^b1 - ((A/A0)^(-b2)))")[0][0], "equation")
        self.assertEqual(kinds("connect(Hs_Rvvs.out, Rt.in, Hs_Revp.in),")[0][0], "equation")


class Claims(unittest.TestCase):
    def test_finding_with_number(self):
        self.assertTrue(is_claim("over-drains at 3.6x CSF production. With the clamp it sees p_ref"))
        self.assertTrue(is_claim("I have kept 100 Hz for now"))

    def test_commented_out_code(self):
        self.assertFalse(is_claim("D(comps[:Rvvs].in.q)     => 0.0,"))
        self.assertFalse(is_claim('scatter!(p, r.bt, r.bamp; ms = 1.6, ma = 0.5, mc = :black, label = "recording")'))

    def test_ids_are_not_claims(self):
        self.assertFalse(is_claim("patient 137 and 150"))


class Criticality(unittest.TestCase):
    def test_generated_fit_is_passable_but_equation_is_not(self):
        from brainchecker import config
        t = config.load()
        sig = rules.scan_code_line("fits/m3/Model_5/fit/081.jl", 16, ":E_v          => 1.929946003,", "julia")
        crit, reasons, level, row = rules.criticality(t, "fits/m3/Model_5/fit/081.jl", sig, generated=True)
        self.assertEqual(level, "passable")
        self.assertFalse(crit)
        sig = rules.scan_code_line("Model_1/Model.jl", 1, "connect(brain.ext, Rspine.in),", "julia")
        self.assertTrue(rules.criticality(t, "Model_1/Model.jl", sig)[0])


if __name__ == "__main__":
    unittest.main()
