"""Standalone wheel loads match sus_load and preserve the requested force totals."""

from contextlib import redirect_stdout
from io import StringIO
import math
import unittest
from unittest.mock import patch

import numpy as np

import angle_stiffness as model
from analysis.wheel_load.models import Vehicle, wheel_load_stiffness


class SuspensionTireForceTests(unittest.TestCase):
    def wheel_loads(self, **overrides):
        values = dict(mass=260.55, unsprung_mass=14.4, cog_height=.3,
                      front_distance=.60, rear_distance=.93, front_track=1.25, rear_track=1.24,
                      acceleration_x_g=.7, acceleration_y_g=.8, downforce=450.,
                      aero_front_ratio=.62, front_roll_stiffness=25000., rear_roll_stiffness=45000.)
        values.update(overrides)
        return model.calculate_suspension_wheel_loads(**values)

    def test_loads_match_sus_load_for_asymmetric_aero_geometry_and_signed_acceleration(self):
        car = Vehicle(318.15, .3, 1.53, 1.25, 1.24, .93 / 1.53, 450., .62)
        for ax, ay in ((0., 0.), (.7, .8), (-.8, -.6), (2., 2.2)):
            with self.subTest(ax=ax, ay=ay):
                result = self.wheel_loads(acceleration_x_g=ax, acceleration_y_g=ay)
                loads = np.array(list(result['wheel_loads_N'].values()))
                expected = wheel_load_stiffness(car, ax * model.g, ay * model.g,
                                                70000., 30000., 25000., 45000.)
                np.testing.assert_allclose(loads, expected, atol=1e-10)
                np.testing.assert_allclose(car.matrix @ loads, car.target(ax * model.g, ay * model.g),
                                           atol=1e-10)
                self.assertAlmostEqual(sum(loads), car.mass * model.g + car.downforce)

    def test_aero_changes_normal_load_without_becoming_inertial_mass(self):
        first = self.wheel_loads(downforce=0.)
        second = self.wheel_loads(downforce=1000.)
        self.assertAlmostEqual(first['longitudinal_transfer_N'], second['longitudinal_transfer_N'])
        self.assertAlmostEqual(second['front_axle_load_N'] - first['front_axle_load_N'], 620.)
        self.assertAlmostEqual(second['rear_axle_load_N'] - first['rear_axle_load_N'], 380.)
        forces = model.calculate_tire_force_demands(second['wheel_loads_N'], second['total_mass_kg'], .7, .8)
        self.assertAlmostEqual(forces['total_Fx_N'], 318.15 * .7 * model.g)
        self.assertAlmostEqual(forces['total_Fy_N'], 318.15 * .8 * model.g)

    def test_proportional_demands_preserve_three_force_totals_when_in_contact(self):
        loads = self.wheel_loads()
        result = model.calculate_tire_force_demands(loads['wheel_loads_N'], loads['total_mass_kg'], .7, .8)
        self.assertTrue(result['contact_valid'])
        self.assertFalse(result['reference_only'])
        forces = result['wheel_forces']
        self.assertAlmostEqual(sum(value['Fx_N'] for value in forces.values()), 318.15 * .7 * model.g)
        self.assertAlmostEqual(sum(value['Fy_N'] for value in forces.values()), 318.15 * .8 * model.g)
        self.assertAlmostEqual(sum(value['Fz_N'] for value in forces.values()), loads['total_normal_load_N'])
        for value in forces.values():
            self.assertAlmostEqual(value['Fx_N'] / value['Fz_N'], result['total_Fx_N'] / loads['total_normal_load_N'])
            self.assertAlmostEqual(value['Fy_N'] / value['Fz_N'], result['total_Fy_N'] / loads['total_normal_load_N'])
            self.assertAlmostEqual(value['force_magnitude_N'],
                                   math.sqrt(value['Fx_N']**2 + value['Fy_N']**2 + value['Fz_N']**2))
        self.assertEqual(result['most_loaded_wheel'], 'RR')

    def test_negative_acceleration_changes_force_sign_and_zero_load_gets_no_force(self):
        result = model.calculate_tire_force_demands(dict(FL=0., FR=300., RL=500., RR=700.), 120., -1., -.5)
        self.assertTrue(result['contact_valid'])
        for axis in ('Fx_N', 'Fy_N', 'Fz_N', 'force_magnitude_N'):
            self.assertEqual(result['wheel_forces']['FL'][axis], 0.)
        self.assertLess(result['wheel_forces']['RR']['Fx_N'], 0.)
        self.assertLess(result['wheel_forces']['RR']['Fy_N'], 0.)
        self.assertEqual(result['most_loaded_wheel'], 'RR')

    def test_negative_raw_load_is_retained_and_clipped_forces_are_reference_only(self):
        loads = dict(FL=-100., FR=300., RL=500., RR=700.)
        result = model.calculate_tire_force_demands(loads, 120., 1., 1.)
        self.assertFalse(result['contact_valid'])
        self.assertTrue(result['reference_only'])
        self.assertEqual(loads['FL'], -100.)
        self.assertEqual(result['wheel_forces']['FL']['raw_Fz_N'], -100.)
        self.assertEqual(result['wheel_forces']['FL']['Fz_N'], 0.)
        self.assertEqual(result['clipped_total_Fz_N'] - sum(loads.values()), 100.)

    def test_invalid_inputs_are_rejected(self):
        invalid = (dict(front_distance=0.), dict(rear_distance=math.nan), dict(front_track=-1.),
                   dict(cog_height=-.1), dict(downforce=-1.), dict(aero_front_ratio=1.1),
                   dict(front_roll_stiffness=0.), dict(rear_roll_stiffness=math.inf),
                   dict(acceleration_x_g=math.nan), dict(acceleration_y_g=math.inf))
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.wheel_loads(**overrides)
        for loads in (dict(FL=math.nan, FR=1., RL=1., RR=1.), dict.fromkeys(('FL', 'FR', 'RL', 'RR'), 0.)):
            with self.subTest(loads=loads), self.assertRaises(ValueError):
                model.calculate_tire_force_demands(loads, 120., 1., 1.)

    def test_main_connects_computed_aero_springs_and_signed_accelerations(self):
        with (patch.multiple(model, ax=-1., ay=-1., lf=.6, lr=.93, F_ref_ratio=.5, wl_aero_front_ratio=.65),
              patch.object(model, 'calculate_suspension_wheel_loads', wraps=model.calculate_suspension_wheel_loads) as solver,
              redirect_stdout(StringIO()) as output):
            model.main()
        args = solver.call_args.args
        downforce = model.calculate_skidpad_downforce(model.ms, model.mu, model.wl_mu_y, model.target_lap_time_s)
        self.assertEqual(args[3:5], (.6, .93))
        self.assertEqual(args[7:9], (-1., -1.))
        self.assertAlmostEqual(args[9], .5 * downforce['skidpad_required_aero_downforce_N'])
        self.assertEqual(args[10], .65)
        self.assertAlmostEqual(args[12] / args[11], model.kr / model.kf * (model.tr / model.tf)**2)
        self.assertIn('sus_load', output.getvalue())
        self.assertIn('合力最大的輪胎', output.getvalue())


class LateralTireRollTests(unittest.TestCase):
    def test_vertical_and_roll_moment_balance_with_signed_acceleration(self):
        for acceleration in (0., 1., -1.):
            with self.subTest(acceleration=acceleration):
                result = model.calculate_lateral_tire_roll(159.075, .3, 1.25, 80000., acceleration)
                left, right = result['left_normal_load_N'], result['right_normal_load_N']
                self.assertTrue(result['contact_valid'])
                self.assertAlmostEqual(left + right, 159.075 * model.g)
                self.assertAlmostEqual((right - left) * 1.25 / 2,
                                       159.075 * acceleration * model.g * .3)
                self.assertAlmostEqual(result['left_linear_compression_m'] * 80000., left)
                self.assertAlmostEqual(result['right_linear_compression_m'] * 80000., right)
                self.assertAlmostEqual(result['deformation_difference_m'],
                                       result['right_linear_compression_m'] - result['left_linear_compression_m'])
                self.assertAlmostEqual(result['tire_roll_angle_rad'], result['deformation_difference_m'] / 1.25)
                self.assertAlmostEqual(result['left_compression_change_m'] + result['right_compression_change_m'], 0.)
        positive = model.calculate_lateral_tire_roll(159.075, .3, 1.25, 80000., 1.)
        negative = model.calculate_lateral_tire_roll(159.075, .3, 1.25, 80000., -1.)
        stiffer = model.calculate_lateral_tire_roll(159.075, .3, 1.25, 160000., 1.)
        self.assertAlmostEqual(positive['left_normal_load_N'], negative['right_normal_load_N'])
        self.assertAlmostEqual(positive['tire_roll_angle_deg'], -negative['tire_roll_angle_deg'])
        self.assertAlmostEqual(stiffer['tire_roll_angle_deg'], positive['tire_roll_angle_deg'] / 2)

    def test_liftoff_preserves_linear_reference_and_withholds_physical_roll(self):
        boundary = model.calculate_lateral_tire_roll(100., .25, 1., 80000., 2.)
        self.assertTrue(boundary['contact_valid'])
        self.assertTrue(boundary['at_lift_boundary'])
        self.assertAlmostEqual(boundary['left_normal_load_N'], 0.)
        result = model.calculate_lateral_tire_roll(159.075, .3, 1.25, 80000., 2.2)
        self.assertFalse(result['contact_valid'])
        self.assertLess(result['left_linear_compression_m'], 0.)
        self.assertIsNone(result['tire_roll_angle_deg'])
        self.assertIsNone(result['tire_roll_angle_rad'])
        self.assertAlmostEqual(result['linear_tire_roll_angle_deg'], .9441858549709072)
        self.assertAlmostEqual(result['ay_contact_limit_g'], 1.25 / .6)
        zero_height = model.calculate_lateral_tire_roll(100., 0., 1., 80000., 3.)
        self.assertTrue(zero_height['contact_valid'])
        self.assertEqual(zero_height['tire_roll_angle_deg'], 0.)

    def test_main_uses_axle_mass_shares_and_only_lateral_acceleration(self):
        with (patch.multiple(model, ax=.8, ay=-1., lf=.6, lr=.93, F_ref_ratio=.25),
              patch.object(model, 'calculate_lateral_tire_roll', wraps=model.calculate_lateral_tire_roll) as solver,
              redirect_stdout(StringIO()) as output):
            model.main()
        calls = [call.args for call in solver.call_args_list]
        total_mass = model.ms + 4 * model.mu
        self.assertEqual(len(calls), 2)
        self.assertAlmostEqual(calls[0][0], total_mass * .93 / 1.53)
        self.assertAlmostEqual(calls[1][0], total_mass * .6 / 1.53)
        self.assertEqual(calls[0][1:], (model.h_cog, model.tf, model.Kt, -1.))
        self.assertEqual(calls[1][1:], (model.h_cog, model.tr, model.Kt, -1.))
        self.assertIn('ax = 0、空力下壓力 = 0', output.getvalue())

    def test_invalid_inputs_are_rejected(self):
        values = [159.075, .3, 1.25, 80000., 1.]
        for index, value in ((0, 0.), (1, -.1), (2, 0.), (3, -1.), (4, math.nan)):
            invalid = values.copy()
            invalid[index] = value
            with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                model.calculate_lateral_tire_roll(*invalid)


class FVSATests(unittest.TestCase):
    def test_requested_process_matches_front_and_rear_examples(self):
        examples = ((1.25, 2.2906100426385296, .9720432720386547, 1.1453050213192648),
                    (1.24, 2.309062789025683, .959593717895401, 1.1545313945128415))
        for track, roll_deg, length_m, camber_deg in examples:
            with self.subTest(track=track):
                result = model.calculate_fvsa(.025, track)
                self.assertAlmostEqual(result['max_roll_angle_deg'], roll_deg, places=12)
                self.assertAlmostEqual(result['fvsa_length_m'], length_m, places=12)
                self.assertAlmostEqual(result['max_camber_change_deg'], camber_deg, places=12)
                self.assertAlmostEqual(result['fvsa_length_mm'], 1000 * length_m)
                self.assertAlmostEqual(result['camber_gain_deg_per_mm'] * 1000,
                                       result['camber_gain_deg_per_m'])
                # For these inputs atan(tan(theta/(2d))) stays on its principal branch.
                self.assertAlmostEqual(result['max_camber_change_deg'], roll_deg / 2)
                _, travel_angle = model.calculate_compressed_travel(260., 1., .3, track, .025)
                self.assertAlmostEqual(result['max_roll_angle_deg'], travel_angle)

    def test_main_passes_travel_and_each_track_in_meters(self):
        with (patch.object(model, 'calculate_fvsa', wraps=model.calculate_fvsa) as solver,
              redirect_stdout(StringIO()) as output):
            model.main()
        self.assertEqual([call.args for call in solver.call_args_list],
                         [(model.sus_travel, model.tf), (model.sus_travel, model.tr)])
        self.assertIn('FVSA：最大 Roll 角', output.getvalue())
        self.assertIn('deg/mm', output.getvalue())
        self.assertIn('最大 Camber 變化角', output.getvalue())

    def test_invalid_lengths_and_nonpositive_fvsa_are_rejected(self):
        for travel, track in ((0., 1.25), (-.025, 1.25), (.025, 0.),
                              (math.nan, 1.25), (.025, math.inf), (.025, .2)):
            with self.subTest(travel=travel, track=track), self.assertRaises(ValueError):
                model.calculate_fvsa(travel, track)


class CasterTests(unittest.TestCase):
    def front_case(self, acceleration=2.2, steering=math.degrees(math.atan(1.53 / 3.))):
        fvsa = model.calculate_fvsa(.025, 1.25)
        tire = model.calculate_lateral_tire_roll(159.075, .3, 1.25, 80000., acceleration)
        return model.calculate_caster_for_zero_camber(
            fvsa['max_roll_angle_deg'], tire['linear_tire_roll_angle_deg'],
            fvsa['max_camber_change_deg'], 8., steering
        )

    def test_current_front_case_and_independent_forward_substitution(self):
        result = self.front_case()
        self.assertEqual(result['solution_status'], 'solved')
        self.assertAlmostEqual(result['base_camber_deg'], 2.0894908762901716)
        self.assertAlmostEqual(result['caster_deg'], 6.28885967803232)
        self.assertAlmostEqual(result['kpi_camber_change_deg'], -.870481487754025)
        delta = math.atan(1.53 / 3.)
        forward_change = delta * math.sin(math.radians(result['caster_deg'])) \
            - (1 - math.cos(delta)) * math.sin(math.radians(8.))
        self.assertAlmostEqual(math.radians(result['base_camber_deg']) - forward_change, 0., places=14)
        self.assertAlmostEqual(result['raw_steering_camber_change_deg'], math.degrees(forward_change))
        self.assertAlmostEqual(result['steering_angle_deg'], 27.02158159117704)
        self.assertEqual(result['camber_direction_factor'], -1)
        self.assertAlmostEqual(result['steering_camber_change_deg'], -result['base_camber_deg'])
        self.assertAlmostEqual(result['final_camber_deg'], 0., places=12)

    def test_signed_steering_and_kpi_contributions(self):
        positive, negative = self.front_case(1., 30.), self.front_case(1., -30.)
        self.assertAlmostEqual(positive['caster_deg'], -negative['caster_deg'])
        self.assertEqual(positive['steering_angle_deg'], 30.)
        self.assertEqual(negative['steering_angle_deg'], -30.)
        self.assertAlmostEqual(positive['kpi_camber_change_deg'], negative['kpi_camber_change_deg'])
        kpi_only = model.calculate_caster_for_zero_camber(0., 0., 0., 8., 30.)
        self.assertGreater(kpi_only['caster_deg'], 0.)
        self.assertAlmostEqual(kpi_only['caster_camber_change_deg'], -kpi_only['kpi_camber_change_deg'])
        no_kpi = model.calculate_caster_for_zero_camber(0., 0., 0., 0., 30.)
        self.assertEqual(no_kpi['caster_deg'], 0.)

    def test_unreachable_target_and_asin_boundary(self):
        impossible = model.calculate_caster_for_zero_camber(90., 0., 0., 8., 1.)
        self.assertEqual(impossible['solution_status'], 'unreachable')
        self.assertFalse(impossible['has_real_solution'])
        self.assertIsNone(impossible['caster_deg'])
        self.assertIsNone(impossible['final_camber_deg'])
        for steering in (30., -30.):
            result = model.calculate_caster_for_zero_camber(30., 0., 0., 0., steering)
            self.assertEqual(result['caster_deg'], math.copysign(90., steering))
            self.assertAlmostEqual(result['final_camber_deg'], 0.)

    def test_fixed_caster_shows_small_and_large_steering_sides(self):
        positive = model.calculate_steering_camber(10., 8., 30.)
        negative = model.calculate_steering_camber(10., 8., -30.)
        self.assertAlmostEqual(positive, 4.141127705474514)
        self.assertAlmostEqual(negative, -6.277762954541307)
        self.assertLess(abs(positive), abs(negative))
        # Direction was checked at a large caster; solve using the explicitly fixed +30 deg.
        result = model.calculate_caster_for_zero_camber(positive, 0., 0., 8., 30.)
        self.assertAlmostEqual(result['caster_deg'], 10.)
        self.assertAlmostEqual(result['steering_camber_change_deg'], -positive)

    def test_fixed_coordinate_sign_preserves_both_raw_polarities(self):
        for base in (2., -2.):
            with self.subTest(base=base):
                result = model.calculate_caster_for_zero_camber(base, 0., 0., 8., 30.)
                self.assertEqual(result['steering_angle_deg'], 30.)
                self.assertEqual(result['camber_direction_factor'], -1)
                self.assertAlmostEqual(result['raw_steering_camber_change_deg'], base)
                self.assertAlmostEqual(result['steering_camber_change_deg'], -base)
                self.assertAlmostEqual(result['final_camber_deg'], 0.)

    def test_direction_check_is_read_only_and_does_not_change_the_solution(self):
        calls = []
        for reference_caster in (10., 20.):
            with (patch.object(model, 'caster_direction_check_deg', reference_caster),
                  patch.object(model, 'calculate_caster_for_zero_camber',
                               wraps=model.calculate_caster_for_zero_camber) as solver,
                  redirect_stdout(StringIO()) as output):
                model.main()
            calls.append(solver.call_args.args)
            self.assertIn('固定正方向 delta = +27.021582 deg', output.getvalue())
            self.assertIn('線性外推參考 Caster = 6.288860 deg', output.getvalue())
            self.assertIn('以下比較僅供查核，不修改設定', output.getvalue())
        self.assertEqual(calls[0], calls[1])

    def test_zero_steering_distinguishes_no_solution_from_underdetermined(self):
        for base, expected in ((1., 'unreachable'), (0., 'underdetermined')):
            result = model.calculate_caster_for_zero_camber(base, 0., 0., 8., 0.)
            self.assertEqual(result['solution_status'], expected)
            self.assertIsNone(result['caster_deg'])
            self.assertIsNone(result['required_caster_sine'])

    def test_main_uses_front_results_and_labels_invalid_contact(self):
        for acceleration in (1., 2.2):
            with (self.subTest(ay=acceleration), patch.object(model, 'ay', acceleration),
                  patch.object(model, 'calculate_caster_for_zero_camber',
                               wraps=model.calculate_caster_for_zero_camber) as solver,
                  redirect_stdout(StringIO()) as output):
                model.main()
            solver.assert_called_once()
            args = solver.call_args.args
            self.assertAlmostEqual(args[0], 2.2906100426385296)
            self.assertAlmostEqual(args[1], .9441858549709072 * acceleration / 2.2)
            self.assertAlmostEqual(args[2], 1.1453050213192648)
            self.assertEqual(args[3], 8.)
            self.assertAlmostEqual(args[4], math.degrees(math.atan((model.lf + model.lr) / model.min_turn_radius_m)))
            self.assertIn('回代前輪 Camber = 0.000000000 deg', output.getvalue())
            if acceleration == 2.2:
                self.assertIn('線性外推參考 Caster = 6.288860 deg', output.getvalue())
                self.assertIn('驗證 delta = +27.021582 deg：原式 Delta camber = +3.821767 deg', output.getvalue())
                self.assertIn('驗證 delta = -27.021582 deg：原式 Delta camber = -5.562730 deg', output.getvalue())
                self.assertIn('固定 delta = +27.021582 deg 的原式 Delta camber = +2.089491 deg', output.getvalue())
                self.assertIn('前軸純 ay 接地模型失效', output.getvalue())
            else:
                self.assertIn('所需 Caster = ', output.getvalue())
                self.assertNotIn('前軸純 ay 接地模型失效', output.getvalue())

    def test_main_recomputes_steering_from_current_wheelbase_and_minimum_radius(self):
        for front, rear, radius in ((.6, .9, 2.5), (.8, .9, 3.5)):
            with (self.subTest(front=front, rear=rear, radius=radius),
                  patch.multiple(model, lf=front, lr=rear, min_turn_radius_m=radius),
                  patch.object(model, 'calculate_required_steering_angle',
                               wraps=model.calculate_required_steering_angle) as steering,
                  patch.object(model, 'calculate_caster_for_zero_camber',
                               wraps=model.calculate_caster_for_zero_camber) as caster,
                  redirect_stdout(StringIO()) as output):
                model.main()
            steering.assert_called_once_with(front + rear, radius)
            used_angle = math.radians(caster.call_args.args[4])
            self.assertAlmostEqual((front + rear) / math.tan(used_angle), radius)
            self.assertIn('最大需求轉向角 theta = atan(L/R)', output.getvalue())

    def test_nonfinite_angles_are_rejected(self):
        for index in range(5):
            values = [2., .5, 1., 8., 30.]
            values[index] = math.nan if index % 2 else math.inf
            with self.subTest(index=index), self.assertRaises(ValueError):
                model.calculate_caster_for_zero_camber(*values)
        for values in ((math.nan, 8., 30.), (4., math.inf, 30.), (4., 8., math.nan)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                model.calculate_steering_camber(*values)
        for wheelbase, radius in ((0., 3.), (1.53, 0.), (1.53, -3.), (math.nan, 3.), (1.53, math.inf)):
            with self.subTest(wheelbase=wheelbase, radius=radius), self.assertRaises(ValueError):
                model.calculate_required_steering_angle(wheelbase, radius)


class RateChainTests(unittest.TestCase):
    def test_series_compliance_and_coordinate_invariance(self):
        result = model.calculate_rate_chain(40000., .6, 80000., 60.)
        ks, kw, ride = (result[key] for key in ('spring_rate_N_per_m', 'wheel_rate_N_per_m', 'ride_rate_N_per_m'))
        self.assertAlmostEqual(1 / ride, 1 / kw + 1 / 80000.)
        self.assertLess(ride, min(kw, 80000.))
        self.assertAlmostEqual(result['frequency_Ks_Hz'], result['frequency_Kw_Hz'])
        self.assertAlmostEqual(result['critical_damping_Ks_Ns_per_m'] * .6**2,
                               result['critical_damping_Kw_Ns_per_m'])
        for stage, stiffness, mass in (('Ks', ks, 60. / .6**2), ('Kw', kw, 60.), ('Kr', ride, 60.)):
            critical = result[f'critical_damping_{stage}_Ns_per_m']
            omega = 2 * math.pi * result[f'frequency_{stage}_Hz']
            self.assertAlmostEqual(stiffness / mass, omega**2)
            self.assertAlmostEqual(critical / (2 * mass), omega)

    def test_tire_rigidity_limit_and_literal_four_case_inputs(self):
        rigid = model.calculate_rate_chain(40000., .6, 1e15, 60.)
        self.assertAlmostEqual(rigid['ride_rate_N_per_m'] / rigid['wheel_rate_N_per_m'], 1., places=9)
        cases = model.calculate_rate_cases(300., .6, .8, 80000., 100000., 70000., 140000., 40000.)
        for axle, mass, combined, roll in (('front', 90., 70000., 100000.), ('rear', 60., 55000., 70000.)):
            self.assertEqual(cases[axle]['combined_average']['spring_rate_N_per_m'], combined)
            self.assertEqual(cases[axle]['heave_with_tender']['spring_rate_N_per_m'], 40000.)
            self.assertEqual(cases[axle]['roll']['spring_rate_N_per_m'], roll)
            self.assertEqual(cases[axle]['heave_only']['spring_rate_N_per_m'], 140000.)
            self.assertEqual(cases[axle]['roll']['sprung_mass_per_wheel_kg'], mass)

    def test_unavailable_tender_and_invalid_rate_inputs(self):
        cases = model.calculate_rate_cases(300., .6, .8, 80000., 100000., 70000., 140000., None)
        for axle in ('front', 'rear'):
            self.assertIsNone(cases[axle]['combined_average'])
            self.assertIsNone(cases[axle]['heave_with_tender'])
            self.assertIsNotNone(cases[axle]['roll'])
            self.assertIsNotNone(cases[axle]['heave_only'])
        for index, value in ((0, 0.), (1, -1.), (2, math.nan), (3, math.inf)):
            inputs = [40000., .6, 80000., 60.]
            inputs[index] = value
            with self.subTest(index=index), self.assertRaises(ValueError):
                model.calculate_rate_chain(*inputs)
        with self.assertRaises(ValueError):
            model.calculate_rate_cases(300., 1., .8, 80000., 100000., 70000., 140000., None)

    def test_main_evaluates_all_cases_and_keeps_independent_cases_without_tender(self):
        for divisor, expected_count in ((5., 8), (3., 4)):
            with (self.subTest(divisor=divisor), patch.multiple(model, N=divisor, lf=.6, lr=.9),
                  patch.object(model, 'calculate_rate_chain', wraps=model.calculate_rate_chain) as solver,
                  redirect_stdout(StringIO()) as output):
                model.main()
            self.assertEqual(solver.call_count, expected_count)
            self.assertAlmostEqual(solver.call_args_list[0].args[3], model.ms * .6 / 2)
            self.assertAlmostEqual(solver.call_args_list[-1].args[3], model.ms * .4 / 2)
            self.assertIn('Ks spring rate → Kw wheel rate → Kr ride rate', output.getvalue())
            self.assertIn('Roll & Pitch gradient', output.getvalue())


class AttitudeGradientTests(unittest.TestCase):
    def gradients(self, **overrides):
        values = dict(total_mass=320., cog_height=.3, front_distance=.6, rear_distance=.9,
                      front_track=1.25, rear_track=1.24, motion_ratio=.8, tire_stiffness=80000.,
                      front_roll_spring=100000., rear_roll_spring=80000., main_heave_spring=140000.,
                      series_heave_spring=40000., front_roll_center=.02, rear_roll_center=.04, anti_dive=.4)
        values.update(overrides)
        return model.calculate_roll_pitch_gradients(**values)

    def test_roll_axis_interpolation_and_static_moment_balance(self):
        result = self.gradients()
        self.assertAlmostEqual(result['roll_axis_height_at_cg_m'], .028)
        moment = 320. * model.g * (.3 - .028)
        for stiffness, gradient in (('roll_suspension_stiffness_Nm_per_rad', 'roll_gradient_suspension_deg_per_g'),
                                    ('roll_ride_stiffness_Nm_per_rad', 'roll_gradient_with_tires_deg_per_g')):
            self.assertAlmostEqual(result[stiffness] * math.radians(result[gradient]), moment)
        self.assertGreater(result['roll_gradient_with_tires_deg_per_g'],
                           result['roll_gradient_suspension_deg_per_g'])

    def test_pitch_matches_axle_force_balance_and_anti_dive_keeps_tire_deformation(self):
        result = self.gradients()
        transfer = 320. * model.g * .3 / 1.5
        tire_angle = (2 * transfer / (2 * 80000.)) / 1.5
        for mode, spring in (('heave_with_tender', 40000.), ('heave_only', 140000.)):
            values = result['pitch'][mode]
            spring_angle = (2 * transfer / (spring * .8**2)) / 1.5
            self.assertAlmostEqual(values['gradient_suspension_deg_per_g'], math.degrees(spring_angle))
            self.assertAlmostEqual(values['gradient_with_tires_deg_per_g'], math.degrees(spring_angle + tire_angle))
            self.assertAlmostEqual(values['gradient_with_tires_and_anti_dive_deg_per_g'],
                                   math.degrees(.6 * spring_angle + tire_angle))
        full_anti = self.gradients(anti_dive=1.)
        self.assertAlmostEqual(full_anti['pitch']['heave_only']['gradient_with_tires_and_anti_dive_deg_per_g'],
                               math.degrees(tire_angle))

    def test_zero_moment_arm_unavailable_tender_and_invalid_inputs(self):
        result = self.gradients(cog_height=0., front_roll_center=0., rear_roll_center=0., series_heave_spring=None)
        self.assertEqual(result['roll_gradient_with_tires_deg_per_g'], 0.)
        self.assertIsNone(result['pitch']['heave_with_tender'])
        self.assertEqual(result['pitch']['heave_only']['gradient_with_tires_deg_per_g'], 0.)
        for invalid in (dict(total_mass=0.), dict(front_distance=0.), dict(tire_stiffness=math.nan),
                        dict(anti_dive=1.1), dict(series_heave_spring=-1.), dict(rear_roll_center=math.inf)):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.gradients(**invalid)


class CriticalDampingTests(unittest.TestCase):
    def damping(self, **overrides):
        values = dict(sprung_mass=260.55, front_weight_ratio=.6,
                      front_roll_spring=100000., rear_roll_spring=80000.,
                      main_heave_spring=140000., series_heave_spring=48000.,
                      motion_ratio=.8, front_track=1.25, rear_track=1.24,
                      sprung_roll_inertia=8.)
        values.update(overrides)
        return model.calculate_suspension_critical_damping(**values)

    def test_linear_reference_has_a_repeated_real_characteristic_root(self):
        mass, stiffness = 130., 140000.
        critical = model.calculate_critical_damping(mass, stiffness)
        self.assertAlmostEqual(critical**2 / (4 * mass * stiffness), 1.)
        root = -critical / (2 * mass)
        self.assertAlmostEqual(mass * root**2 + critical * root + stiffness, 0.)

    def test_heave_modes_and_roll_distribution_are_critical_in_their_coordinates(self):
        result = self.damping()
        for mode in ('heave_with_tender', 'pure_heave'):
            front, rear = result[mode]['front'], result[mode]['rear']
            self.assertAlmostEqual(front['sprung_mass_kg'] + rear['sprung_mass_kg'], 260.55)
            self.assertAlmostEqual(front['sprung_mass_kg'] / 260.55, .6)
            for axle in (front, rear):
                c = axle['damper_critical_damping_Ns_per_m'] * .8**2
                m, k = axle['sprung_mass_kg'], axle['body_stiffness_N_per_m']
                self.assertAlmostEqual(c**2 / (4 * m * k), 1.)
                self.assertAlmostEqual(c, axle['body_critical_damping_Ns_per_m'])
        self.assertLess(result['heave_with_tender']['front']['damper_critical_damping_Ns_per_m'],
                        result['pure_heave']['front']['damper_critical_damping_Ns_per_m'])
        roll_c = sum(result['roll'][axle]['damper_critical_damping_Ns_per_m'] * (.8 * track)**2
                     for axle, track in (('front', 1.25), ('rear', 1.24)))
        self.assertAlmostEqual(roll_c, result['roll_total_critical_damping_Nms_per_rad'])
        self.assertAlmostEqual(roll_c**2 / (4 * 8. * result['roll_total_stiffness_Nm_per_rad']), 1.)
        self.assertAlmostEqual(sum(axle['stiffness_fraction'] for axle in result['roll'].values()), 1.)
        front, rear = result['roll']['front'], result['roll']['rear']
        self.assertAlmostEqual(front['angular_damping_Nms_per_rad'] / rear['angular_damping_Nms_per_rad'],
                               front['angular_stiffness_Nm_per_rad'] / rear['angular_stiffness_Nm_per_rad'])

    def test_motion_ratio_and_inertia_scaling_preserve_the_physical_conversion(self):
        baseline = self.damping()
        doubled_mr = self.damping(motion_ratio=1.6)
        heavier_inertia = self.damping(sprung_roll_inertia=32.)
        for mode in ('roll', 'heave_with_tender', 'pure_heave'):
            for axle in ('front', 'rear'):
                key = 'damper_critical_damping_Ns_per_m'
                self.assertAlmostEqual(doubled_mr[mode][axle][key], baseline[mode][axle][key] / 2)
                expected = baseline[mode][axle][key] * (2 if mode == 'roll' else 1)
                self.assertAlmostEqual(heavier_inertia[mode][axle][key], expected)

    def test_main_passes_existing_spring_rates_and_axle_mass_distribution(self):
        with (patch.multiple(model, lf=.6, lr=.9, MR=.8),
              patch.object(model, 'calculate_suspension_critical_damping',
                           wraps=model.calculate_suspension_critical_damping) as solver,
              redirect_stdout(StringIO()) as output):
            model.main()
        solver.assert_called_once()
        args = solver.call_args.args
        self.assertEqual(args[0], model.ms)
        self.assertAlmostEqual(args[1], .6)
        self.assertAlmostEqual(args[3] / args[2], model.kr / model.kf)
        self.assertTrue(0 < args[5] < args[4])
        self.assertEqual(args[6:], (.8, model.tf, model.tr, model.sprung_roll_inertia_kg_m2))
        self.assertIn('前阻尼器 [N s/m]', output.getvalue())
        self.assertIn('固定輪端、剛性車體', output.getvalue())

    def test_unavailable_tender_preserves_roll_and_pure_heave_results(self):
        result = self.damping(series_heave_spring=None)
        self.assertIsNone(result['heave_with_tender'])
        self.assertGreater(result['roll']['front']['damper_critical_damping_Ns_per_m'], 0.)
        self.assertGreater(result['pure_heave']['rear']['damper_critical_damping_Ns_per_m'], 0.)
        with patch.object(model, 'N', 3.), redirect_stdout(StringIO()) as output:
            model.main()
        self.assertIn('Heave + Tender：前序 Tender 無有限正剛性解', output.getvalue())
        self.assertIn('純 Heave', output.getvalue())

    def test_invalid_mass_rates_ratios_and_inertia_are_rejected(self):
        for mass, stiffness in ((0., 1.), (1., -1.), (math.nan, 1.), (1., math.inf)):
            with self.subTest(mass=mass, stiffness=stiffness), self.assertRaises(ValueError):
                model.calculate_critical_damping(mass, stiffness)
        for overrides in (dict(sprung_mass=0.), dict(front_weight_ratio=1.), dict(front_weight_ratio=math.nan),
                          dict(motion_ratio=0.), dict(front_track=0.), dict(rear_roll_spring=-1.),
                          dict(sprung_roll_inertia=math.inf), dict(series_heave_spring=140000.),
                          dict(series_heave_spring=0.), dict(series_heave_spring=math.nan)):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.damping(**overrides)


class AntiDiveTests(unittest.TestCase):
    def test_normalized_optimum_matches_front_roll_center_model(self):
        for ratio in (1., 10., 20.):
            with self.subTest(ratio=ratio):
                anti = model.calculate_anti_dive(ratio)
                rc = model.calculate_roll_center(.3, ratio)
                self.assertAlmostEqual(anti['anti_dive'], rc['rc_normalized_optimal_ratio'])
                self.assertAlmostEqual(anti['anti_dive_normalized_min_stiffness'],
                                       rc['rc_normalized_min_stiffness'])
                alpha = anti['anti_dive_suspension_fraction']
                self.assertAlmostEqual(alpha, rc['rc_suspension_fraction'])
                self.assertAlmostEqual(alpha + anti['anti_dive'], 1.)
                self.assertAlmostEqual(rc['rc_normalized_optimal_height_m'], .3 * (1 - alpha))
                suspension_stiffness, chassis_stiffness = 1000., ratio * 1000.
                self.assertAlmostEqual(2 * alpha * suspension_stiffness
                                       - 2 * (1 - alpha) * chassis_stiffness, 0.)
                equivalent = alpha**2 * suspension_stiffness + (1 - alpha)**2 * chassis_stiffness
                self.assertAlmostEqual(equivalent / suspension_stiffness,
                                       anti['anti_dive_normalized_min_stiffness'])
                self.assertFalse(any('grid' in key for key in anti))
                self.assertFalse(any('grid' in key for key in rc))
                optimum = anti['anti_dive']
                for offset in (-.01, .01):
                    nearby = optimum + offset
                    self.assertGreater((1 - nearby)**2 + ratio * nearby**2,
                                       anti['anti_dive_normalized_min_stiffness'])
        anti = model.calculate_anti_dive(10.)
        self.assertAlmostEqual(anti['anti_dive_percent'], 100 / 11)
        scrub = model.calculate_anti_scrub(anti['anti_dive'], 1.2, 2.)
        self.assertAlmostEqual(scrub['anti_scrub_percent'], 60 / 11)

    def test_main_uses_normalized_anti_without_a_feasible_tender(self):
        with (patch.multiple(model, N=3., rc_chassis_stiffness_ratio=10.),
              patch.object(model, 'calculate_anti_scrub', wraps=model.calculate_anti_scrub) as scrub,
              redirect_stdout(StringIO()) as output):
            model.main()
        self.assertAlmostEqual(scrub.call_args.args[0], 1 / 11)
        anti_text = output.getvalue().split('Anti dive（')[1].split('Anti-Scrub（')[0]
        self.assertIn('9.091%', anti_text)
        self.assertIn('最小正規化等效剛性', anti_text)
        self.assertIn('懸吊路徑比例 alpha', anti_text)
        self.assertNotIn('無法計算', anti_text)
        self.assertNotIn('300 點搜尋', output.getvalue())

    def test_invalid_chassis_stiffness_ratios_are_rejected(self):
        for ratio in (0., -1., math.nan, math.inf):
            with self.subTest(ratio=ratio), self.assertRaises(ValueError):
                model.calculate_anti_dive(ratio)


class GearRateTests(unittest.TestCase):
    def gear_rate(self, **overrides):
        values = dict(mass=260.55, unsprung_mass=14.4, cog_height=.3,
                      front_distance=.765, rear_distance=.765, acceleration_g=1.2,
                      tire_radius=.2, motor_torque=22.30565254, motor_rpm=15000., target_speed_kmh=110.)
        values.update(overrides)
        return model.calculate_gear_rate(**values)

    def test_ratios_match_existing_gear_rate_with_symmetric_static_distribution(self):
        from analysis.gearing.workflow import run
        expected = run('gear_rate', dict(cog_total_mass_kg=318.15, L=1.53, h_cog=.3,
                                        hl_front_weight_ratio=.5, R_tire=.2, acc_g=1.2,
                                        drive_motor_torque_Nm=22.30565254, drive_motor_rpm=15000.,
                                        drive_target_speed_kmh=110.))
        try:
            actual = self.gear_rate()
            for key in ('gear_ratio_accel', 'gear_ratio_top_speed', 'gear_ratio_avg'):
                self.assertAlmostEqual(actual[key], expected.outputs[key])
        finally:
            expected.close()

    def test_loads_and_drive_force_preserve_no_aero_equilibrium_with_asymmetric_cg(self):
        result = self.gear_rate(front_distance=.6, rear_distance=.9)
        weight = 318.15 * model.g
        front, rear = result['front_axle_load_N'], result['rear_axle_load_N']
        self.assertAlmostEqual(front + rear, weight)
        self.assertAlmostEqual(front * .6 - rear * .9, -318.15 * 1.2 * model.g * .3)
        self.assertAlmostEqual(result['front_axle_Fx_N'] + result['rear_axle_Fx_N'], 318.15 * 1.2 * model.g)
        static = self.gear_rate(front_distance=.6, rear_distance=.9, cog_height=0.)
        self.assertAlmostEqual(static['front_axle_load_N'], weight * .6)
        self.assertAlmostEqual(static['rear_axle_load_N'], weight * .4)

    def test_motor_torque_and_speed_changes_affect_the_corresponding_ratio(self):
        base = self.gear_rate()
        stronger = self.gear_rate(motor_torque=2 * 22.30565254)
        faster = self.gear_rate(motor_rpm=30000.)
        self.assertAlmostEqual(stronger['gear_ratio_accel'], base['gear_ratio_accel'] / 2)
        self.assertEqual(stronger['gear_ratio_top_speed'], base['gear_ratio_top_speed'])
        self.assertAlmostEqual(faster['gear_ratio_top_speed'], 2 * base['gear_ratio_top_speed'])
        self.assertEqual(faster['gear_ratio_accel'], base['gear_ratio_accel'])
        wheel_speed = 15000. / base['gear_ratio_top_speed']
        self.assertAlmostEqual(wheel_speed * (2 * math.pi * .2) / 60 * 3.6, 110.)
        self.assertAlmostEqual(base['gear_ratio_avg'],
                               (base['gear_ratio_accel'] + base['gear_ratio_top_speed']) / 2)

    def test_invalid_inputs_and_axle_lift_are_rejected(self):
        invalid = (dict(acceleration_g=0.), dict(acceleration_g=math.nan), dict(acceleration_g=4.),
                   dict(tire_radius=0.), dict(motor_torque=-1.), dict(motor_rpm=math.inf),
                   dict(target_speed_kmh=0.), dict(cog_height=-.1), dict(unsprung_mass=-1.))
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.gear_rate(**overrides)

    def test_main_uses_a_acc_for_the_no_aero_gear_case(self):
        with (patch.multiple(model, a_acc=1.2, ax=1.6, ay=1.4, F_ref_ratio=.25),
              patch.object(model, 'calculate_gear_rate', wraps=model.calculate_gear_rate) as solver,
              redirect_stdout(StringIO()) as output):
            model.main()
        self.assertEqual(solver.call_args.args[5], 1.2)
        text = output.getvalue().split('Gear_rate：無空力加速與極速齒比：')[1]
        self.assertIn('ax = a_acc = 1.2 g，ay = 0 g，空力下壓力 = 0 N', text)
        self.assertIn('平均減速比 gear_ratio_avg', text)


class BrakeRatioTests(unittest.TestCase):
    def brake_ratio(self, **overrides):
        values = dict(mass=260.55, unsprung_mass=14.4, cog_height=.3,
                      front_distance=.765, rear_distance=.765, deceleration_g=2.,
                      tire_friction=1.6046564575663345)
        values.update(overrides)
        return model.calculate_brake_ratio(**values)

    def test_requested_point_matches_braking_models_with_asymmetric_cg(self):
        from analysis.braking.models import axle_loads, ideal_distribution
        params = dict(cog_total_mass_kg=318.15, L=1.53, h_cog=.3, hl_front_weight_ratio=.93 / 1.53)
        actual = self.brake_ratio(front_distance=.6, rear_distance=.93, deceleration_g=1.5)['requested_point']
        front, rear = axle_loads(params, 1.5)
        front_force, rear_force = ideal_distribution(params, 1.5)
        self.assertAlmostEqual(actual['front_axle_load_N'], front)
        self.assertAlmostEqual(actual['rear_axle_load_N'], rear)
        self.assertAlmostEqual(actual['front_brake_force_N'], front_force)
        self.assertAlmostEqual(actual['rear_brake_force_N'], rear_force)
        self.assertAlmostEqual(front + rear, 318.15 * model.g)
        self.assertAlmostEqual(front_force + rear_force, 318.15 * 1.5 * model.g)

    def test_ten_point_fit_matches_existing_brake_ratio_with_the_friction_limit(self):
        from analysis.braking.workflow import run
        params = dict(cog_total_mass_kg=318.15, L=1.53, h_cog=.3,
                      hl_front_weight_ratio=.5, mu_w=1.6046564575663345)
        with redirect_stdout(StringIO()):
            expected = run('brake_ratio', params)
        try:
            actual = self.brake_ratio()
            for key in ('brake_ideal_front_ratio', 'brake_ideal_rear_ratio',
                        'brake_design_deceleration_g', 'brake_ideal_fit_rear_over_front'):
                self.assertAlmostEqual(actual[key], expected.outputs[key])
            np.testing.assert_allclose([row['deceleration_g'] for row in actual['samples']],
                                       expected.tables['ideal_brake_distribution.csv']['deceleration_g'])
        finally:
            expected.close()

    def test_two_g_design_is_distinguished_from_the_achievable_limit(self):
        result = self.brake_ratio()
        requested, limit = result['requested_point'], result['limit_point']
        self.assertEqual(requested['deceleration_g'], 2.)
        self.assertAlmostEqual(requested['front_ratio'], .8921568627450981)
        self.assertAlmostEqual(requested['rear_ratio'], .10784313725490197)
        self.assertFalse(result['target_achievable'])
        self.assertEqual(result['required_tire_mu'], 2.)
        self.assertEqual(limit['deceleration_g'], 1.6046564575663345)
        self.assertAlmostEqual(requested['front_ratio'] + requested['rear_ratio'], 1.)
        self.assertTrue(self.brake_ratio(tire_friction=2.2)['target_achievable'])

    def test_rear_contact_boundary_allows_front_only_braking_and_rejects_wheel_lift(self):
        result = self.brake_ratio(front_distance=.75, rear_distance=.75, deceleration_g=2.5, tire_friction=3.)
        requested = result['requested_point']
        self.assertTrue(result['target_achievable'])
        self.assertEqual(requested['rear_axle_load_N'], 0.)
        self.assertEqual(requested['rear_brake_force_N'], 0.)
        self.assertEqual(requested['front_ratio'], 1.)
        with self.assertRaises(ValueError):
            self.brake_ratio(deceleration_g=3., tire_friction=3.)

    def test_invalid_brake_inputs_are_rejected(self):
        for overrides in (dict(deceleration_g=0.), dict(deceleration_g=-2.), dict(deceleration_g=math.nan),
                          dict(tire_friction=0.), dict(tire_friction=math.inf), dict(front_distance=0.),
                          dict(cog_height=-.1), dict(unsprung_mass=-1.)):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.brake_ratio(**overrides)

    def test_main_uses_positive_two_g_deceleration_in_the_independent_brake_case(self):
        with (patch.multiple(model, brake_ax=2., mu_w=2.2, ax=1.6, ay=1.4, F_ref_ratio=.25),
              patch.object(model, 'calculate_brake_ratio', wraps=model.calculate_brake_ratio) as solver,
              redirect_stdout(StringIO()) as output):
            model.main()
        self.assertEqual(solver.call_args.args[5:], (2., 2.2))
        text = output.getvalue().split('Brake_ratio：極限煞車工況的前後煞車比：')[1]
        self.assertIn('車身 ax = -2 g', text)
        self.assertIn('ay = 0 g，空力下壓力 = 0 N', text)
        self.assertIn('2 g 理想前後煞車比', text)


if __name__ == '__main__':
    unittest.main()
