'''
Tests for intuition.core.engine
'''

import unittest
from nose.tools import raises, ok_, eq_, nottest
import pytz
import datetime as dt
import pandas as pd
import dna.errors
# from zipline.data.benchmarks import BenchmarkDataNotFoundError
import intuition.core.engine as engine
from intuition.errors import InvalidEngine
from intuition.test_framework import TestAlgorithm
import dna.test_utils


# TODO Test standalone run of this engine
# TODO Test elapsed_time
class EngineTestCase(unittest.TestCase):
    default_capital_base = 100000.0

    def setUp(self):
        dna.test_utils.setup_logger(self)
        self.test_identity = 'test-gekko'
        self.good_algo = 'intuition.test_framework.TestAlgorithm'
        self.good_manager = 'intuition.test_framework.TestPortfolio'

    def tearDown(self):
        dna.test_utils.teardown_logger(self)

    def test_new_minimal_engine(self):
        eng = engine.TradingEngine(
            self.test_identity,
            {'algorithm': self.good_algo},
            {}
        )
        eq_(eng.identity, self.test_identity)
        ok_(hasattr(eng, 'logger'))
        eq_(eng.capital_base, self.default_capital_base)
        self.assertIsNone(eng.manager)
        # New version of zipline set it to true
        self.assertTrue(eng.initialized)
        self.assertFalse(eng._warmed)
        self.assertListEqual(eng.middlewares, [])
        self.assertListEqual(eng.sources, [])

    @raises(InvalidEngine)
    def test_new_engine_without_algo_module(self):
        engine.TradingEngine(self.test_identity, {}, {})

    @raises(dna.errors.DynamicImportFailed)
    def test_new_engine_with_wrong_algo_module(self):
        engine.TradingEngine(
            self.test_identity, {'algorithm': 'invalid.algo'}, {})

    @raises(dna.errors.DynamicImportFailed)
    def test_new_engine_with_wrong_manager_module(self):
        engine.TradingEngine(
            self.test_identity,
            {'algorithm': self.good_algo, 'manager': 'invalid.manager'},
            {})

    def test_new_engine_with_manager(self):
        eng = engine.TradingEngine(
            self.test_identity,
            {'algorithm': self.good_algo,
             'manager': self.good_manager},
            {})
        self.assertIsNotNone(eng.manager)
        ok_(hasattr(eng.manager, 'log'))


# TODO simulation.__call__
class SimulationTestCase(unittest.TestCase):

    def setUp(self):
        dna.test_utils.setup_logger(self)
        self.test_identity = 'test-gekko'
        self.good_algo = 'intuition.test_framework.TestAlgorithm'
        self.good_manager = 'intuition.test_framework.TestPortfolio'
        # self.default_first_date = dt.date(1990, 1, 2)
        # self.default_first_date = dt.date(2008, 6, 25)
        self.default_last_date = (dt.date.today() - pd.datetools.Day()).date()
        self.whatever_naive_date = dt.datetime(2013, 1, 1)
        self.whatever_date = dt.datetime(2013, 1, 1, tzinfo=pytz.utc)
        self.whatever_live_date = dt.datetime(2015, 1, 1, tzinfo=pytz.utc)

        self.simu = engine.Simulation()

    def tearDown(self):
        dna.test_utils.teardown_logger(self)

    @nottest
    def _check_environment(self, env):
        eq_(env.exchange_tz, 'Europe/Paris')
        # eq_(env.first_trading_day.date(), self.default_first_date)
        # FIXME It doesn't work this way
        # eq_(env.last_trading_day.date(), self.default_last_date)
        self.assertIsInstance(env.treasury_curves, pd.DataFrame)
        self.assertFalse(env.treasury_curves.empty)
        self.assertIsInstance(env.benchmark_returns, pd.Series)
        self.assertFalse(env.benchmark_returns.empty)

    def test_environment_configuration(self):
        self.assertIsNone(self.simu.trading_context)
        self.simu.configure_environment(
            last_trade=self.whatever_date,
            benchmark='FCHI',
            timezone='Europe/Paris')
        eq_(self.simu.benchmark, 'FCHI')
        eq_(self.simu.benchmark, self.simu.trading_context.bm_symbol)
        self._check_environment(self.simu.trading_context)

    def test_environment_configuration_naive_date(self):
        self.simu.configure_environment(
            last_trade=self.whatever_naive_date,
            benchmark='FCHI',
            timezone='Europe/Paris')
        self._check_environment(self.simu.trading_context)

    def test_environment_configuration_live_date(self):
        self.simu.configure_environment(
            last_trade=self.whatever_live_date,
            benchmark='FCHI',
            timezone='Europe/Paris')
        self._check_environment(self.simu.trading_context)

    # FIXME This test uses the network
    '''
    @raises(BenchmarkDataNotFoundError)
    def test_environment_configuration_invalid_benchmark(self):
            self.simu.configure_environment(
                self.whatever_date, 'vzbrzgbe', 'Europe/Paris')
    '''

    def _check_engine(self, eng):
        eq_(eng.identity, self.test_identity)
        self.assertIsNone(eng.manager)
        eq_(eng.__class__, TestAlgorithm)
