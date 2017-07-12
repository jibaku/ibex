import unittest
import os
import re

from sklearn import linear_model
from sklearn import preprocessing
from sklearn import pipeline, base
import pandas as pd
import numpy as np

from frame_learn import *


class _ConceptsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._prd = frame(linear_model.LinearRegression())
        cls._clf = frame(linear_model.LogisticRegression())

    def test_base_estimator(self):
        self.assertTrue(
            isinstance(self._prd, base.BaseEstimator))
        self.assertTrue(
            isinstance(self._clf, base.BaseEstimator))

    def test_regressor_mixin(self):
        self.assertTrue(
            isinstance(self._prd, base.RegressorMixin))
        self.assertTrue(
            isinstance(self._clf, base.ClassifierMixin))

    def test_classifier_mixin(self):
        self.assertFalse(
            isinstance(self._prd, base.ClassifierMixin))
        self.assertFalse(
            isinstance(self._clf, base.RegressorMixin))


class _BaseTest(unittest.TestCase):
    def test_neut(self):
        x = pd.DataFrame({'a': [1, 2, 3]})
        y = pd.Series([1, 2, 3])

        prd = linear_model.LinearRegression(fit_intercept=False)
        self.assertIn('get_params', dir(prd))
        self.assertEquals(prd.get_params()['fit_intercept'], False)

        prd = frame(linear_model.LinearRegression(fit_intercept=False))
        self.assertIn('get_params', dir(prd))
        self.assertEquals(prd.get_params()['fit_intercept'], False)

    def test_get_attr(self):
        x = pd.DataFrame({'a': [1, 2, 3]})
        y = pd.Series([1, 2, 3])

        prd = frame(linear_model.LinearRegression())
        with self.assertRaises(AttributeError):
            prd.coef_
        prd.fit(x, y)
        prd.coef_


class _FrameTest(unittest.TestCase):
    def test_transform_y(self):
        x = pd.DataFrame({'a': [1, 2, 3]})
        y = pd.Series([1, 2, 3])

        xt = frame(preprocessing.StandardScaler()).fit(x, y).transform(x)
        self.assertTrue(isinstance(xt, pd.DataFrame))
        xt = frame(preprocessing.StandardScaler()).fit_transform(x, y)
        self.assertTrue(isinstance(xt, pd.DataFrame))

    def test_transform_no_y(self):
        x = pd.DataFrame({'a': [1, 2, 3]})
        y = pd.Series([1, 2, 3])

        xt = frame(preprocessing.StandardScaler()).fit(x).transform(x)
        self.assertTrue(isinstance(xt, pd.DataFrame))
        xt = frame(preprocessing.StandardScaler()).fit_transform(x)
        self.assertTrue(isinstance(xt, pd.DataFrame))

    def test_fit(self):
        s = frame(linear_model.LinearRegression())
        x = pd.DataFrame({'a': [1, 2, 3]})
        y = pd.Series([1, 2, 3])

        y_hat = frame(linear_model.LinearRegression()).fit(x, y).predict(x)
        self.assertTrue(isinstance(y_hat, pd.Series))

    def test_fit_permute_cols(self):
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [30, 23, 2]})
        y = pd.Series([1, 2, 3])
        z = pd.DataFrame({'b': [1, 2, 3], 'a': [30, 23, 2]})

        pred = frame(linear_model.LinearRegression()).fit(x, y)

        y_hat = pred.predict(z)
        self.assertTrue(isinstance(y_hat, pd.Series))

        y_hat = pred.predict(x[list(reversed(list(x.columns)))])
        self.assertTrue(isinstance(y_hat, pd.Series))

        # Tmp Ami - compare

    def test_fit_bad_cols(self):
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [30, 23, 2]})
        y = pd.Series([1, 2, 3])

        pred = frame(linear_model.LinearRegression()).fit(x, y)

        y_hat = pred.predict(x)
        self.assertTrue(isinstance(y_hat, pd.Series))

        x.rename(columns={'a': 'c'}, inplace=True)

        with self.assertRaises(KeyError):
            pred.predict(x)

    def test_pipeline_fit(self):
        s = frame(linear_model.LinearRegression())
        x = pd.DataFrame({'a': [1, 2, 3]})
        y = pd.Series([1, 2, 3])

        p = pipeline.make_pipeline(linear_model.LinearRegression())
        prd = frame(p)
        prd = prd.fit(x, y)
        y_hat = frame(p).fit(x, y).predict(x)
        self.assertTrue(isinstance(y_hat, pd.Series))

    def test_pipeline_fit_internal_pd_stage(self):
        s = frame(linear_model.LinearRegression())
        x = pd.DataFrame({'a': [1, 2, 3]})
        y = pd.Series([1, 2, 3])

        p = pipeline.make_pipeline(frame(linear_model.LinearRegression()))
        y_hat = frame(p).fit(x, y).predict(x)
        self.assertTrue(isinstance(y_hat, pd.Series))


class _ApplyTest(unittest.TestCase):
    def test_trans_none(self):
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [30, 23, 2]})

        trans().transform(x)

    def test_trans_none_cols(self):
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [30, 23, 2]})

        trans(columns=['a']).transform(x)

    def test_trans_none_bad_cols(self):
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [30, 23, 2]})

        with self.assertRaises(KeyError):
            trans(columns=['c']).transform(x)

    def test_trans_pd(self):
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [30, 23, 2]})

        trans(lambda x: pd.DataFrame({'sqrt_a': np.sqrt(x['a'])})).transform(x)

    def test_trans_no_pd_single(self):
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [30, 23, 2]})

        trans({'sqrt_a': lambda x: np.sqrt(x)}, columns='a').transform(x)

    def test_trans_no_pd_multiple(self):
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [30, 23, 2]})


class _UnionTest(unittest.TestCase):

    class simple_transformer(object):
        def __init__(self, col=0):
            self.col = col

        def fit_transform(self, x, y):
            xt = x.iloc[:, self.col]
            return pd.DataFrame(xt, index=x.index)

        def fit(self, x, y):
            return self

        def transform(self, x):
            xt = x.iloc[:, self.col]
            return pd.DataFrame(xt, index=x.index)

    def test_pandas_support(self):
        """ simple test to make sure the pandas wrapper works properly"""
        x = pd.DataFrame(np.random.rand(500, 10), index=range(500))
        y = x.iloc[:, 0]

        trans_list = [
            ('1', self.simple_transformer(col=0)),
            ('2', self.simple_transformer(col=1))]

        xt1 = self.simple_transformer().fit_transform(x, y)
        self.assertEqual(xt1.shape, (len(x), 1))

        feat_un = FeatureUnion(trans_list)

        xt2 = feat_un.fit_transform(x, y)
        self.assertEqual(xt2.shape, (len(x), 2))
        self.assertListEqual(list(xt2.index), list(x.index))

        feat_un.fit(x, y)
        xt3 = feat_un.transform(x)
        self.assertEqual(xt3.shape, (len(x), 2))
        self.assertListEqual(list(xt3.index), list(x.index))


class _OperatorsTest(unittest.TestCase):

    def test_pipe_fit(self):
        s = frame(linear_model.LinearRegression())
        x = pd.DataFrame({'a': [1, 2, 3]})
        y = pd.Series([1, 2, 3])

        prd = frame(preprocessing.StandardScaler()) | \
            frame(preprocessing.StandardScaler()) | \
            frame(linear_model.LinearRegression())
        y_hat = prd.fit(x, y).predict(x)
        self.assertTrue(isinstance(y_hat, pd.Series))

    def test_pipe_trans_fit(self):
        s = frame(linear_model.LinearRegression())
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [2, 3, 4]})
        y = pd.Series([1, 2, 3])

        prd = frame(preprocessing.MinMaxScaler()) | \
            trans({'sqrt_a': np.sqrt, 'sqr_a': lambda x: x ** 2}, columns='a') | \
            frame(linear_model.LinearRegression())
        y_hat = prd.fit(x, y).predict(x)
        self.assertTrue(isinstance(y_hat, pd.Series))

    def test_pipe_add_trans_fit(self):
        s = frame(linear_model.LinearRegression())
        x = pd.DataFrame({'a': [1, 2, 3], 'b': [2, 3, 4]})
        y = pd.Series([1, 2, 3])

        prd = frame(preprocessing.MinMaxScaler()) | \
            trans() + trans({'sqrt_a': np.sqrt, 'sqr_a': lambda x: x ** 2}, columns='a') | \
            frame(linear_model.LinearRegression())
        y_hat = prd.fit(x, y).predict(x)
        self.assertTrue(isinstance(y_hat, pd.Series))


class _FeatureUnionTest(unittest.TestCase):

    class simple_transformer(object):
        def __init__(self, col=0):
            self.col = col

        def fit_transform(self, x, y):
            xt = x.iloc[:, self.col]
            return pd.DataFrame(xt, index=x.index)

        def fit(self, x, y):
            return self

        def transform(self, x):
            xt = x.iloc[:, self.col]
            return pd.DataFrame(xt, index=x.index)

    def test_pandas_support(self):
        """ simple test to make sure the pandas wrapper works properly"""
        x = pd.DataFrame(np.random.rand(500, 10), index=range(500))
        y = x.iloc[:, 0]

        trans_list = [
            ('1', self.simple_transformer(col=0)),
            ('2', self.simple_transformer(col=1))]

        xt1 = self.simple_transformer().fit_transform(x, y)
        self.assertEqual(xt1.shape, (len(x), 1))

        feat_un = FeatureUnion(trans_list)

        xt2 = feat_un.fit_transform(x, y)
        self.assertEqual(xt2.shape, (len(x), 2))
        self.assertListEqual(list(xt2.index), list(x.index))

        feat_un.fit(x, y)
        xt3 = feat_un.transform(x)
        self.assertEqual(xt3.shape, (len(x), 2))
        self.assertListEqual(list(xt3.index), list(x.index))


if False:
    class _VerifyDocumentTest(unittest.TestCase):
        def test(self):
            f_name = os.path.join(os.path.split(__file__)[0], '../../README.rst')
            lines = [l.rstrip() for l in open(f_name)]

            python_re = re.compile(r'\s+(?:>>>|\.\.\.) (.*)')
            lines = [python_re.match(l).groups()[0] for l in lines if python_re.match(l) if python_re.match(l)]
            for l in lines:
                print(l)
            exec('\n'.join(lines))


if __name__ == '__main__':
    unittest.main()
